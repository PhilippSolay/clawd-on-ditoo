"""Watch a GitHub repo's pull requests and turn state changes into Clawd events.

The pet daemon is global (it doesn't know which repo you're hacking on), so repo
awareness lives here instead: a small `gh`-backed poller you run inside a repo
(`clawd watch`) that translates PR/CI transitions into `POST /event` calls on the
generic surface. PR merged → "MERGED" banner + happy + voice; CI red → alert; a
new PR → a "PR #N" banner.

The transition logic (`diff`) is pure and unit-tested; the IO (gh + posting) wraps
around it. Requires the `gh` CLI to be installed and authenticated.
"""

from __future__ import annotations

import json
import subprocess
import time
from typing import Callable, Dict, List, Optional

from .cli import DEFAULT_URL, _post

# How a PR's aggregate check status is summarized.
CHECK_SUCCESS = "SUCCESS"
CHECK_FAILURE = "FAILURE"
CHECK_PENDING = "PENDING"
CHECK_NONE = "NONE"

Snapshot = Dict[int, Dict[str, str]]


# -------------------- pure transition logic (tested) --------------------


def rollup_checks(checks: Optional[List[dict]]) -> str:
    """Reduce a statusCheckRollup array to one of SUCCESS / FAILURE / PENDING / NONE."""
    if not checks:
        return CHECK_NONE
    conclusions = [(c.get("conclusion") or c.get("state") or "").upper() for c in checks]
    statuses = [(c.get("status") or "").upper() for c in checks]
    if any(c == "FAILURE" or c == "TIMED_OUT" or c == "CANCELLED" for c in conclusions):
        return CHECK_FAILURE
    if any(s and s != "COMPLETED" for s in statuses):
        return CHECK_PENDING
    if conclusions and all(c in ("SUCCESS", "NEUTRAL", "SKIPPED") for c in conclusions):
        return CHECK_SUCCESS
    return CHECK_PENDING


def snapshot_from_prs(prs: List[dict]) -> Snapshot:
    """Index a `gh pr list --json` payload by PR number → {state, title, checks}."""
    out: Snapshot = {}
    for pr in prs:
        number = pr.get("number")
        if number is None:
            continue
        out[int(number)] = {
            "state": str(pr.get("state", "OPEN")).upper(),
            "title": str(pr.get("title", "")),
            "checks": rollup_checks(pr.get("statusCheckRollup")),
        }
    return out


def diff(old: Snapshot, new: Snapshot) -> List[dict]:
    """Compute the Clawd events implied by moving from `old` to `new`."""
    events: List[dict] = []
    for number, cur in new.items():
        prev = old.get(number)
        if prev is None:
            if cur["state"] == "OPEN":
                events.append({"kind": "banner", "text": f"PR {number}", "color": "orange",
                               "say": "New pull request."})
            continue
        if prev["state"] == "OPEN" and cur["state"] == "MERGED":
            events.append({"kind": "banner", "text": "MERGED", "color": "green",
                           "mood": "happy", "say": "Pull request merged!"})
        elif prev["state"] == "OPEN" and cur["state"] == "CLOSED":
            events.append({"kind": "banner", "text": "CLOSED", "color": "gray",
                           "say": "Pull request closed."})
        if cur["checks"] != prev["checks"]:
            if cur["checks"] == CHECK_FAILURE:
                events.append({"kind": "banner", "text": "CI RED", "color": "red",
                               "mood": "alert", "say": "Tests are failing."})
            elif cur["checks"] == CHECK_SUCCESS:
                events.append({"kind": "banner", "text": "CI OK", "color": "green",
                               "say": "Tests passed."})
    return events


# -------------------- IO (gh + posting) --------------------


def gh_pr_list(repo: Optional[str] = None, limit: int = 30) -> List[dict]:
    """Fetch PRs via the gh CLI. Returns [] on any failure (gh missing, not a repo,
    network) so the watcher degrades quietly rather than crashing."""
    cmd = ["gh", "pr", "list", "--state", "all", "--limit", str(limit),
           "--json", "number,state,title,statusCheckRollup"]
    if repo:
        cmd += ["--repo", repo]
    try:
        out = subprocess.check_output(cmd, text=True, timeout=20,
                                      stderr=subprocess.DEVNULL)
        return json.loads(out)
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
        return []


def watch(
    repo: Optional[str] = None,
    interval: float = 30.0,
    url: str = DEFAULT_URL,
    once: bool = False,
    poster: Optional[Callable[[str, dict], None]] = None,
    lister: Optional[Callable[[], List[dict]]] = None,
) -> None:
    """Poll the repo and feed transitions to Clawd. The first poll only seeds the
    baseline (no flood of banners for already-open PRs). `poster`/`lister` are
    injectable for testing."""
    post = poster or (lambda u, body: _post(u, body))
    fetch = lister or (lambda: gh_pr_list(repo))

    old: Snapshot = {}
    seeded = False
    while True:
        new = snapshot_from_prs(fetch())
        if seeded:
            for event in diff(old, new):
                post(f"{url}/event", event)
        else:
            seeded = True
        old = new
        if once:
            return
        time.sleep(interval)

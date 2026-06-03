"""Unit tests for the GitHub PR/CI watcher transition logic."""

import unittest

from divoom_pet.watch import (
    CHECK_FAILURE,
    CHECK_NONE,
    CHECK_PENDING,
    CHECK_SUCCESS,
    diff,
    rollup_checks,
    snapshot_from_prs,
    watch,
)


class RollupChecksTests(unittest.TestCase):
    def test_no_checks_is_none(self):
        self.assertEqual(rollup_checks(None), CHECK_NONE)
        self.assertEqual(rollup_checks([]), CHECK_NONE)

    def test_any_failure_wins(self):
        checks = [{"conclusion": "SUCCESS"}, {"conclusion": "FAILURE"}]
        self.assertEqual(rollup_checks(checks), CHECK_FAILURE)

    def test_incomplete_is_pending(self):
        checks = [{"status": "IN_PROGRESS"}, {"conclusion": "SUCCESS", "status": "COMPLETED"}]
        self.assertEqual(rollup_checks(checks), CHECK_PENDING)

    def test_all_success(self):
        checks = [{"conclusion": "SUCCESS", "status": "COMPLETED"},
                  {"conclusion": "SKIPPED", "status": "COMPLETED"}]
        self.assertEqual(rollup_checks(checks), CHECK_SUCCESS)


class SnapshotTests(unittest.TestCase):
    def test_indexes_by_number_and_uppercases_state(self):
        snap = snapshot_from_prs([{"number": 7, "state": "open", "title": "x"}])
        self.assertIn(7, snap)
        self.assertEqual(snap[7]["state"], "OPEN")
        self.assertEqual(snap[7]["checks"], CHECK_NONE)

    def test_skips_entries_without_number(self):
        self.assertEqual(snapshot_from_prs([{"state": "OPEN"}]), {})


class DiffTests(unittest.TestCase):
    def test_new_open_pr_emits_banner(self):
        new = {12: {"state": "OPEN", "title": "t", "checks": CHECK_NONE}}
        events = diff({}, new)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "banner")
        self.assertIn("12", events[0]["text"])

    def test_merge_emits_celebration(self):
        old = {3: {"state": "OPEN", "title": "t", "checks": CHECK_SUCCESS}}
        new = {3: {"state": "MERGED", "title": "t", "checks": CHECK_SUCCESS}}
        events = diff(old, new)
        self.assertTrue(any(e["text"] == "MERGED" and e.get("mood") == "happy" for e in events))

    def test_ci_failure_emits_alert(self):
        old = {3: {"state": "OPEN", "title": "t", "checks": CHECK_PENDING}}
        new = {3: {"state": "OPEN", "title": "t", "checks": CHECK_FAILURE}}
        events = diff(old, new)
        self.assertTrue(any(e["text"] == "CI RED" and e.get("mood") == "alert" for e in events))

    def test_ci_recovery_emits_ok(self):
        old = {3: {"state": "OPEN", "title": "t", "checks": CHECK_FAILURE}}
        new = {3: {"state": "OPEN", "title": "t", "checks": CHECK_SUCCESS}}
        events = diff(old, new)
        self.assertTrue(any(e["text"] == "CI OK" for e in events))

    def test_no_change_no_events(self):
        snap = {3: {"state": "OPEN", "title": "t", "checks": CHECK_SUCCESS}}
        self.assertEqual(diff(snap, dict(snap)), [])

    def test_closed_without_merge(self):
        old = {3: {"state": "OPEN", "title": "t", "checks": CHECK_NONE}}
        new = {3: {"state": "CLOSED", "title": "t", "checks": CHECK_NONE}}
        events = diff(old, new)
        self.assertTrue(any(e["text"] == "CLOSED" for e in events))


class WatchLoopTests(unittest.TestCase):
    def test_first_poll_seeds_without_firing(self):
        posted = []
        prs = [{"number": 1, "state": "OPEN", "title": "t"}]
        watch(once=True, poster=lambda u, b: posted.append(b), lister=lambda: prs)
        self.assertEqual(posted, [])  # baseline only; no flood of banners

    def test_merge_between_polls_fires_once(self):
        # Drive two polls by hand using the pure pieces (watch(once=True) seeds only).
        first = snapshot_from_prs([{"number": 1, "state": "OPEN", "title": "t"}])
        second = snapshot_from_prs([{"number": 1, "state": "MERGED", "title": "t"}])
        events = diff(first, second)
        self.assertTrue(any(e["text"] == "MERGED" for e in events))


if __name__ == "__main__":
    unittest.main()

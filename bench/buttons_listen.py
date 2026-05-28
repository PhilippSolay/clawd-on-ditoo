#!/usr/bin/env python3
"""Listen for inbound RFCOMM packets from the Ditoo.

This is a reverse-engineering harness. We open the Light channel via the Swift
bridge's new `listen` subcommand, which streams `<unix_ms> <hex>` lines to stdout
whenever the device sends bytes back. You press buttons / interact with the
device, we log everything, and at the end the script proposes a
"button → packet signature" map.

The Ditoo SHOULD send packets back when:
  - You press buttons under the keyboard
  - You press the play/skip media buttons on top
  - The built-in games receive input

Whether it actually does this is the open question — that's why we measure.

Two modes:
  1. Free mode (default):   `python3 bench/buttons_listen.py --mac ...`
       Just logs everything for 60 seconds (or until Ctrl-C). You poke around.

  2. Guided mode:           `python3 bench/buttons_listen.py --mac ... --guided`
       Walks you through each button by name, captures the response for each,
       and produces a signature map at the end.

Output:
  bench/results/buttons_<timestamp>.jsonl  (one event per line)
  bench/results/buttons_<timestamp>_signatures.md
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from divoom_pet.daemon.bridge import find_bundled_bridge  # noqa: E402


# Suggested controls on the Ditoo Pro (you can name them however you like at runtime).
SUGGESTED_BUTTONS = [
    "m (menu)",
    "+ (volume up)",
    "- (volume down)",
    ": (play/pause)",
    "lever / slider",
    "lighting button",
    "power (single tap)",
    "a keyboard key",
]


class Listener:
    def __init__(self, bridge_path: Path, mac: str, channel: int, log_path: Path):
        self.bridge_path = bridge_path
        self.mac = mac
        self.channel = channel
        self.log_path = log_path
        self.events: List[dict] = []
        self.proc: Optional[subprocess.Popen] = None
        self.lock = threading.Lock()
        self._reader: Optional[threading.Thread] = None
        self._stderr_reader: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def start(self) -> None:
        self.proc = subprocess.Popen(
            [str(self.bridge_path), "listen", self.mac, "--channel", str(self.channel)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            text=True,
        )
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()
        self._stderr_reader = threading.Thread(target=self._read_stderr, daemon=True)
        self._stderr_reader.start()
        time.sleep(0.6)  # let RFCOMM open
        if self.proc.poll() is not None:
            err = self.proc.stderr.read() if self.proc.stderr else ""
            raise RuntimeError(f"bridge listen exited immediately: {err}")

    def _read_stdout(self) -> None:
        if not self.proc or not self.proc.stdout:
            return
        for line in self.proc.stdout:
            if self.stop_event.is_set():
                return
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            ts, hexs = parts
            try:
                ts_ms = int(ts)
            except ValueError:
                continue
            event = {"ts_ms": ts_ms, "hex": hexs, "iso": datetime.fromtimestamp(ts_ms / 1000).isoformat(timespec="milliseconds")}
            with self.lock:
                self.events.append(event)
            # Live feedback to user
            print(f"  \033[2m{event['iso']}\033[0m  \033[36m{hexs}\033[0m")

    def _read_stderr(self) -> None:
        if not self.proc or not self.proc.stderr:
            return
        for line in self.proc.stderr:
            if self.stop_event.is_set():
                return
            sys.stderr.write(f"  [bridge] {line}")

    def take_events_since(self, ts_ms: int) -> List[dict]:
        with self.lock:
            return [e for e in self.events if e["ts_ms"] >= ts_ms]

    def stop(self) -> None:
        self.stop_event.set()
        if self.proc:
            try:
                self.proc.send_signal(signal.SIGINT)
                self.proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.proc.terminate()
            except Exception:
                pass


def run_free(listener: Listener, seconds: float) -> None:
    print(f"\n  Listening for {int(seconds)}s. Press buttons on the Ditoo (or Ctrl-C to stop early).")
    print(f"  Live packet log:")
    deadline = time.time() + seconds
    try:
        while time.time() < deadline:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n  stopped by Ctrl-C")


def run_guided(listener: Listener, log_path: Path) -> dict:
    print()
    print("  \033[1mFree-form capture\033[0m — you name each button as you go.")
    print("  Suggested controls on the Ditoo Pro:")
    for b in SUGGESTED_BUTTONS:
        print(f"    • {b}")
    print()
    print("  For each one:")
    print("    1. type a name (or 'done' to finish)")
    print("    2. press Enter, then press/hold that button on the Ditoo")
    print("    3. press Enter again to capture what arrived")
    print()
    signatures: dict = {}
    idx = 1
    while True:
        try:
            label = input(f"  [{idx}] button name (or 'done'): ").strip()
        except EOFError:
            break
        if label.lower() in ("done", "q", "quit", "exit", ""):
            break
        input(f"      ready — press Enter, THEN press '{label}' on the device... ")
        t0 = int(time.time() * 1000)
        input(f"      ...press Enter once you've pressed '{label}'. ")
        events = listener.take_events_since(t0)
        sig = " | ".join(e["hex"] for e in events) if events else "(no inbound bytes)"
        marker = "\033[32m✓\033[0m" if events else "\033[2m·\033[0m"
        print(f"      {marker} captured {len(events)} event(s): {sig[:100]}{'…' if len(sig) > 100 else ''}")
        signatures[label] = {"events": events, "first_hex": events[0]["hex"] if events else None}
        idx += 1
    return signatures


def write_signatures_md(signatures: dict, md_path: Path) -> None:
    lines = ["# Ditoo inbound packet signatures\n",
             f"_Captured {datetime.now().isoformat(timespec='seconds')}_\n",
             "| Button | Event count | First packet (hex) | Distinct (hex...) |",
             "|---|---|---|---|"]
    for button, data in signatures.items():
        n = len(data["events"])
        first = data["first_hex"] or "—"
        distinct = sorted({e["hex"] for e in data["events"]})
        d = ", ".join(distinct[:3])
        lines.append(f"| {button} | {n} | `{first[:24]}{'…' if len(first) > 24 else ''}` | `{d[:80]}{'…' if len(d) > 80 else ''}` |")
    md_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mac", required=True)
    ap.add_argument("--channel", type=int, default=1)
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--guided", action="store_true")
    args = ap.parse_args()

    bridge_path = find_bundled_bridge()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ROOT / "bench" / "results" / f"buttons_{stamp}.jsonl"
    md_path = ROOT / "bench" / "results" / f"buttons_{stamp}_signatures.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\033[1mDitoo buttons / inbound packet listener\033[0m")
    print(f"  bridge: {bridge_path}")
    print(f"  mac:    {args.mac}  channel={args.channel}")
    print(f"  log:    {log_path}")

    listener = Listener(bridge_path, args.mac, args.channel, log_path)
    try:
        listener.start()
    except Exception as e:
        print(f"  \033[31mfailed to start bridge:\033[0m {e}")
        return 2

    try:
        if args.guided:
            signatures = run_guided(listener, log_path)
        else:
            run_free(listener, args.seconds)
            signatures = {}
    finally:
        listener.stop()

    # write JSONL
    with open(log_path, "w") as fh:
        for e in listener.events:
            fh.write(json.dumps(e) + "\n")

    print(f"\n  Total inbound events: \033[1m{len(listener.events)}\033[0m")
    if signatures:
        write_signatures_md(signatures, md_path)
        print(f"  Signatures: {md_path}")

    if not listener.events:
        print("\n  \033[33mNo inbound bytes received.\033[0m")
        print("  Possibilities:")
        print("    1. The Ditoo doesn't send button events on this RFCOMM channel (try --channel 2).")
        print("    2. Buttons are read by the Divoom app via a separate channel/profile.")
        print("    3. The keyboard is purely a backlight peripheral with no host wiring.")
    else:
        unique = sorted({e["hex"] for e in listener.events})
        print(f"  Distinct packet signatures: {len(unique)}")
        for h in unique[:8]:
            count = sum(1 for e in listener.events if e["hex"] == h)
            print(f"    \033[36m{h[:32]}{'…' if len(h) > 32 else ''}\033[0m × {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

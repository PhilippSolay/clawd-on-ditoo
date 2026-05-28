#!/usr/bin/env python3
"""Visual FPS test — find the real refresh ceiling with your eyes.

`writeSync` only measures queue time, not on-screen time. To learn the true
refresh rate we push a moving element at several target frame rates and YOU
report which ones look smooth vs. which stutter or lag behind.

A bright Anthropic-orange column sweeps left->right->left. At low FPS it steps;
at high FPS it should glide. The rate where it stops looking smooth (or starts
lagging behind the printed counter) is the practical ceiling.

Usage:
  python3 bench/fps_visual.py --mac AA:BB:CC:DD:EE:FF --channel 2
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from divoom_pet.daemon.bridge import DitooBridge, find_bundled_bridge  # noqa: E402

RGB = Tuple[int, int, int]
ORANGE = (217, 119, 87)
DARK = (8, 8, 10)


def column_frame(x: int) -> List[RGB]:
    """16x16 frame with a bright vertical column at position x."""
    px: List[RGB] = []
    for _y in range(16):
        for col in range(16):
            px.append(ORANGE if col == x else DARK)
    return px


def sweep(bridge: DitooBridge, target_fps: float, seconds: float) -> dict:
    period = 1.0 / target_fps
    positions = list(range(16)) + list(range(14, 0, -1))  # bounce
    n = 0
    actual_intervals = []
    deadline = time.time() + seconds
    i = 0
    last = time.perf_counter()
    while time.time() < deadline:
        x = positions[i % len(positions)]
        bridge.push_image(column_frame(x))
        n += 1
        i += 1
        now = time.perf_counter()
        actual_intervals.append(now - last)
        last = now
        sleep_for = period - (time.perf_counter() - now)
        if sleep_for > 0:
            time.sleep(sleep_for)
    achieved = n / seconds
    return {"target": target_fps, "frames": n, "achieved_fps": achieved}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mac", default=os.environ.get("DITOO_MAC", "AA:BB:CC:DD:EE:FF"))
    ap.add_argument("--channel", type=int, default=2)
    ap.add_argument("--seconds", type=float, default=3.0, help="seconds per rate")
    args = ap.parse_args()

    bridge = DitooBridge(binary=find_bundled_bridge(), mac=args.mac, channel=args.channel)
    print(f"\033[1mVisual FPS test\033[0m  mac={args.mac} channel={args.channel}")
    print("  connecting...")
    try:
        bridge.start()
        bridge.set_brightness(85)
    except Exception as e:
        print(f"  \033[31mconnect failed:\033[0m {e}")
        return 2

    rates = [2, 5, 10, 20, 40]
    print("  A bright orange column will sweep back and forth at increasing speeds.")
    print("  Watch the Ditoo. Note the rate where it STOPS looking smooth or starts")
    print("  lagging behind (frames piling up / motion going sluggish).\n")
    try:
        for r in rates:
            print(f"  >>> target {r:>2d} fps for {args.seconds:.0f}s ...", end="", flush=True)
            res = sweep(bridge, r, args.seconds)
            print(f" pushed {res['frames']} frames")
            time.sleep(0.6)
    finally:
        bridge.stop()

    print("\n  Which was the FASTEST rate that still looked smooth on the device?")
    print("  (If even 40 fps looked fine, the buffer never saturated at this size.)")
    print("  Tell Claude that number — it sets the animation budget for Clawd.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

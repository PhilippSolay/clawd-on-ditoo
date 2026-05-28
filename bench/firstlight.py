#!/usr/bin/env python3
"""First light — push real Clawd sprites to the Ditoo to confirm the channel works.

Unlike display_bench.py (which pushes random noise to measure latency), this
shows recognizable images so you can SEE it working. It also prints the push
latency for each frame as a first real-world reading.

Usage:
  python3 bench/firstlight.py --mac AA:BB:CC:DD:EE:FF --channel 2
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from divoom_pet.daemon.bridge import DitooBridge, find_bundled_bridge  # noqa: E402
from divoom_pet.sprites import SPRITES, sprite_to_rgb_frame  # noqa: E402


# Recognizable sequence: hatch asterisk -> Clawd face -> wink -> happy -> think -> idle
SEQUENCE = [
    ("hatch", 2.0, "Anthropic asterisk"),
    ("idle_open", 1.5, "Clawd, eyes open"),
    ("idle_blink", 0.5, "blink"),
    ("idle_open", 1.0, "eyes open"),
    ("happy_a", 1.8, "heart pop"),
    ("thinking_b", 1.8, "thinking swirl"),
    ("tool_use", 1.8, "gear / tool"),
    ("idle_open", 1.5, "back to idle"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mac", default=os.environ.get("DITOO_MAC", "AA:BB:CC:DD:EE:FF"))
    ap.add_argument("--channel", type=int, default=2)
    ap.add_argument("--brightness", type=int, default=80)
    args = ap.parse_args()

    print(f"\033[1mFirst light\033[0m  mac={args.mac} channel={args.channel}")
    bridge = DitooBridge(binary=find_bundled_bridge(), mac=args.mac, channel=args.channel)

    print("  connecting (this opens the RFCOMM channel)...")
    try:
        bridge.start()
    except Exception as e:
        print(f"  \033[31mconnect failed:\033[0m {e}")
        print("  If this says the channel won't open, try --channel 1 (rare) or re-run discover.sh.")
        return 2

    try:
        t0 = time.perf_counter()
        bridge.set_brightness(args.brightness)
        print(f"  brightness set in {(time.perf_counter()-t0)*1000:.0f} ms")
        print("  watch the Ditoo:")
        latencies = []
        for name, hold, desc in SEQUENCE:
            frame = sprite_to_rgb_frame(SPRITES[name])
            t = time.perf_counter()
            bridge.push_image(frame)
            dt = (time.perf_counter() - t) * 1000
            latencies.append(dt)
            print(f"    {desc:22s} pushed in {dt:6.0f} ms")
            time.sleep(hold)
        if latencies:
            avg = sum(latencies) / len(latencies)
            print(f"\n  per-frame push latency: avg {avg:.0f} ms, "
                  f"min {min(latencies):.0f} / max {max(latencies):.0f} ms")
            if avg < 150:
                print("  \033[32mverdict:\033[0m fast enough for fluid animation.")
            elif avg < 300:
                print("  \033[33mverdict:\033[0m good for state changes; animation ~3-5 fps.")
            else:
                print("  \033[33mverdict:\033[0m usable but slow; favour single-image state pushes.")
    finally:
        print("  closing channel...")
        bridge.stop()
    print("\n  If you saw Clawd on the screen — we're in business.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

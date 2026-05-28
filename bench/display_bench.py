#!/usr/bin/env python3
"""Display channel benchmark.

What it measures:
  - Per-frame latency for `set_image` pushes over Bluetooth (write + ACK round trip)
  - Sustained FPS for back-to-back full-screen updates
  - ACK error rate
  - Behavior with different palette sizes (1 / 4 / 16 / 64 / 256 colors), because
    larger palettes mean larger packets and slower pushes.

What it writes:
  bench/results/display_<timestamp>.csv     — one row per push
  stdout summary table

Requires the Light half of the Ditoo to be paired and Bluetooth permission
granted. Run probe.py first.

Usage:
  python3 bench/display_bench.py --mac AA:BB:CC:DD:EE:FF [--frames 50] [--quiet]
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from divoom_pet.daemon.bridge import DitooBridge, find_bundled_bridge  # noqa: E402

RGB = Tuple[int, int, int]

CLAWD_ORANGE = (217, 119, 87)
ANTHROPIC_DARK = (20, 20, 19)
ANTHROPIC_CREAM = (250, 249, 245)


def gen_frame(palette_size: int, seed: int) -> List[RGB]:
    """Generate a deterministic 256-pixel frame with ~palette_size unique colors."""
    rng = random.Random(seed)
    palette: List[RGB] = [
        (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        for _ in range(palette_size)
    ]
    return [palette[rng.randrange(palette_size)] for _ in range(256)]


def percentile(xs: List[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * p / 100.0
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def fmt_ms(x_s: float) -> str:
    return f"{x_s * 1000:6.1f}"


PROFILES = [
    ("solid",     1),    # one-color frame — smallest packet
    ("tiny",      4),    # 4 colors — 2 bpp
    ("medium",   16),    # 16 colors — 4 bpp
    ("rich",     64),    # 64 colors — 6 bpp
    ("noise",   256),    # max palette — biggest packet
]


def benchmark(bridge: DitooBridge, frames_per_profile: int, csv_path: Path, verbose: bool) -> dict:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(csv_path, "w", newline="")
    writer = csv.writer(fh)
    writer.writerow(["timestamp", "profile", "palette_size", "frame_index", "push_latency_s", "error"])

    results: dict[str, dict] = {}

    for profile_name, palette_size in PROFILES:
        latencies: List[float] = []
        errors = 0
        if verbose:
            print(f"\n[{profile_name}] palette={palette_size}, {frames_per_profile} frames")
        t_profile_start = time.time()
        for i in range(frames_per_profile):
            frame = gen_frame(palette_size, seed=i * 31 + palette_size)
            t0 = time.perf_counter()
            err = ""
            try:
                bridge.push_image(frame)
            except Exception as e:
                err = type(e).__name__ + ": " + str(e)[:80]
                errors += 1
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            writer.writerow([
                datetime.now().isoformat(timespec="milliseconds"),
                profile_name, palette_size, i, f"{elapsed:.4f}", err,
            ])
            if verbose and (i + 1) % 10 == 0:
                print(f"  {i + 1:3d}/{frames_per_profile}  last={fmt_ms(elapsed)}ms")
        wall = time.time() - t_profile_start
        results[profile_name] = {
            "palette": palette_size,
            "n": len(latencies),
            "errors": errors,
            "mean_ms": statistics.mean(latencies) * 1000 if latencies else 0,
            "p50_ms": percentile(latencies, 50) * 1000,
            "p95_ms": percentile(latencies, 95) * 1000,
            "p99_ms": percentile(latencies, 99) * 1000,
            "fps":    len(latencies) / wall if wall > 0 else 0,
            "wall_s": wall,
        }
    fh.close()
    return results


def print_table(results: dict) -> None:
    print("\n\033[1mDisplay channel — latency by palette\033[0m")
    print(f"  {'profile':9s} {'pal':>4s} {'n':>4s} {'mean':>7s} {'p50':>7s} {'p95':>7s} {'p99':>7s} {'fps':>6s} {'err':>4s}")
    print(f"  {'-'*9} {'-'*4} {'-'*4} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*6} {'-'*4}")
    for name, r in results.items():
        print(f"  {name:9s} {r['palette']:>4d} {r['n']:>4d} "
              f"{r['mean_ms']:>6.1f}m {r['p50_ms']:>6.1f}m {r['p95_ms']:>6.1f}m {r['p99_ms']:>6.1f}m "
              f"{r['fps']:>5.1f}f {r['errors']:>4d}")
    print()
    fastest = min(results.values(), key=lambda r: r["mean_ms"])
    slowest = max(results.values(), key=lambda r: r["mean_ms"])
    print(f"  fastest: {[k for k,v in results.items() if v is fastest][0]:s} ({fastest['mean_ms']:.0f} ms avg)")
    print(f"  slowest: {[k for k,v in results.items() if v is slowest][0]:s} ({slowest['mean_ms']:.0f} ms avg)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mac", required=False, default=os.environ.get("DITOO_MAC"))
    ap.add_argument("--channel", type=int, default=1)
    ap.add_argument("--frames", type=int, default=40, help="frames per palette profile (default 40)")
    ap.add_argument("--simulate", action="store_true", help="don't touch Bluetooth (smoke test only)")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()

    if not args.mac and not args.simulate:
        ap.error("--mac required (or --simulate). Run `python3 bench/probe.py` to find it.")

    bridge_path = find_bundled_bridge()
    bridge = DitooBridge(binary=bridge_path, mac=args.mac or "00:00:00:00:00:00",
                         channel=args.channel, simulate=args.simulate)
    bridge.start()

    # Pre-warm: brightness command to make sure the channel is live before we time pushes.
    try:
        bridge.set_brightness(70)
    except Exception as e:
        print(f"set_brightness failed before timing run: {e}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = ROOT / "bench" / "results" / f"display_{stamp}.csv"

    try:
        results = benchmark(bridge, args.frames, csv_path, verbose=not args.quiet)
    finally:
        bridge.stop()

    print_table(results)
    print(f"\n  full per-frame log: {csv_path}")

    # Heuristic verdict
    rich_p95 = results.get("rich", {}).get("p95_ms", 0)
    if rich_p95 < 150:
        print("  \033[32mverdict:\033[0m display is responsive enough for real-time pet animation.")
    elif rich_p95 < 300:
        print("  \033[33mverdict:\033[0m display works but full-frame animation will feel sluggish; favour single-image state pushes.")
    else:
        print("  \033[31mverdict:\033[0m display is slow — bluetooth interference, wrong channel, or unsupported device.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Audio channel benchmark.

What it measures:
  - `say "word"` startup-to-finish wall time (includes voice synth + playback latency)
  - `afplay` wall time for a short clip (raw playback latency)
  - Variance across N trials

What it DOESN'T measure:
  - True audio-onset latency (we'd need to record the output to measure that — out of scope here).
  - Whether the Ditoo speaker is actually the active output device — pair it and select
    it in System Settings -> Sound -> Output if you want results to apply to the Ditoo.

Usage:
  python3 bench/audio_bench.py [--trials 5] [--voice "Samantha"] [--quiet]
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def percentile(xs, p):
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * p / 100.0
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def detect_output_device() -> str:
    """Best-effort: find the active audio output device name."""
    try:
        out = subprocess.check_output(
            ["system_profiler", "SPAudioDataType"],
            text=True, stderr=subprocess.DEVNULL, timeout=4.0,
        )
    except Exception:
        return "(unknown)"
    # find a "Default Output Device: Yes" block and its preceding name
    name = "(unknown)"
    current = None
    import re
    for line in out.splitlines():
        m = re.match(r"^\s{8}(\S[^:]*):$", line)
        if m:
            current = m.group(1).strip()
        if "Default Output Device: Yes" in line and current:
            name = current
    return name


def make_short_wav(path: Path, freq: float = 880, duration_s: float = 0.15, sample_rate: int = 22050) -> None:
    """Write a tiny mono PCM WAV: a single sine-wave beep. Used as the `afplay` payload."""
    import math
    samples = int(sample_rate * duration_s)
    pcm = bytearray()
    for i in range(samples):
        v = math.sin(2 * math.pi * freq * (i / sample_rate))
        # fade out the last 25 ms to avoid a click
        fade = 1.0
        fade_samples = int(sample_rate * 0.025)
        if i > samples - fade_samples:
            fade = max(0.0, (samples - i) / fade_samples)
        s = int(v * fade * 0.5 * 32767)
        pcm.extend(struct.pack("<h", s))
    data_size = len(pcm)
    with open(path, "wb") as f:
        # RIFF header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))           # subchunk1 size
        f.write(struct.pack("<H", 1))            # PCM
        f.write(struct.pack("<H", 1))            # mono
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", sample_rate * 2))
        f.write(struct.pack("<H", 2))            # block align
        f.write(struct.pack("<H", 16))           # bits/sample
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        f.write(pcm)


def measure_say(trials: int, phrase: str, voice: str | None, verbose: bool) -> list[float]:
    if not shutil.which("say"):
        print("  `say` not available — skipping")
        return []
    times = []
    for i in range(trials):
        args = ["say"]
        if voice:
            args += ["-v", voice]
        args.append(phrase)
        t0 = time.perf_counter()
        subprocess.run(args, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dt = time.perf_counter() - t0
        times.append(dt)
        if verbose:
            print(f"    say trial {i+1}/{trials}: {dt*1000:.0f} ms")
        time.sleep(0.2)
    return times


def measure_afplay(trials: int, wav_path: Path, verbose: bool) -> list[float]:
    if not shutil.which("afplay"):
        print("  `afplay` not available — skipping")
        return []
    times = []
    for i in range(trials):
        t0 = time.perf_counter()
        subprocess.run(["afplay", str(wav_path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dt = time.perf_counter() - t0
        times.append(dt)
        if verbose:
            print(f"    afplay trial {i+1}/{trials}: {dt*1000:.0f} ms")
        time.sleep(0.2)
    return times


def summarize(label: str, times: list[float]) -> dict:
    if not times:
        return {}
    return {
        "label": label,
        "n": len(times),
        "mean_ms": statistics.mean(times) * 1000,
        "p50_ms": percentile(times, 50) * 1000,
        "p95_ms": percentile(times, 95) * 1000,
        "stdev_ms": (statistics.stdev(times) * 1000) if len(times) > 1 else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--voice", default=None, help="voice to use for `say` (e.g. Samantha)")
    ap.add_argument("--phrase", default="Hello.", help="phrase to speak (short)")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()

    verbose = not args.quiet
    output_device = detect_output_device()
    print(f"\033[1mAudio channel benchmark\033[0m")
    print(f"  Default output device: {output_device}")
    print(f"  Trials per test: {args.trials}")
    if "ditoo" in output_device.lower() or "divoom" in output_device.lower():
        print(f"  \033[32mOutput is the Ditoo — these numbers reflect real device latency.\033[0m")
    else:
        print(f"  \033[33mOutput is NOT the Ditoo — these numbers reflect built-in speakers.\033[0m")
        print(f"  To benchmark the Ditoo: System Settings -> Sound -> Output -> Divoom Ditoo")

    # Generate the chime WAV
    tmp = tempfile.mkdtemp(prefix="ditoo-bench-")
    chime = Path(tmp) / "beep.wav"
    make_short_wav(chime)

    print("\n  say trials...")
    say_times = measure_say(args.trials, args.phrase, args.voice, verbose)
    print("\n  afplay trials...")
    afp_times = measure_afplay(args.trials, chime, verbose)

    say_s = summarize("say", say_times)
    afp_s = summarize("afplay", afp_times)

    # write CSV
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = ROOT / "bench" / "results" / f"audio_{stamp}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["test", "trial", "wall_seconds"])
        for i, t in enumerate(say_times):
            w.writerow(["say", i, f"{t:.4f}"])
        for i, t in enumerate(afp_times):
            w.writerow(["afplay", i, f"{t:.4f}"])

    print("\n\033[1mSummary\033[0m")
    print(f"  {'test':8s} {'n':>3s} {'mean':>8s} {'p50':>8s} {'p95':>8s} {'σ':>6s}")
    print(f"  {'-'*8} {'-'*3} {'-'*8} {'-'*8} {'-'*8} {'-'*6}")
    for s in (say_s, afp_s):
        if s:
            print(f"  {s['label']:8s} {s['n']:>3d} {s['mean_ms']:>6.0f}ms {s['p50_ms']:>6.0f}ms {s['p95_ms']:>6.0f}ms {s['stdev_ms']:>4.0f}ms")
    print(f"\n  full log: {csv_path}")

    afp_mean = afp_s.get("mean_ms", 9999)
    afp_p95 = afp_s.get("p95_ms", 9999)
    say_mean = say_s.get("mean_ms", 9999)
    is_bt = any(k in output_device.lower() for k in ("ditoo", "divoom", "airpods", "wh-1000", "megaboom", "jbl", "bluetooth"))

    if is_bt:
        # Bluetooth speakers legitimately have ~0.5-1.3s cold-start; that's physics, not a fault.
        print("  \033[36mcontext:\033[0m output is a Bluetooth speaker — cold-start latency is expected.")
        spread = afp_p95 - afp_s.get("p50_ms", afp_p95)
        if spread > 250:
            print("  \033[33mverdict:\033[0m bimodal latency detected — the radio sleeps between sounds.")
            print("            -> use a silent keep-alive tone to pin it awake (consistent ~warm latency).")
        else:
            print("  \033[32mverdict:\033[0m latency is stable; speaker is staying awake.")
        if say_mean > 1200:
            print(f"            -> live `say` is slow ({say_mean:.0f}ms); pre-render phrases to WAV and `afplay` them.")
    else:
        if afp_mean < 400 and say_mean < 800:
            print("  \033[32mverdict:\033[0m audio reaction times are well-suited to status sounds and short phrases.")
        elif afp_mean < 800:
            print("  \033[33mverdict:\033[0m chimes are fine; speech may feel laggy after triggers.")
        else:
            print("  \033[31mverdict:\033[0m audio is slow — check the output device / codec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

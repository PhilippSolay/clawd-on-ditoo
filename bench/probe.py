#!/usr/bin/env python3
"""Static probe of the user's setup — no Bluetooth permission needed.

Reports on:
  - Swift bridge binary presence + code signing
  - Paired Divoom devices (from system_profiler)
  - Audio output + input devices (looking for the Ditoo)
  - Available TTS voices (looking for preferred ones)
  - Python version

Exit code 0 if everything looks ready, 1 if something is missing that the user
needs to fix before running the live benchmarks.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIDGE_BIN = ROOT / "ditoo_bridge" / "ditoo-bridge"
BRIDGE_APP = ROOT / "ditoo_bridge" / "DitooBridge.app" / "Contents" / "MacOS" / "DitooBridge"


def ok(s: str) -> None: print(f"  \033[32m✓\033[0m {s}")
def warn(s: str) -> None: print(f"  \033[33m!\033[0m {s}")
def bad(s: str) -> None: print(f"  \033[31m✗\033[0m {s}")
def info(s: str) -> None: print(f"    {s}")


def section(title: str) -> None: print(f"\n\033[1m{title}\033[0m")


def check_bridge() -> bool:
    section("Swift bridge")
    ok_all = True
    if BRIDGE_BIN.exists():
        ok(f"binary: {BRIDGE_BIN}")
    else:
        bad(f"missing: {BRIDGE_BIN}")
        ok_all = False
    if BRIDGE_APP.exists():
        ok(f".app bundle: {BRIDGE_APP}")
    else:
        warn(f"missing .app bundle (TCC may not attribute correctly): {BRIDGE_APP}")
    if BRIDGE_BIN.exists():
        cs = subprocess.run(["codesign", "-dv", str(BRIDGE_BIN)], capture_output=True, text=True)
        if "adhoc" in cs.stderr or "Info.plist entries" in cs.stderr:
            ok("binary is ad-hoc signed with embedded Info.plist")
        else:
            warn("binary may not be properly signed — Bluetooth TCC will refuse")
            info(cs.stderr.strip())
    return ok_all


def get_bluetooth_devices() -> list[dict]:
    """Parse `system_profiler SPBluetoothDataType` for paired devices."""
    try:
        out = subprocess.check_output(["system_profiler", "SPBluetoothDataType"], text=True, stderr=subprocess.DEVNULL)
    except Exception as e:
        bad(f"system_profiler failed: {e}")
        return []
    devs: list[dict] = []
    cur: dict | None = None
    for line in out.splitlines():
        stripped = line.strip()
        m = re.match(r"^([^:]+):$", stripped)
        if m and not stripped.startswith(("State", "Address", "Vendor", "Product", "Firmware", "Minor")):
            # New device block — only if the indent is deep (devices are indented children of "Connected/Not Connected")
            if line.startswith("          "):
                cur = {"name": m.group(1).strip()}
                devs.append(cur)
                continue
        if cur:
            am = re.match(r"^Address: (\S+)", stripped)
            if am:
                cur["address"] = am.group(1)
            mt = re.match(r"^Minor Type: (.+)", stripped)
            if mt:
                cur["minor"] = mt.group(1)
    return devs


def check_bluetooth() -> tuple[bool, list[dict]]:
    section("Paired Bluetooth devices")
    devs = get_bluetooth_devices()
    divoom = [d for d in devs if any(k in d.get("name", "").lower() for k in ("divoom", "ditoo", "pixoo", "timoo"))]
    if not divoom:
        bad("no Divoom devices paired")
        info("Pair your Ditoo via System Settings -> Bluetooth.")
        return False, []
    for d in divoom:
        label = f"{d.get('name','?')}  {d.get('address','?')}"
        ok(label)
    light = [d for d in divoom if "light" in d.get("name", "").lower()]
    audio = [d for d in divoom if "audio" in d.get("name", "").lower()]
    if not light:
        warn("no *-Light device — display output won't work until paired")
    if not audio:
        warn("no *-Audio device — pet voice won't play through Ditoo")
    return True, divoom


def check_audio_devices() -> None:
    section("Audio devices (Core Audio)")
    try:
        out = subprocess.check_output(["system_profiler", "SPAudioDataType"], text=True, stderr=subprocess.DEVNULL, timeout=4.0)
    except Exception as e:
        warn(f"system_profiler SPAudioDataType failed: {e}")
        return
    # Pull the "Devices:" subtree and look for Ditoo entries; report inputs/outputs.
    in_devices = False
    cur_name = None
    has_ditoo_out = False
    has_ditoo_in = False
    for line in out.splitlines():
        m = re.match(r"^\s{8}(\S[^:]*):$", line)
        if m:
            cur_name = m.group(1).strip()
            continue
        if cur_name and "ditoo" in cur_name.lower() or cur_name and "divoom" in cur_name.lower():
            if "Input Channels" in line or "InputChannels" in line:
                has_ditoo_in = True
            if "Output Channels" in line or "OutputChannels" in line:
                has_ditoo_out = True
    if has_ditoo_out:
        ok("Ditoo enumerates as an output device")
    else:
        warn("Ditoo not currently listed as an audio output — connect/select it in System Settings -> Sound -> Output")
    if has_ditoo_in:
        ok("Ditoo enumerates as an audio input (HFP mic) — mic experiments are possible")
    else:
        info("Ditoo not currently an audio input — that's normal until something switches it into HFP/call mode")


def check_voices() -> None:
    section("TTS voices")
    if not shutil.which("say"):
        bad("`say` not in PATH (macOS TTS unavailable)")
        return
    try:
        out = subprocess.check_output(["say", "-v", "?"], text=True, timeout=2.0)
    except Exception as e:
        warn(f"say -v ? failed: {e}")
        return
    preferred = ["Zoe (Premium)", "Zoe", "Samantha (Enhanced)", "Samantha", "Karen", "Alex"]
    found = []
    for cand in preferred:
        if cand in out:
            found.append(cand)
    if found:
        ok(f"preferred voice available: {found[0]}")
        if len(found) > 1:
            info(f"also: {', '.join(found[1:])}")
    else:
        warn("none of the preferred voices found — `say` will use system default")


def main() -> int:
    print("\033[1mDivoom Ditoo bench — probe\033[0m")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Project root: {ROOT}")

    setup_ok = True
    setup_ok &= check_bridge()
    bt_ok, devs = check_bluetooth()
    setup_ok &= bt_ok
    check_audio_devices()
    check_voices()

    section("Verdict")
    if setup_ok:
        light = [d for d in devs if "light" in d.get("name", "").lower()]
        if light:
            print(f"  Ready to run live benchmarks against {light[0].get('address')}.")
            print(f"  Try:  python3 bench/display_bench.py --mac {light[0].get('address')}")
        else:
            print("  Outbound audio + voice are wired. Pair the *-Light device to enable the display.")
        return 0
    else:
        print("  Setup incomplete. Fix the items marked ✗ before running live tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

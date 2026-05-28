"""Subprocess driver for the Swift `ditoo-bridge` binary.

The bridge speaks length-prefixed framing on stdin and ack-per-packet on stdout.
We hold the subprocess open across many writes (one BT connection, many frames).
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Optional

from divoom_pet.protocol import (
    build_set_animation_from_rgb_frames,
    build_set_brightness,
    build_set_image_from_rgb,
)
from divoom_pet.protocol.divoom import bridge_close_frame, to_bridge_frame

log = logging.getLogger("bridge")


class DitooBridge:
    """Owns the Swift subprocess and serializes writes to it."""

    def __init__(self, binary: Path, mac: str, channel: int = 1, simulate: bool = False):
        self.binary = Path(binary)
        self.mac = mac
        self.channel = channel
        self.simulate = simulate
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._reader_thread: Optional[threading.Thread] = None
        self._last_reconnect = 0.0
        self._reconnect_interval = 12.0  # seconds between reconnect attempts

    # ---------- lifecycle ----------

    def start(self) -> None:
        if self.simulate:
            log.info("[bridge] simulate mode: not spawning subprocess")
            return
        if self._proc and self._proc.poll() is None:
            return
        if not self.binary.exists():
            raise FileNotFoundError(f"Swift bridge binary not found: {self.binary}")
        cmd = [str(self.binary), "send", self.mac, "--channel", str(self.channel)]
        log.info("[bridge] launching: %s", " ".join(cmd))
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        # Drain stderr in the background so we never deadlock on a full pipe.
        self._reader_thread = threading.Thread(
            target=self._drain_stderr, daemon=True, name="bridge-stderr"
        )
        self._reader_thread.start()
        # Give the bridge a moment to open the SPP channel.
        time.sleep(0.6)
        if self._proc.poll() is not None:
            err = self._proc.stderr.read().decode("utf-8", errors="replace") if self._proc.stderr else ""
            raise RuntimeError(f"Bridge exited immediately. stderr: {err}")

    def _drain_stderr(self) -> None:
        if not self._proc or not self._proc.stderr:
            return
        try:
            for line in self._proc.stderr:
                log.info("[bridge.stderr] %s", line.decode("utf-8", "replace").rstrip())
        except Exception:
            pass

    def stop(self) -> None:
        with self._lock:
            if self._proc and self._proc.poll() is None:
                try:
                    if self._proc.stdin:
                        self._proc.stdin.write(bridge_close_frame())
                        self._proc.stdin.flush()
                except Exception:
                    pass
                try:
                    self._proc.wait(timeout=1.5)
                except subprocess.TimeoutExpired:
                    self._proc.terminate()
            self._proc = None

    def is_alive(self) -> bool:
        if self.simulate:
            return True
        return self._proc is not None and self._proc.poll() is None

    def ensure_alive(self) -> bool:
        """Return True if the bridge is connected. If not, attempt a throttled
        reconnect (so the state loop can keep running and recover automatically
        when the Ditoo comes back / the channel frees up)."""
        if self.is_alive():
            return True
        now = time.time()
        if now - self._last_reconnect < self._reconnect_interval:
            return False
        self._last_reconnect = now
        log.info("[bridge] not connected; attempting reconnect...")
        try:
            self.stop()
            self.start()
        except Exception as e:
            log.warning("[bridge] reconnect failed: %s", e)
        return self.is_alive()

    # ---------- low-level send ----------

    def _send_packet(self, packet: bytes) -> None:
        if self.simulate:
            log.debug("[sim] packet %d bytes (head=%s)", len(packet), packet[:6].hex())
            return
        if not self._proc or not self._proc.stdin or self._proc.poll() is not None:
            raise RuntimeError("Bridge is not running")
        framed = to_bridge_frame(packet)
        with self._lock:
            self._proc.stdin.write(framed)
            self._proc.stdin.flush()
            # Read one-line ack (best effort; some packets may be fire-and-forget).
            try:
                if self._proc.stdout:
                    ack = self._proc.stdout.readline().decode("utf-8", "replace").strip()
                    if ack and ack != "OK":
                        log.warning("[bridge] non-OK ack: %s", ack)
            except Exception:
                pass

    # ---------- high-level commands ----------

    def set_brightness(self, value: int) -> None:
        self._send_packet(build_set_brightness(value))

    def push_image(self, rgb_pixels: List) -> None:
        self._send_packet(build_set_image_from_rgb(rgb_pixels))

    def push_animation(self, frames) -> None:
        for pkt in build_set_animation_from_rgb_frames(frames):
            self._send_packet(pkt)
            time.sleep(0.04)  # gentle pacing for the SPP channel


def find_bundled_bridge() -> Path:
    """Locate the Swift bridge binary shipped next to this package."""
    here = Path(__file__).resolve().parent.parent.parent
    candidates = [
        here / "ditoo_bridge" / "DitooBridge.app" / "Contents" / "MacOS" / "DitooBridge",
        here / "ditoo_bridge" / "ditoo-bridge",
    ]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError(
        "Could not find Swift bridge binary. Expected one of: " + ", ".join(str(c) for c in candidates)
    )

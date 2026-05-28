"""Clap-detection driver — runs the Swift `ditoo-ears` binary and fires callbacks.

The Swift helper prints `clap <unix_ms> <peak>` lines on stdout. We turn those
into single-clap and double-clap events (a double = two claps within a window).
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger("ears")


def find_ears_binary() -> Path:
    here = Path(__file__).resolve().parent.parent.parent
    candidates = [
        here / "ditoo_ears" / "DitooEars.app" / "Contents" / "MacOS" / "DitooEars",
        here / "ditoo_ears" / "ditoo-ears",
    ]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError("ditoo-ears binary not found; build it in ditoo_ears/")


class Ears:
    """Spawns the clap detector and dispatches single/double clap callbacks."""

    def __init__(
        self,
        binary: Path,
        on_clap: Callable[[], None],
        on_double_clap: Optional[Callable[[], None]] = None,
        double_window: float = 0.55,
        floor: float = 0.06,
        rise: float = 4.0,
        debounce_ms: int = 220,
        enabled: bool = True,
    ):
        self.binary = Path(binary)
        self.on_clap = on_clap
        self.on_double_clap = on_double_clap
        self.double_window = double_window
        self.floor = floor
        self.rise = rise
        self.debounce_ms = debounce_ms
        self.enabled = enabled
        self._proc: Optional[subprocess.Popen] = None
        self._reader: Optional[threading.Thread] = None
        self._stderr_reader: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._pending_single: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        self._stop.clear()  # allow restart after a previous stop()
        if not self.enabled:
            log.info("[ears] disabled")
            return
        if not self.binary.exists():
            raise FileNotFoundError(f"ears binary missing: {self.binary}")
        cmd = [
            str(self.binary),
            "--floor", str(self.floor),
            "--rise", str(self.rise),
            "--debounce", str(self.debounce_ms),
        ]
        log.info("[ears] launching: %s", " ".join(cmd))
        self._proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )
        self._reader = threading.Thread(target=self._read_stdout, daemon=True, name="ears-stdout")
        self._reader.start()
        self._stderr_reader = threading.Thread(target=self._read_stderr, daemon=True, name="ears-stderr")
        self._stderr_reader.start()
        time.sleep(0.4)
        if self._proc.poll() is not None:
            err = self._proc.stderr.read() if self._proc.stderr else ""
            raise RuntimeError(f"ears exited immediately: {err}")

    def _read_stderr(self) -> None:
        if not self._proc or not self._proc.stderr:
            return
        for line in self._proc.stderr:
            if self._stop.is_set():
                return
            log.info("[ears] %s", line.rstrip())

    def _read_stdout(self) -> None:
        if not self._proc or not self._proc.stdout:
            return
        for line in self._proc.stdout:
            if self._stop.is_set():
                return
            line = line.strip()
            if not line.startswith("clap"):
                continue
            self._handle_clap()

    def _handle_clap(self) -> None:
        with self._lock:
            if self._pending_single is not None:
                # This is the second clap within the window -> double clap.
                self._pending_single.cancel()
                self._pending_single = None
                self._fire_double()
                return
            # First clap: wait to see if a second arrives.
            if self.on_double_clap is None:
                # No double handler — just fire single immediately.
                self._fire_single()
                return
            self._pending_single = threading.Timer(self.double_window, self._fire_single_timeout)
            self._pending_single.daemon = True
            self._pending_single.start()

    def _fire_single_timeout(self) -> None:
        with self._lock:
            self._pending_single = None
        self._fire_single()

    def _fire_single(self) -> None:
        log.info("[ears] CLAP (single)")
        try:
            self.on_clap()
        except Exception as e:
            log.warning("on_clap failed: %s", e)

    def _fire_double(self) -> None:
        log.info("[ears] CLAP CLAP (double)")
        try:
            if self.on_double_clap:
                self.on_double_clap()
        except Exception as e:
            log.warning("on_double_clap failed: %s", e)

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            if self._pending_single:
                self._pending_single.cancel()
                self._pending_single = None
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=1.0)
            except Exception:
                pass
        self._proc = None

    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def set_enabled(self, on: bool) -> None:
        """Turn clap detection on/off live."""
        self.enabled = on
        if on and not self.is_alive():
            self.start()
        elif not on and self.is_alive():
            self.stop()

    def reconfigure(self, floor: float, rise: float, double_window: float) -> None:
        """Apply new clap sensitivity. Restarts the subprocess since these are
        launch arguments of the Swift detector."""
        self.floor = floor
        self.rise = rise
        self.double_window = double_window
        if self.is_alive():
            self.stop()
            self.start()

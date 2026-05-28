"""Pet state machine + animation loop.

The state machine has one current State. A background thread renders the
animation loop for the current state, pushing frames over the bridge.

Switching states is atomic: we cancel the current frame loop and restart with
the new animation. A state may auto-transition (e.g. ALERT -> IDLE after 4s).
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from divoom_pet.sprites import DEFAULT_IDLE, IdleOpts, State, animation_for_state, sprite_to_rgb_frame
from divoom_pet.voice.sounds import STATE_CHIRP, STATE_SPEAK, SoundPlayer

from .bridge import DitooBridge

log = logging.getLogger("state")


# Auto-transition table: after T seconds in this state, fall back to fallback.
AUTO_TIMEOUTS = {
    State.ALERT: (3.0, State.IDLE),
    State.HAPPY: (2.6, State.IDLE),
    State.HATCH: (3.5, State.IDLE),
    State.TOOL_USE: (4.0, State.IDLE),
    State.TYPING: (8.0, State.IDLE),
    State.THINKING: (60.0, State.IDLE),  # safety net
    State.POKE: (1.6, State.IDLE),
}

# Idle -> Sleeping after N seconds with no activity. Generous so Clawd stays
# awake through normal reading/thinking pauses and only naps when you've left.
IDLE_TO_SLEEP_AFTER = 240.0


@dataclass
class PetController:
    bridge: DitooBridge
    sounds: Optional[SoundPlayer] = None
    brightness: int = 70
    idle_to_sleep: float = IDLE_TO_SLEEP_AFTER
    idle_opts: IdleOpts = field(default_factory=lambda: DEFAULT_IDLE)
    _state: State = State.IDLE
    _state_started_at: float = field(default_factory=time.time)
    _last_activity_at: float = field(default_factory=time.time)
    _stop: threading.Event = field(default_factory=threading.Event)
    _state_changed: threading.Event = field(default_factory=threading.Event)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _loop_thread: Optional[threading.Thread] = None

    def start(self, initial_state: State = State.HATCH) -> None:
        # Tolerate an initial connection failure — the loop will keep retrying via
        # ensure_alive() so the daemon recovers when the Ditoo/channel comes back.
        try:
            self.bridge.start()
            self.bridge.set_brightness(self.brightness)
        except Exception as e:
            log.warning("bridge start failed (%s); will keep retrying in background", e)
        self._loop_thread = threading.Thread(target=self._run, daemon=True, name="pet-loop")
        self._loop_thread.start()
        self.set_state(initial_state, note="boot")

    def stop(self) -> None:
        self._stop.set()
        self._state_changed.set()
        if self._loop_thread:
            self._loop_thread.join(timeout=1.5)
        self.bridge.stop()

    # ---------- public api ----------

    def set_state(self, state: State, note: str = "") -> None:
        with self._lock:
            if state == self._state and state != State.HAPPY and state != State.ALERT:
                # Already in this state; ignore noisy re-entries (but allow re-triggers
                # for one-shot reactions like HAPPY / ALERT).
                self._last_activity_at = time.time()
                return
            log.info("state: %s -> %s  (%s)", self._state.value, state.value, note)
            self._state = state
            self._state_started_at = time.time()
            self._last_activity_at = time.time()
            self._state_changed.set()
        self._play_sounds_for(state)

    def _play_sounds_for(self, state: State) -> None:
        if not self.sounds:
            return
        chirp = STATE_CHIRP.get(state.value)
        if chirp:
            self.sounds.chirp(chirp)
        spoken = STATE_SPEAK.get(state.value)
        if spoken:
            self.sounds.speak(spoken)

    def current_state(self) -> State:
        with self._lock:
            return self._state

    def touch(self) -> None:
        """Mark recent activity; resets idle->sleep timer."""
        self._last_activity_at = time.time()

    def set_brightness(self, value: int) -> None:
        """Update display brightness now (best-effort; survives a dead bridge)."""
        self.brightness = value
        try:
            if self.bridge.is_alive():
                self.bridge.set_brightness(value)
        except Exception as e:
            log.debug("set_brightness failed: %s", e)

    def poke(self) -> None:
        """React to a clap: startle + delight, then settle back to idle."""
        self.set_state(State.POKE, note="clap")

    def toggle_sleep(self) -> None:
        """Double-clap: wake a sleeping crab, or send an awake one to nap."""
        if self.current_state() == State.SLEEPING:
            self.set_state(State.POKE, note="double-clap wake")
        else:
            self.set_state(State.SLEEPING, note="double-clap sleep")

    # ---------- internal loop ----------

    def _run(self) -> None:
        while not self._stop.is_set():
            with self._lock:
                current = self._state
                idle_opts = self.idle_opts
            anim = animation_for_state(current, idle_opts)
            # Render the animation once. After it loops we re-check state.
            for sprite, duration_ms in anim:
                if self._stop.is_set():
                    return
                # Only push when connected; ensure_alive() reconnects (throttled)
                # without spamming, so a dropped link recovers on its own.
                if self.bridge.ensure_alive():
                    try:
                        self.bridge.push_image(sprite_to_rgb_frame(sprite))
                    except Exception as e:
                        log.debug("push_image failed: %s", e)
                # Wait the duration, but break early if state changed.
                if self._state_changed.wait(timeout=max(0.04, duration_ms / 1000.0)):
                    self._state_changed.clear()
                    break
            else:
                # Animation completed without interruption; check auto-transitions.
                self._maybe_auto_transition()

    def _maybe_auto_transition(self) -> None:
        with self._lock:
            now = time.time()
            current = self._state
            elapsed = now - self._state_started_at
            idle_for = now - self._last_activity_at

            if current in AUTO_TIMEOUTS:
                timeout, fallback = AUTO_TIMEOUTS[current]
                if elapsed >= timeout:
                    log.info("auto-transition: %s -> %s after %.1fs", current.value, fallback.value, elapsed)
                    self._state = fallback
                    self._state_started_at = now
                    self._state_changed.set()
                    return

            if current == State.IDLE and idle_for >= self.idle_to_sleep:
                log.info("idle for %.0fs -> sleeping", idle_for)
                self._state = State.SLEEPING
                self._state_started_at = now
                self._state_changed.set()

"""Switchable sound themes for Clawd.

Each event (wake / think / tool / done / error / sleep / poke) has one shared
*gesture* — a little melody — and each theme renders those gestures through its own
*voice* (timbre). So the semantics stay consistent across themes while the
character changes completely:

  - chip       the original 8-bit square-wave chiptune (retro)
  - marimba    warm wooden mallet — soft, rounded, friendly (the default)
  - music_box  bell / glockenspiel with a touch of echo — magical, alive
  - bubbly     playful pitch-glide "bloops" — bouncy, organic

A theme is a dict ``event -> [generator_fns]`` (same shape as the legacy CHIRPS),
so the renderer treats every theme identically.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from .synth import Samples, Voice, additive, echo, glide, lowpass, pack, render_gesture

# Shared melodies (note, duration_s). 'R' is a rest.
GESTURES: Dict[str, List[Tuple[str, float]]] = {
    "wake":  [("C5", 0.11), ("E5", 0.11), ("G5", 0.20)],
    "think": [("E5", 0.12), ("R", 0.05), ("C5", 0.17)],
    "tool":  [("A5", 0.06), ("E5", 0.08)],
    "done":  [("C5", 0.10), ("E5", 0.10), ("G5", 0.10), ("C6", 0.24)],
    "error": [("G4", 0.16), ("Eb4", 0.28)],
    "sleep": [("G4", 0.22), ("E4", 0.22), ("C4", 0.36)],
    "poke":  [("E6", 0.06), ("B6", 0.13)],
}


# -------------------- voices (timbres) --------------------


def _marimba_voice(f: float, dur: float) -> Samples:
    s = additive(f, dur, [(1, 1.0), (4, 0.40), (8, 0.12)],
                 attack=0.004, decay=min(0.45, dur * 1.5), volume=0.55)
    return lowpass(s, 0.50)


def _musicbox_voice(f: float, dur: float) -> Samples:
    # Slightly inharmonic partials → bell shimmer; long decay + echo for sparkle.
    s = additive(f, dur, [(1, 1.0), (2, 0.50), (3.46, 0.28), (5.43, 0.12)],
                 attack=0.003, decay=min(0.9, dur * 2.4), detune_cents=6, volume=0.40)
    return echo(s, delay_s=0.09, decay=0.28, repeats=2)


def _bubbly_voice(f: float, dur: float) -> Samples:
    # Each note slides down a touch into pitch → a soft "bloop".
    s = glide(f * 1.18, f, dur, attack=0.006, decay=min(0.4, dur * 1.3), volume=0.55)
    return lowpass(s, 0.42)


# -------------------- theme assembly --------------------


def _theme_from_voice(voice: Voice, gap: float = 0.012) -> Dict[str, List[Callable]]:
    """Build an event→[generator] dict by rendering every gesture through `voice`."""
    from .sounds import _s_keepalive  # theme-independent near-silent keep-warm tone

    theme: Dict[str, List[Callable]] = {}
    for event, notes in GESTURES.items():
        theme[event] = [lambda notes=notes: pack(render_gesture(notes, voice, gap=gap))]
    theme["keepalive"] = [_s_keepalive]
    return theme


THEME_BUILDERS: Dict[str, Callable[[], Dict[str, List[Callable]]]] = {
    "marimba": lambda: _theme_from_voice(_marimba_voice, gap=0.012),
    "music_box": lambda: _theme_from_voice(_musicbox_voice, gap=0.02),
    "bubbly": lambda: _theme_from_voice(_bubbly_voice, gap=0.01),
}

# Display order for menus / CLI. "chip" is the legacy CHIRPS in sounds.py.
BUILTIN_THEMES: List[str] = ["marimba", "music_box", "bubbly", "chip"]
DEFAULT_THEME = "marimba"


def get_theme(name: str) -> Dict[str, List[Callable]]:
    """Return the event→[generator] dict for a theme. Unknown / 'chip' → legacy."""
    builder = THEME_BUILDERS.get(name)
    if builder:
        return builder()
    from .sounds import CHIRPS
    return dict(CHIRPS)

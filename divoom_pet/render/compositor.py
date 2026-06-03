"""Flatten Clawd's mood + data overlays into a single 16×16 frame.

This is the heart of the "mood vs content" split: `compose(base, overlays)` draws
the emotional sprite (`base`) onto a fresh Canvas, then lets each overlay draw its
data on top, and freezes the result. Overlays are small frozen dataclasses with a
`.draw(canvas)` method — persistent things like a progress bar or a count badge.

Big one-shot moments (a "MERGED" marquee) are *takeovers*, not overlays: full
animations returned as (frame, duration_ms) lists by helpers like `banner`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from divoom_pet.sprites import CLAWD_PALETTE

from .canvas import BLACK, WIDTH, Canvas, RGB
from .colors import COLORS
from .font import GLYPH_H, draw_text, text_width

Frame = List[RGB]


# -------------------- base + overlay composition --------------------


def _draw_base(canvas: Canvas, base) -> None:
    """Draw whatever `base` is onto the canvas: a Sprite, raw char rows, a flat
    256-RGB frame, or None (leave the background)."""
    if base is None:
        return
    rows = getattr(base, "rows", None)
    if rows is not None:
        canvas.blit_sprite(rows, CLAWD_PALETTE)
        return
    if isinstance(base, Sequence) and base:
        first = base[0]
        if isinstance(first, str):
            canvas.blit_sprite(base, CLAWD_PALETTE)
        else:
            canvas.blit_frame(base)


def compose(base, overlays: Sequence["Overlay"] = ()) -> Frame:
    """Compose `base` (mood) + `overlays` (data) into a fresh 256-RGB frame."""
    canvas = Canvas()
    _draw_base(canvas, base)
    for overlay in overlays:
        overlay.draw(canvas)
    return canvas.to_frame()


def compose_animation(
    anim: Sequence[Tuple[object, int]], overlays: Sequence["Overlay"] = ()
) -> List[Tuple[Frame, int]]:
    """Map an animation of (sprite, duration_ms) into composited (frame, ms) pairs,
    applying the same overlays to every frame."""
    return [(compose(sprite, overlays), ms) for sprite, ms in anim]


# -------------------- overlays --------------------


class Overlay:
    """Structural base: anything with `draw(canvas)` is a valid overlay. Subclass
    or just duck-type. Kept as a class for isinstance-friendliness and docs."""

    def draw(self, canvas: Canvas) -> None:  # pragma: no cover - interface
        raise NotImplementedError


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass(frozen=True)
class ProgressBar(Overlay):
    """A horizontal fill bar. By default a 1px bar pinned to the bottom row."""

    value: float                       # 0..1
    row: int = WIDTH - 1               # bottom row
    height: int = 1
    fg: RGB = COLORS["green"]
    track: Optional[RGB] = COLORS["dim"]  # None = leave pixels under the empty part
    x: int = 0
    width: int = WIDTH

    def draw(self, canvas: Canvas) -> None:
        filled = round(_clamp01(self.value) * self.width)
        for dy in range(self.height):
            y = self.row + dy
            if self.track is not None:
                canvas.hline(self.x, y, self.width, self.track)
            if filled > 0:
                canvas.hline(self.x, y, filled, self.fg)


_CORNERS = {"tl", "tr", "bl", "br"}


@dataclass(frozen=True)
class CountBadge(Overlay):
    """A small number tucked into a corner — e.g. how many agents came home."""

    count: int
    corner: str = "tr"
    color: RGB = COLORS["yellow"]
    backing: Optional[RGB] = COLORS["black"]  # dark box behind digits for legibility
    max_digits: int = 2

    def _text(self) -> str:
        ceiling = 10 ** self.max_digits - 1
        if self.count > ceiling:
            return f"{ceiling}+"[: self.max_digits + 1]
        return str(max(0, self.count))

    def draw(self, canvas: Canvas) -> None:
        text = self._text()
        w = text_width(text)
        corner = self.corner if self.corner in _CORNERS else "tr"
        x = 0 if corner in ("tl", "bl") else WIDTH - w
        y = 0 if corner in ("tl", "tr") else WIDTH - GLYPH_H
        if self.backing is not None:
            canvas.rect(x - 1, y - 1, w + 2, GLYPH_H + 2, self.backing, fill=True)
        draw_text(canvas, x, y, text, self.color)


# Canonical session states (shared with the daemon's SessionRegistry) + their dot
# colors. Defined here in the render layer because the SessionBar overlay owns the
# visual vocabulary; the daemon imports these names.
SESSION_RUNNING = "running"
SESSION_FINISHED = "finished"
SESSION_NEEDS_INPUT = "needs_input"
SESSION_IDLE = "idle"

SESSION_COLORS = {
    SESSION_RUNNING: COLORS["amber"],     # actively working
    SESSION_FINISHED: COLORS["green"],    # turn complete
    SESSION_NEEDS_INPUT: COLORS["red"],   # waiting on you
    SESSION_IDLE: COLORS["dim"],          # quiet
}


@dataclass(frozen=True)
class SessionBar(Overlay):
    """A strip of status dots along the bottom — one per live Claude Code session,
    colored by state. `states` is ordered by session age so each keeps its slot."""

    states: Tuple[str, ...]
    row: int = WIDTH - 1   # bottom row (below Clawd's legs)
    pitch: int = 2         # px between dot starts; auto-tightens when crowded

    def draw(self, canvas: Canvas) -> None:
        n = len(self.states)
        if n == 0:
            return
        pitch = self.pitch if n * self.pitch <= WIDTH else 1  # pack tighter if many
        for i, state in enumerate(self.states[:WIDTH]):
            canvas.set_pixel(i * pitch, self.row, SESSION_COLORS.get(state, COLORS["dim"]))


# -------------------- takeovers (one-shot animations) --------------------


def banner(
    text: str,
    color: RGB = COLORS["orange"],
    y: int = 5,
    bg: RGB = BLACK,
    step_px: int = 1,
    step_ms: int = 90,
    tail_px: int = 6,
) -> List[Tuple[Frame, int]]:
    """A scrolling marquee of `text`, right-to-left across the display. Returns
    (frame, duration_ms) pairs ready for `PetController.play_takeover`."""
    w = text_width(text)
    start_x = WIDTH
    end_x = -(w + tail_px)
    frames: List[Tuple[Frame, int]] = []
    x = start_x
    while x > end_x:
        canvas = Canvas(bg)
        draw_text(canvas, x, y, text, color)
        frames.append((canvas.to_frame(), step_ms))
        x -= step_px
    return frames or [(Canvas(bg).to_frame(), step_ms)]

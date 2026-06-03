"""A 16×16 drawing surface for procedural frames and compositing.

A `Canvas` is the codebase's one sanctioned *transient builder* (think
StringBuilder): you create one, draw into it — these calls mutate the builder's
private pixel buffer — then freeze it to an immutable 256-RGB frame with
`to_frame()`. All *domain* data (sprites, frames, configs, overlays) stays
immutable; only this short-lived, never-escaping builder is mutated.

Drawing is bounds-safe: pixels outside 0..15 are silently clipped, so you can
blit a sprite partly off-screen (for slide-in / scroll effects) without guarding
every coordinate yourself.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

RGB = Tuple[int, int, int]

WIDTH = 16
HEIGHT = 16
PIXELS = WIDTH * HEIGHT
BLACK: RGB = (0, 0, 0)

# Default transparent key for char-grid sprites (matches the sprite palette's '.').
TRANSPARENT_KEY = "."


class Canvas:
    """Mutable 16×16 RGB scratch buffer. Drawing ops return `self` for chaining."""

    __slots__ = ("_px",)

    def __init__(self, background: RGB = BLACK):
        self._px: List[RGB] = [background] * PIXELS

    # ---------- primitives ----------

    def set_pixel(self, x: int, y: int, color: RGB) -> "Canvas":
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self._px[y * WIDTH + x] = color
        return self

    def get_pixel(self, x: int, y: int) -> RGB:
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            return self._px[y * WIDTH + x]
        return BLACK

    def fill(self, color: RGB) -> "Canvas":
        self._px = [color] * PIXELS
        return self

    def hline(self, x: int, y: int, length: int, color: RGB) -> "Canvas":
        for i in range(length):
            self.set_pixel(x + i, y, color)
        return self

    def vline(self, x: int, y: int, length: int, color: RGB) -> "Canvas":
        for i in range(length):
            self.set_pixel(x, y + i, color)
        return self

    def rect(self, x: int, y: int, w: int, h: int, color: RGB, fill: bool = False) -> "Canvas":
        if w <= 0 or h <= 0:
            return self
        if fill:
            for row in range(h):
                self.hline(x, y + row, w, color)
            return self
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)
        return self

    # ---------- compositing ----------

    def blit_sprite(
        self,
        rows: Sequence[str],
        palette,
        dx: int = 0,
        dy: int = 0,
        transparent: str = TRANSPARENT_KEY,
    ) -> "Canvas":
        """Draw a char-grid sprite (list of equal-ish-length strings). Characters
        equal to `transparent` are skipped (left showing whatever's underneath);
        every other char is looked up in `palette` (missing → black)."""
        for row_idx, row in enumerate(rows):
            for col_idx, ch in enumerate(row):
                if ch == transparent:
                    continue
                self.set_pixel(col_idx + dx, row_idx + dy, palette.get(ch, BLACK))
        return self

    def blit_frame(
        self,
        frame: Sequence[RGB],
        dx: int = 0,
        dy: int = 0,
        transparent: Optional[RGB] = None,
        width: int = WIDTH,
    ) -> "Canvas":
        """Draw another flat RGB frame at an offset. If `transparent` is given,
        pixels matching it are skipped (used for layering pre-baked frames)."""
        for i, color in enumerate(frame):
            if transparent is not None and color == transparent:
                continue
            self.set_pixel((i % width) + dx, (i // width) + dy, color)
        return self

    # ---------- freeze ----------

    def to_frame(self) -> List[RGB]:
        """Return a fresh 256-RGB list (independent copy) for the bridge."""
        return list(self._px)

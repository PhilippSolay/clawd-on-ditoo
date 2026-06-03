"""A tiny procedural clock face for the 16×16 panel.

HH:MM won't fit on one row at 3px/glyph, so we stack it: hours on top, minutes
below, with a blinking dot separator between. Drawn with the same pixel font as
everything else, so it composes and recolors like any other content.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .canvas import BLACK, WIDTH, Canvas, RGB
from .colors import COLORS
from .font import GLYPH_H, draw_text, text_width

Frame = List[RGB]
Anim = List[Tuple[Frame, int]]


def clock_frame(hh: int, mm: int, color: RGB = COLORS["cyan"],
                bg: RGB = BLACK, separator: bool = True) -> Frame:
    """A single stacked HH / MM clock frame. `separator` draws the blink dots."""
    cv = Canvas(bg)
    top = f"{hh:02d}"
    bottom = f"{mm:02d}"
    tx = (WIDTH - text_width(top)) // 2
    bx = (WIDTH - text_width(bottom)) // 2
    draw_text(cv, tx, 1, top, color)            # hours, rows 1..5
    draw_text(cv, bx, WIDTH - GLYPH_H - 1, bottom, color)  # minutes, rows 10..14
    if separator:
        cv.set_pixel(WIDTH // 2 - 1, 7, color)  # the two ":" blink dots, centered
        cv.set_pixel(WIDTH // 2, 8, color)
    return cv.to_frame()


def clock_takeover(hh: int, mm: int, color: RGB = COLORS["cyan"],
                   hold_ms: int = 2600, blinks: int = 3) -> Anim:
    """Show the time for a few seconds, blinking the separator like a digital clock."""
    on = clock_frame(hh, mm, color, separator=True)
    off = clock_frame(hh, mm, color, separator=False)
    per = max(120, hold_ms // max(1, blinks * 2))
    frames: Anim = []
    for _ in range(blinks):
        frames.append((on, per))
        frames.append((off, per))
    return frames

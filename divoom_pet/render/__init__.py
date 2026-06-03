"""Procedural rendering: a tiny drawing surface, a pixel font, and a compositor.

This package is the "content" half of Clawd — the layer that draws data (progress
bars, counters, banners) and composites it on top of his emotional sprite. It is
deliberately dependency-free at runtime (PIL lives only in `preview.py`, which is
imported on demand for offline previews, never by the daemon).
"""

from .canvas import BLACK, HEIGHT, PIXELS, RGB, WIDTH, Canvas
from .colors import COLORS, parse_color
from .compositor import CountBadge, Overlay, ProgressBar, banner, compose
from .font import draw_text, text_width

__all__ = [
    "Canvas",
    "RGB",
    "WIDTH",
    "HEIGHT",
    "PIXELS",
    "BLACK",
    "COLORS",
    "parse_color",
    "draw_text",
    "text_width",
    "compose",
    "Overlay",
    "ProgressBar",
    "CountBadge",
    "banner",
]

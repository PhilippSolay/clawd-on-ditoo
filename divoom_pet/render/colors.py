"""Named colors for procedural content, plus a tolerant parser.

Keeps the palette consistent with Clawd's sprite colors (Anthropic orange et al.)
so overlays and banners feel like they belong to the same character.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

RGB = Tuple[int, int, int]

# Curated palette. Names are lowercase; aliases included where handy.
COLORS = {
    "black": (0, 0, 0),
    "white": (254, 253, 249),
    "cream": (250, 249, 245),
    "orange": (217, 119, 87),   # Anthropic primary #d97757 — Clawd's shell
    "clawd": (217, 119, 87),
    "rust": (164, 78, 54),      # shell shadow
    "green": (74, 201, 126),
    "lime": (140, 220, 90),
    "red": (214, 67, 58),
    "magenta": (227, 90, 139),  # heart
    "pink": (227, 90, 139),
    "yellow": (242, 196, 99),   # Anthropic asterisk
    "amber": (242, 196, 99),
    "blue": (106, 155, 204),    # sleepy z
    "cyan": (96, 199, 210),
    "purple": (150, 120, 210),
    "gray": (90, 90, 90),
    "grey": (90, 90, 90),
    "dim": (40, 40, 40),        # backing/track color
}


def _clamp8(v) -> int:
    return max(0, min(255, int(v)))


def parse_color(value, default: RGB = (217, 119, 87)) -> RGB:
    """Coerce a name ('green'), a hex string ('#d97757' / 'd97757'), or an
    [r, g, b] sequence into an RGB tuple. Unknown / malformed → `default`."""
    if value is None:
        return default
    if isinstance(value, str):
        key = value.strip().lower()
        if key in COLORS:
            return COLORS[key]
        hexstr = key[1:] if key.startswith("#") else key
        if len(hexstr) == 6:
            try:
                return (int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16))
            except ValueError:
                return default
        return default
    if isinstance(value, Sequence) and len(value) == 3:
        try:
            return (_clamp8(value[0]), _clamp8(value[1]), _clamp8(value[2]))
        except (TypeError, ValueError):
            return default
    return default

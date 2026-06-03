"""A 3×5 pixel font for tiny labels and scrolling banners.

Each glyph is 3 wide × 5 tall, drawn as five '#'/'.' rows. At 3px wide + 1px gap,
four glyphs fit across the 16px display; anything longer scrolls (see
`compositor.banner`). Lookups are case-folded to uppercase; unknown characters
render as blank space, so arbitrary text never raises.

M / N / W are unavoidable approximations at 3px wide — fine for the short labels
Clawd actually shows (PR, OK, DONE, MERGED, AGENTS, TESTS, CI…).
"""

from __future__ import annotations

from typing import Dict, Tuple

from .canvas import RGB, Canvas

GLYPH_W = 3
GLYPH_H = 5
GLYPH_SPACING = 1  # blank columns between glyphs

_BLANK = ("...", "...", "...", "...", "...")

# 3×5 glyph table. Keys are uppercase; digits, A–Z, and a handful of symbols.
GLYPHS: Dict[str, Tuple[str, str, str, str, str]] = {
    " ": _BLANK,
    "0": ("###", "#.#", "#.#", "#.#", "###"),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"),
    "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"),
    "7": ("###", "..#", "..#", "..#", "..#"),
    "8": ("###", "#.#", "###", "#.#", "###"),
    "9": ("###", "#.#", "###", "..#", "###"),
    "A": ("###", "#.#", "###", "#.#", "#.#"),
    "B": ("##.", "#.#", "##.", "#.#", "##."),
    "C": ("###", "#..", "#..", "#..", "###"),
    "D": ("##.", "#.#", "#.#", "#.#", "##."),
    "E": ("###", "#..", "##.", "#..", "###"),
    "F": ("###", "#..", "##.", "#..", "#.."),
    "G": ("###", "#..", "#.#", "#.#", "###"),
    "H": ("#.#", "#.#", "###", "#.#", "#.#"),
    "I": ("###", ".#.", ".#.", ".#.", "###"),
    "J": ("..#", "..#", "..#", "#.#", "###"),
    "K": ("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": ("#..", "#..", "#..", "#..", "###"),
    "M": ("#.#", "###", "###", "#.#", "#.#"),
    "N": ("##.", "#.#", "#.#", "#.#", ".##"),
    "O": ("###", "#.#", "#.#", "#.#", "###"),
    "P": ("###", "#.#", "###", "#..", "#.."),
    "Q": ("###", "#.#", "#.#", "###", "..#"),
    "R": ("###", "#.#", "###", "##.", "#.#"),
    "S": ("###", "#..", "###", "..#", "###"),
    "T": ("###", ".#.", ".#.", ".#.", ".#."),
    "U": ("#.#", "#.#", "#.#", "#.#", "###"),
    "V": ("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": ("#.#", "#.#", "###", "###", "#.#"),
    "X": ("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": ("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": ("###", "..#", ".#.", "#..", "###"),
    "%": ("#.#", "..#", ".#.", "#..", "#.#"),
    "+": ("...", ".#.", "###", ".#.", "..."),
    "-": ("...", "...", "###", "...", "..."),
    ":": ("...", ".#.", "...", ".#.", "..."),
    ".": ("...", "...", "...", "...", ".#."),
    "!": (".#.", ".#.", ".#.", "...", ".#."),
    "?": ("###", "..#", ".#.", "...", ".#."),
    ">": ("#..", ".#.", "..#", ".#.", "#.."),
    "<": ("..#", ".#.", "#..", ".#.", "..#"),
    "/": ("..#", "..#", ".#.", "#..", "#.."),
    "*": ("...", "#.#", ".#.", "#.#", "..."),
    "HEART": ("#.#", "###", "###", ".#.", "..."),
}

# Aliases so callers can use a friendly literal in text strings.
GLYPHS["♥"] = GLYPHS["HEART"]  # ♥


def glyph(ch: str) -> Tuple[str, str, str, str, str]:
    return GLYPHS.get(ch.upper(), _BLANK)


def text_width(s: str, spacing: int = GLYPH_SPACING) -> int:
    """Pixel width of `s` rendered with `draw_text` (no trailing gap)."""
    if not s:
        return 0
    return len(s) * GLYPH_W + (len(s) - 1) * spacing


def draw_text(
    canvas: Canvas,
    x: int,
    y: int,
    s: str,
    color: RGB,
    spacing: int = GLYPH_SPACING,
) -> int:
    """Draw `s` onto `canvas` with its top-left at (x, y). Bounds-safe (off-canvas
    columns clip). Returns the x just past the last glyph (for chaining)."""
    cursor = x
    for ch in s:
        rows = glyph(ch)
        for row_idx, row in enumerate(rows):
            for col_idx, cell in enumerate(row):
                if cell != ".":
                    canvas.set_pixel(cursor + col_idx, y + row_idx, color)
        cursor += GLYPH_W + spacing
    return cursor - spacing if s else x

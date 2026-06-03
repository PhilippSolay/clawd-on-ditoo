"""Unit tests for the 3×5 pixel font."""

import unittest

from divoom_pet.render.canvas import BLACK, Canvas
from divoom_pet.render.font import GLYPH_H, GLYPH_W, GLYPHS, draw_text, glyph, text_width

WHITE = (255, 255, 255)


class GlyphTableTests(unittest.TestCase):
    def test_every_glyph_is_3x5(self):
        for ch, rows in GLYPHS.items():
            self.assertEqual(len(rows), GLYPH_H, f"{ch} wrong height")
            for r in rows:
                self.assertEqual(len(r), GLYPH_W, f"{ch} row {r!r} wrong width")

    def test_unknown_char_is_blank(self):
        self.assertEqual(glyph("¡"), GLYPHS[" "])

    def test_lookup_is_case_insensitive(self):
        self.assertEqual(glyph("a"), GLYPHS["A"])


class TextWidthTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(text_width(""), 0)

    def test_single_char_no_trailing_gap(self):
        self.assertEqual(text_width("8"), GLYPH_W)

    def test_multi_char_includes_inter_glyph_gaps(self):
        # 3 chars: 3*3 + 2 gaps = 11
        self.assertEqual(text_width("123"), 3 * GLYPH_W + 2)


class DrawTextTests(unittest.TestCase):
    def test_draws_pixels_for_filled_cells(self):
        c = Canvas()
        draw_text(c, 0, 0, "1", WHITE)
        # '1' glyph: (".#.", "##.", ".#.", ".#.", "###") -> (1,0) set, (0,0) not
        self.assertEqual(c.get_pixel(1, 0), WHITE)
        self.assertEqual(c.get_pixel(0, 0), BLACK)
        self.assertEqual(c.get_pixel(0, 4), WHITE)  # bottom row "###"

    def test_returns_end_cursor(self):
        c = Canvas()
        end = draw_text(c, 0, 0, "12", WHITE)
        self.assertEqual(end, text_width("12"))

    def test_offscreen_text_is_clipped_not_raised(self):
        c = Canvas()
        # Far off the right edge; should draw nothing in-bounds and not raise.
        draw_text(c, 30, 0, "HELLO", WHITE)
        self.assertTrue(all(px == BLACK for px in c.to_frame()))

    def test_negative_x_partial_render(self):
        c = Canvas()
        # "88" starting at x=-4 puts the second 8 partly on-screen; just shouldn't raise.
        draw_text(c, -4, 0, "88", WHITE)
        # at least one white pixel should be visible
        self.assertTrue(any(px == WHITE for px in c.to_frame()))


if __name__ == "__main__":
    unittest.main()

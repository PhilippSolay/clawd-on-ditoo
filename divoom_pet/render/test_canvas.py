"""Unit tests for the Canvas drawing surface."""

import unittest

from divoom_pet.render.canvas import BLACK, PIXELS, WIDTH, Canvas

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


class CanvasBasicsTests(unittest.TestCase):
    def test_starts_black_and_right_size(self):
        frame = Canvas().to_frame()
        self.assertEqual(len(frame), PIXELS)
        self.assertTrue(all(px == BLACK for px in frame))

    def test_background_color(self):
        self.assertTrue(all(px == RED for px in Canvas(RED).to_frame()))

    def test_set_and_get_pixel(self):
        c = Canvas()
        c.set_pixel(3, 4, RED)
        self.assertEqual(c.get_pixel(3, 4), RED)
        self.assertEqual(c.to_frame()[4 * WIDTH + 3], RED)

    def test_out_of_bounds_is_clipped_not_raised(self):
        c = Canvas()
        # None of these should raise or alter in-bounds pixels.
        c.set_pixel(-1, 0, RED).set_pixel(16, 0, RED).set_pixel(0, 99, RED)
        self.assertTrue(all(px == BLACK for px in c.to_frame()))
        self.assertEqual(c.get_pixel(-1, -1), BLACK)

    def test_to_frame_returns_independent_copy(self):
        c = Canvas()
        frame = c.to_frame()
        c.set_pixel(0, 0, RED)
        self.assertEqual(frame[0], BLACK)  # earlier snapshot untouched


class CanvasShapeTests(unittest.TestCase):
    def test_hline(self):
        c = Canvas()
        c.hline(2, 5, 3, GREEN)
        for x in (2, 3, 4):
            self.assertEqual(c.get_pixel(x, 5), GREEN)
        self.assertEqual(c.get_pixel(5, 5), BLACK)

    def test_vline(self):
        c = Canvas()
        c.vline(7, 1, 4, BLUE)
        for y in (1, 2, 3, 4):
            self.assertEqual(c.get_pixel(7, y), BLUE)
        self.assertEqual(c.get_pixel(7, 5), BLACK)

    def test_rect_outline(self):
        c = Canvas()
        c.rect(1, 1, 4, 3, RED, fill=False)
        # corners present, center hollow
        self.assertEqual(c.get_pixel(1, 1), RED)
        self.assertEqual(c.get_pixel(4, 3), RED)
        self.assertEqual(c.get_pixel(2, 2), BLACK)

    def test_rect_filled(self):
        c = Canvas()
        c.rect(0, 0, 3, 2, GREEN, fill=True)
        for y in (0, 1):
            for x in (0, 1, 2):
                self.assertEqual(c.get_pixel(x, y), GREEN)
        self.assertEqual(c.get_pixel(3, 0), BLACK)

    def test_zero_size_rect_noop(self):
        c = Canvas()
        c.rect(0, 0, 0, 5, RED)
        self.assertTrue(all(px == BLACK for px in c.to_frame()))


class CanvasBlitTests(unittest.TestCase):
    PALETTE = {"o": RED, "x": GREEN}

    def test_blit_sprite_respects_transparency(self):
        c = Canvas()
        rows = ["ox.", "..o"]
        c.blit_sprite(rows, self.PALETTE)
        self.assertEqual(c.get_pixel(0, 0), RED)    # 'o'
        self.assertEqual(c.get_pixel(1, 0), GREEN)  # 'x'
        self.assertEqual(c.get_pixel(2, 0), BLACK)  # '.' transparent
        self.assertEqual(c.get_pixel(2, 1), RED)    # 'o'

    def test_blit_sprite_offset(self):
        c = Canvas()
        c.blit_sprite(["o"], self.PALETTE, dx=5, dy=6)
        self.assertEqual(c.get_pixel(5, 6), RED)

    def test_blit_sprite_offscreen_is_clipped(self):
        c = Canvas()
        c.blit_sprite(["oo"], self.PALETTE, dx=-1)  # first 'o' off the left edge
        self.assertEqual(c.get_pixel(0, 0), RED)    # second 'o' lands at x=0
        # nothing raised; left-clipped pixel simply dropped

    def test_blit_frame_with_transparency(self):
        base = Canvas(RED)
        overlay = [GREEN] * PIXELS
        overlay[0] = BLACK  # make one pixel "transparent"
        base.blit_frame(overlay, transparent=BLACK)
        self.assertEqual(base.get_pixel(0, 0), RED)   # kept underlying red
        self.assertEqual(base.get_pixel(1, 0), GREEN)


if __name__ == "__main__":
    unittest.main()

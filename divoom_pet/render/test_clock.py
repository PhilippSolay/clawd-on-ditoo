"""Unit tests for the procedural clock face."""

import unittest

from divoom_pet.render.canvas import PIXELS
from divoom_pet.render.clock import clock_frame, clock_takeover
from divoom_pet.render.colors import COLORS


class ClockFrameTests(unittest.TestCase):
    def test_frame_is_256_and_has_color(self):
        frame = clock_frame(12, 34, color=COLORS["cyan"])
        self.assertEqual(len(frame), PIXELS)
        self.assertIn(COLORS["cyan"], frame)

    def test_separator_toggle_changes_pixels(self):
        self.assertNotEqual(
            clock_frame(9, 5, separator=True),
            clock_frame(9, 5, separator=False),
        )

    def test_zero_padding(self):
        # 01:05 must render without raising and stay on-canvas.
        self.assertEqual(len(clock_frame(1, 5)), PIXELS)


class ClockTakeoverTests(unittest.TestCase):
    def test_blinks_produce_frames(self):
        anim = clock_takeover(7, 42, blinks=3)
        self.assertEqual(len(anim), 6)  # on/off per blink
        for frame, ms in anim:
            self.assertEqual(len(frame), PIXELS)
            self.assertGreater(ms, 0)


if __name__ == "__main__":
    unittest.main()

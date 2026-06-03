"""Unit tests for the compositor, overlays, and banner takeover."""

import unittest

from divoom_pet.render.canvas import BLACK, PIXELS, WIDTH
from divoom_pet.render.colors import COLORS
from divoom_pet.render.compositor import (
    CountBadge,
    ProgressBar,
    banner,
    compose,
    compose_animation,
)
from divoom_pet.sprites import SPRITES, State, animation_for_state, sprite_to_rgb_frame

GREEN = COLORS["green"]
DIM = COLORS["dim"]


class ComposeBaseTests(unittest.TestCase):
    def test_compose_sprite_matches_legacy_flatten(self):
        # A bare sprite composed with no overlays must equal the old path.
        sprite = SPRITES["idle_open"]
        self.assertEqual(compose(sprite), sprite_to_rgb_frame(sprite))

    def test_compose_none_is_blank(self):
        self.assertEqual(compose(None), [BLACK] * PIXELS)

    def test_compose_accepts_raw_frame(self):
        frame = [COLORS["red"]] * PIXELS
        self.assertEqual(compose(frame), frame)

    def test_compose_accepts_char_rows(self):
        out = compose(["o" * WIDTH] + ["." * WIDTH] * 15)
        self.assertEqual(out[0], COLORS["orange"])  # 'o' -> clawd orange
        self.assertEqual(out[WIDTH], BLACK)          # second row transparent


class ProgressBarTests(unittest.TestCase):
    def test_full_bar_fills_row(self):
        frame = compose(None, [ProgressBar(value=1.0, row=15, fg=GREEN, track=DIM)])
        bottom = frame[15 * WIDTH:16 * WIDTH]
        self.assertTrue(all(px == GREEN for px in bottom))

    def test_empty_bar_is_track_only(self):
        frame = compose(None, [ProgressBar(value=0.0, row=15, fg=GREEN, track=DIM)])
        bottom = frame[15 * WIDTH:16 * WIDTH]
        self.assertTrue(all(px == DIM for px in bottom))

    def test_half_bar_fills_left_half(self):
        frame = compose(None, [ProgressBar(value=0.5, row=15, fg=GREEN, track=DIM)])
        bottom = frame[15 * WIDTH:16 * WIDTH]
        self.assertEqual(bottom[:8], [GREEN] * 8)
        self.assertEqual(bottom[8:], [DIM] * 8)

    def test_value_clamped(self):
        frame = compose(None, [ProgressBar(value=9.0, row=15, fg=GREEN, track=DIM)])
        bottom = frame[15 * WIDTH:16 * WIDTH]
        self.assertTrue(all(px == GREEN for px in bottom))

    def test_none_track_leaves_underlying_pixels(self):
        base = [COLORS["red"]] * PIXELS
        frame = compose(base, [ProgressBar(value=0.25, row=15, fg=GREEN, track=None)])
        bottom = frame[15 * WIDTH:16 * WIDTH]
        self.assertEqual(bottom[:4], [GREEN] * 4)
        self.assertEqual(bottom[4:], [COLORS["red"]] * 12)  # untouched base


class CountBadgeTests(unittest.TestCase):
    def test_badge_renders_some_colored_pixels(self):
        frame = compose(None, [CountBadge(count=3, color=COLORS["yellow"], backing=None)])
        self.assertIn(COLORS["yellow"], frame)

    def test_badge_overflow_caps_with_plus(self):
        b = CountBadge(count=999, max_digits=2)
        self.assertEqual(b._text(), "99+")

    def test_badge_corner_positions_differ(self):
        tl = compose(None, [CountBadge(count=8, corner="tl", backing=None)])
        br = compose(None, [CountBadge(count=8, corner="br", backing=None)])
        self.assertNotEqual(tl, br)

    def test_badge_backing_draws_box(self):
        frame = compose(None, [CountBadge(count=8, corner="tl",
                                          color=COLORS["yellow"], backing=COLORS["dim"])])
        self.assertIn(COLORS["dim"], frame)


class BannerTests(unittest.TestCase):
    def test_banner_returns_frames(self):
        frames = banner("PR", color=GREEN)
        self.assertTrue(len(frames) > WIDTH)  # scrolls across + tail
        for frame, ms in frames:
            self.assertEqual(len(frame), PIXELS)
            self.assertGreater(ms, 0)

    def test_banner_shows_text_somewhere_in_the_middle(self):
        frames = banner("8", color=GREEN, bg=BLACK)
        # Some mid frame should have the glyph color visible.
        self.assertTrue(any(GREEN in f for f, _ in frames))

    def test_empty_text_still_yields_a_frame(self):
        frames = banner("", color=GREEN)
        self.assertTrue(len(frames) >= 1)


class ComposeAnimationTests(unittest.TestCase):
    def test_overlays_applied_to_every_frame(self):
        anim = animation_for_state(State.THINKING)
        out = compose_animation(anim, [ProgressBar(value=1.0, fg=GREEN, track=DIM)])
        self.assertEqual(len(out), len(anim))
        for frame, ms in out:
            self.assertEqual(len(frame), PIXELS)
            self.assertGreater(ms, 0)
            self.assertTrue(all(px == GREEN for px in frame[15 * WIDTH:16 * WIDTH]))


if __name__ == "__main__":
    unittest.main()

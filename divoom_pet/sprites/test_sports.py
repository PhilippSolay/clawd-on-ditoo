"""Unit tests for Clawd's bored-idle workout scenes."""

import unittest

from divoom_pet.render.canvas import PIXELS
from divoom_pet.render.compositor import compose
from divoom_pet.sprites import State, animation_for_state
from divoom_pet.sprites.clawd import IdleOpts
from divoom_pet.sprites.sports import (
    SCENES,
    SPORT_ORDER,
    SPORT_SPRITES,
    quick_activity,
    random_sport,
)


class SportsSpriteTests(unittest.TestCase):
    def test_all_sprites_are_16x16(self):
        for name, sprite in SPORT_SPRITES.items():
            self.assertEqual(len(sprite.rows), 16, name)
            for row in sprite.rows:
                self.assertEqual(len(row), 16, f"{name}: {row!r}")

    def test_sprites_compose_to_full_frame(self):
        for sprite in SPORT_SPRITES.values():
            self.assertEqual(len(compose(sprite)), PIXELS)

    def test_no_stray_palette_chars(self):
        # A typo'd char renders as black and silently disappears; forbid unknowns.
        from divoom_pet.sprites.clawd import CLAWD_PALETTE
        for name, sprite in SPORT_SPRITES.items():
            for row in sprite.rows:
                for ch in row:
                    self.assertIn(ch, CLAWD_PALETTE, f"{name}: unknown char {ch!r}")


class SportsSceneTests(unittest.TestCase):
    def test_known_scene_names(self):
        self.assertEqual(
            set(SCENES),
            {"jumprope", "pushups", "weights", "jumpingjacks", "boxing",
             "meditate", "tea", "yoga"},
        )

    def test_order_matches_scenes(self):
        self.assertEqual(set(SPORT_ORDER), set(SCENES))

    def test_each_scene_has_valid_frames(self):
        for name, anim in SCENES.items():
            self.assertGreaterEqual(len(anim), 2, name)  # at least one full rep
            for sprite, ms in anim:
                self.assertGreater(ms, 0)

    def test_random_sport_returns_a_known_scene(self):
        for _ in range(25):
            self.assertIn(random_sport(), SCENES.values())

    def test_sporty_state_yields_a_sport_scene(self):
        # SPORTY dispatches to a random exercise; every frame must be a sport sprite.
        sport_frames = {id(s) for scene in SCENES.values() for s, _ in scene}
        anim = animation_for_state(State.SPORTY)
        self.assertGreaterEqual(len(anim), 2)
        for sprite, _ in anim:
            self.assertIn(id(sprite), sport_frames)


class QuickActivityTests(unittest.TestCase):
    def test_quick_activity_is_short_and_valid(self):
        sport_frames = {id(s) for scene in SCENES.values() for s, _ in scene}
        for _ in range(25):
            anim = quick_activity()
            total = sum(ms for _, ms in anim)
            self.assertGreater(total, 0)
            self.assertLess(total, 3500, "an idle peek should stay brief")
            for sprite, _ in anim:
                self.assertIn(id(sprite), sport_frames)


class IdleMixInTests(unittest.TestCase):
    """The standard idle loop should occasionally splice a special activity in —
    but only when fidgets are enabled, and never when frequency is 0."""

    def _sport_frame_ids(self):
        return {id(s) for scene in SCENES.values() for s, _ in scene}

    def test_specials_appear_in_some_idle_cycles(self):
        sport_frames = self._sport_frame_ids()
        opts = IdleOpts(fidgets=True, frequency=3.0, blink=True)  # crank it to force some
        mixed = 0
        for _ in range(120):
            anim = animation_for_state(State.IDLE, opts)
            if any(id(s) in sport_frames for s, _ in anim):
                mixed += 1
        self.assertGreater(mixed, 0, "a special never mixed into idle")

    def test_no_specials_when_fidgets_disabled(self):
        sport_frames = self._sport_frame_ids()
        opts = IdleOpts(fidgets=False, frequency=3.0, blink=True)
        for _ in range(120):
            anim = animation_for_state(State.IDLE, opts)
            self.assertFalse(any(id(s) in sport_frames for s, _ in anim),
                             "no special should appear when fidgets are off")


if __name__ == "__main__":
    unittest.main()

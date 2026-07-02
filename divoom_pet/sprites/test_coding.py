"""Unit tests for the crab-with-laptop coding scenes."""

import unittest

from divoom_pet.render.canvas import PIXELS
from divoom_pet.render.compositor import compose
from divoom_pet.sprites import State, animation_for_state
from divoom_pet.sprites.coding import CODING_SPRITES, SCENES


class CodingSpriteTests(unittest.TestCase):
    def test_all_sprites_are_16x16(self):
        for name, sprite in CODING_SPRITES.items():
            self.assertEqual(len(sprite.rows), 16, name)
            for row in sprite.rows:
                self.assertEqual(len(row), 16, f"{name}: {row!r}")

    def test_sprites_compose_to_full_frame(self):
        for sprite in CODING_SPRITES.values():
            self.assertEqual(len(compose(sprite)), PIXELS)


class SceneTests(unittest.TestCase):
    def test_each_scene_has_valid_frames(self):
        for name, anim in SCENES.items():
            self.assertGreaterEqual(len(anim), 1, name)
            for sprite, ms in anim:
                self.assertGreater(ms, 0)

    def test_known_scene_names(self):
        self.assertEqual(
            set(SCENES),
            {"crabtype", "crabtool", "laptop", "terminal", "compile", "tooling",
             "rubberduck", "whiteboard", "reading"},
        )

    def test_no_stray_palette_chars(self):
        # A typo'd char renders as black and silently vanishes; forbid unknowns.
        from divoom_pet.sprites.clawd import CLAWD_PALETTE
        for name, sprite in CODING_SPRITES.items():
            for row in sprite.rows:
                for ch in row:
                    self.assertIn(ch, CLAWD_PALETTE, f"{name}: unknown char {ch!r}")

    def test_tool_scene_shares_laptop_body_with_compile(self):
        # The legacy peeking scenes: rows 0-4 and 9-12 match so coding<->tool only
        # changes the screen icon (no jarring pose jump).
        from divoom_pet.sprites.coding import CODING_SPRITES
        compile_rows = CODING_SPRITES["compile_a"].rows
        tool_rows = CODING_SPRITES["laptop_tool_a"].rows
        for i in list(range(0, 5)) + list(range(9, 13)):
            self.assertEqual(tool_rows[i], compile_rows[i], f"row {i} differs")

    def test_crab_type_and_tool_share_body(self):
        # The default front-facing pair must share everything but the 2 screen rows
        # (9, 10), so coding<->tool only swaps code<->gear on the screen.
        from divoom_pet.sprites.coding import CODING_SPRITES
        type_rows = CODING_SPRITES["crab_type_a"].rows
        tool_rows = CODING_SPRITES["crab_tool_a"].rows
        for i in range(16):
            if i in (9, 10):
                self.assertNotEqual(tool_rows[i], type_rows[i], f"screen row {i} should differ")
            else:
                self.assertEqual(tool_rows[i], type_rows[i], f"body row {i} should match")

    def test_coding_leads_with_a_special_about_every_minute(self):
        # Time-based, not per-cycle odds: driving cycles every 5s of simulated time
        # over 5 minutes should surface a special ~once a minute, and each such cycle
        # must LEAD with the special (so it shows even if a tool call cuts in).
        from divoom_pet.sprites.coding import (
            DEFAULT_CODING_SCENE, WORK_SPECIALS, coding_loop, _reset_work_special_clock,
        )
        _reset_work_special_clock(None)
        coding_frames = {id(s) for s in CODING_SPRITES.values()}
        keyboard_first = id(SCENES[DEFAULT_CODING_SCENE][0][0])
        special_firsts = {id(SCENES[n][0][0]) for n in WORK_SPECIALS}
        special_times = []
        for t in range(0, 300, 5):                 # 5 min of working, a cycle every 5s
            anim = coding_loop(now=float(t))
            self.assertGreaterEqual(len(anim), 2)
            for sprite, ms in anim:
                self.assertGreater(ms, 0)
                self.assertIn(id(sprite), coding_frames)
            led = id(anim[0][0])
            self.assertIn(led, special_firsts | {keyboard_first})
            if led in special_firsts:
                special_times.append(t)
        # ~one per minute → 4-5 across five minutes, never back-to-back.
        self.assertGreaterEqual(len(special_times), 4)
        self.assertLessEqual(len(special_times), 5)
        for a, b in zip(special_times, special_times[1:]):
            self.assertGreaterEqual(b - a, 60, "specials fired more often than once a minute")

    def test_coding_is_keyboard_first_without_a_special_due(self):
        from divoom_pet.sprites.coding import DEFAULT_CODING_SCENE, coding_loop, _reset_work_special_clock
        _reset_work_special_clock(None)
        first = coding_loop(now=0.0)               # first cycle starts the clock — keyboard
        self.assertIs(first[0][0], SCENES[DEFAULT_CODING_SCENE][0][0])
        soon = coding_loop(now=10.0)               # 10s later, not due yet — still keyboard
        self.assertIs(soon[0][0], SCENES[DEFAULT_CODING_SCENE][0][0])

    def test_coding_loop_holds_a_pose(self):
        # A cycle should last a few seconds, not a single sub-second twitch.
        from divoom_pet.sprites.coding import coding_loop
        total_ms = sum(ms for _, ms in coding_loop())
        self.assertGreaterEqual(total_ms, 2000)


if __name__ == "__main__":
    unittest.main()

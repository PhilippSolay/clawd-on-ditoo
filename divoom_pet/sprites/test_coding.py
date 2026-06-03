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
        self.assertEqual(set(SCENES), {"laptop", "terminal", "compile", "tooling"})

    def test_tool_scene_shares_laptop_body_with_compile(self):
        # Rows 0-4 and 9-12 must match the compile scene exactly so coding<->tool
        # only changes the screen icon (no jarring pose jump).
        from divoom_pet.sprites.coding import CODING_SPRITES
        compile_rows = CODING_SPRITES["compile_a"].rows
        tool_rows = CODING_SPRITES["laptop_tool_a"].rows
        for i in list(range(0, 5)) + list(range(9, 13)):
            self.assertEqual(tool_rows[i], compile_rows[i], f"row {i} differs")

    def test_coding_state_returns_default_scene(self):
        from divoom_pet.sprites.coding import DEFAULT_CODING_SCENE
        self.assertEqual(animation_for_state(State.CODING), SCENES[DEFAULT_CODING_SCENE])


if __name__ == "__main__":
    unittest.main()

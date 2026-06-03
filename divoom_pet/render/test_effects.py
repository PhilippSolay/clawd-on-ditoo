"""Unit tests for the procedural effects kit."""

import unittest

from divoom_pet.render.canvas import PIXELS
from divoom_pet.render.effects import (
    EFFECTS,
    celebrate,
    confetti,
    fireworks,
    plasma,
    pulse,
    sparkle_over,
)
from divoom_pet.sprites import SPRITES


def _valid_anim(test, anim, expected_len=None):
    test.assertTrue(len(anim) >= 1)
    if expected_len is not None:
        test.assertEqual(len(anim), expected_len)
    for frame, ms in anim:
        test.assertEqual(len(frame), PIXELS)
        test.assertGreater(ms, 0)


class EffectShapeTests(unittest.TestCase):
    def test_confetti(self):
        _valid_anim(self, confetti(frames=10), 10)

    def test_fireworks(self):
        _valid_anim(self, fireworks(frames=10), 10)

    def test_plasma(self):
        _valid_anim(self, plasma(frames=4), 4)

    def test_pulse(self):
        _valid_anim(self, pulse(frames=8), 8)


class DeterminismTests(unittest.TestCase):
    def test_same_seed_same_output(self):
        self.assertEqual(confetti(frames=6, seed=1), confetti(frames=6, seed=1))

    def test_different_seed_differs(self):
        self.assertNotEqual(confetti(frames=6, seed=1), confetti(frames=6, seed=2))


class OverBaseTests(unittest.TestCase):
    def test_sparkle_over_sprite(self):
        _valid_anim(self, sparkle_over(SPRITES["happy_a"], frames=5, seed=3), 5)

    def test_celebrate_over_sprite(self):
        _valid_anim(self, celebrate(SPRITES["happy_a"], frames=8, seed=4), 8)


class RegistryTests(unittest.TestCase):
    def test_every_registered_effect_runs(self):
        for name, generator in EFFECTS.items():
            _valid_anim(self, generator())


if __name__ == "__main__":
    unittest.main()

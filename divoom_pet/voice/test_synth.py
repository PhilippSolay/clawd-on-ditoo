"""Unit tests for the richer synthesis primitives."""

import unittest

from divoom_pet.voice.sounds import SAMPLE_RATE
from divoom_pet.voice.synth import (
    additive,
    echo,
    fm,
    glide,
    lowpass,
    pack,
    render_gesture,
)


class OscillatorTests(unittest.TestCase):
    def test_additive_length_and_signal(self):
        s = additive(440, 0.05, [(1, 1.0), (2, 0.5)])
        self.assertEqual(len(s), int(SAMPLE_RATE * 0.05))
        self.assertTrue(any(abs(x) > 0.01 for x in s))

    def test_zero_freq_is_silence(self):
        self.assertTrue(all(x == 0.0 for x in additive(0, 0.02, [(1, 1.0)])))
        self.assertTrue(all(x == 0.0 for x in glide(0, 100, 0.02)))

    def test_fm_and_glide_length(self):
        self.assertEqual(len(fm(330, 0.04)), int(SAMPLE_RATE * 0.04))
        self.assertEqual(len(glide(400, 200, 0.04)), int(SAMPLE_RATE * 0.04))


class EffectTests(unittest.TestCase):
    def test_lowpass_preserves_length_and_bounds(self):
        s = [1.0, -1.0] * 100
        out = lowpass(s, 0.3)
        self.assertEqual(len(out), len(s))
        self.assertTrue(all(-1.0 <= x <= 1.0 for x in out))

    def test_echo_extends_buffer(self):
        out = echo([0.5] * 100, delay_s=0.001, decay=0.5, repeats=2)
        self.assertGreater(len(out), 100)


class PackTests(unittest.TestCase):
    def test_two_bytes_per_sample(self):
        self.assertEqual(len(pack([0.0, 0.5, -0.5])), 6)

    def test_clamps_without_error(self):
        self.assertEqual(len(pack([10.0, -10.0])), 4)


class GestureTests(unittest.TestCase):
    def _voice(self, f, d):
        return additive(f, d, [(1, 1.0)])

    def test_concatenates_notes(self):
        s = render_gesture([("C5", 0.02), ("E5", 0.02)], self._voice)
        self.assertEqual(len(s), 2 * int(SAMPLE_RATE * 0.02))

    def test_rest_is_silence(self):
        s = render_gesture([("R", 0.02)], self._voice)
        self.assertTrue(all(x == 0.0 for x in s))


if __name__ == "__main__":
    unittest.main()

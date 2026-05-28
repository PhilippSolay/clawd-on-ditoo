"""Unit tests for the Clawd config schema."""

import json
import tempfile
import unittest
from pathlib import Path

from divoom_pet.config import Config


class DefaultsTests(unittest.TestCase):
    def test_defaults_are_sane(self):
        c = Config()
        self.assertTrue(c.sounds.enabled)
        self.assertEqual(c.animations.brightness, 70)
        self.assertEqual(c.sleep.idle_to_sleep_seconds, 240.0)
        self.assertEqual(c.device.channel, 2)

    def test_round_trip_dict(self):
        c = Config()
        self.assertEqual(Config.from_dict(c.to_dict()), c)


class FromDictToleranceTests(unittest.TestCase):
    def test_unknown_keys_ignored(self):
        c = Config.from_dict({"sounds": {"volume": 0.3, "bogus": 1}, "nope": {}})
        self.assertEqual(c.sounds.volume, 0.3)

    def test_partial_sections_fall_back_to_defaults(self):
        c = Config.from_dict({"mic": {"enabled": False}})
        self.assertFalse(c.mic.enabled)
        self.assertEqual(c.mic.clap_floor, 0.06)  # default preserved
        self.assertTrue(c.sounds.enabled)         # untouched section default

    def test_empty_and_none(self):
        self.assertEqual(Config.from_dict({}), Config())
        self.assertEqual(Config.from_dict(None), Config())


class NormalizationTests(unittest.TestCase):
    def test_volume_clamped(self):
        self.assertEqual(Config.from_dict({"sounds": {"volume": 5}}).sounds.volume, 1.0)
        self.assertEqual(Config.from_dict({"sounds": {"volume": -1}}).sounds.volume, 0.0)

    def test_brightness_clamped_and_int(self):
        c = Config.from_dict({"animations": {"brightness": 999}})
        self.assertEqual(c.animations.brightness, 100)
        self.assertIsInstance(c.animations.brightness, int)

    def test_sleep_floor(self):
        self.assertEqual(Config.from_dict({"sleep": {"idle_to_sleep_seconds": 1}}).sleep.idle_to_sleep_seconds, 10.0)

    def test_fidget_frequency_clamped(self):
        self.assertEqual(Config.from_dict({"animations": {"fidget_frequency": 99}}).animations.fidget_frequency, 3.0)


class MergeTests(unittest.TestCase):
    def test_merge_is_immutable_and_deep(self):
        base = Config()
        new = base.merged({"sounds": {"volume": 0.2}})
        self.assertEqual(new.sounds.volume, 0.2)
        self.assertEqual(base.sounds.volume, 0.6)         # original untouched
        self.assertEqual(new.sounds.audio_device, "DitooPro")  # sibling key preserved

    def test_merge_multiple_sections(self):
        new = Config().merged({"mic": {"clap_rise": 6.0}, "sleep": {"idle_to_sleep_seconds": 60}})
        self.assertEqual(new.mic.clap_rise, 6.0)
        self.assertEqual(new.sleep.idle_to_sleep_seconds, 60.0)

    def test_merge_clamps(self):
        self.assertEqual(Config().merged({"sounds": {"volume": 9}}).sounds.volume, 1.0)


class PersistenceTests(unittest.TestCase):
    def test_save_load_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config.json"
            c = Config().merged({"animations": {"brightness": 42}})
            c.save(p)
            self.assertEqual(Config.load(p), c)

    def test_missing_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(Config.load(Path(d) / "nope.json"), Config())

    def test_corrupt_file_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config.json"
            p.write_text("{ not json ]")
            self.assertEqual(Config.load(p), Config())


if __name__ == "__main__":
    unittest.main()

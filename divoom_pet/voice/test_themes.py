"""Unit tests for the sound theme registry."""

import unittest

from divoom_pet.voice.themes import BUILTIN_THEMES, GESTURES, get_theme

EVENTS = set(GESTURES)  # wake/think/tool/done/error/sleep/poke


class ThemeRegistryTests(unittest.TestCase):
    def test_builtins_present(self):
        for name in ("marimba", "music_box", "bubbly", "chip"):
            self.assertIn(name, BUILTIN_THEMES)

    def test_each_theme_covers_events_plus_keepalive(self):
        for name in BUILTIN_THEMES:
            theme = get_theme(name)
            self.assertTrue(EVENTS.issubset(set(theme)), name)
            self.assertIn("keepalive", theme)

    def test_generators_produce_int16_pcm(self):
        for name in ("marimba", "music_box", "bubbly"):
            theme = get_theme(name)
            for event in EVENTS:
                pcm = theme[event][0]()
                self.assertGreater(len(pcm), 0, f"{name}/{event}")
                self.assertEqual(len(pcm) % 2, 0, f"{name}/{event} not 16-bit aligned")

    def test_unknown_theme_falls_back(self):
        self.assertIn("wake", get_theme("does-not-exist"))


if __name__ == "__main__":
    unittest.main()

"""Unit tests for the live-voice layer (phrase slug, render args, cache/gating).

The actual macOS `say` call is monkeypatched out, so these run anywhere.
"""

import tempfile
import unittest
from pathlib import Path

import divoom_pet.voice.sounds as snd
from divoom_pet.voice.sounds import VOCAB, SoundPlayer, _phrase_slug


class PhraseSlugTests(unittest.TestCase):
    def test_normalizes_whitespace_and_case(self):
        self.assertEqual(_phrase_slug("Hello   There"), _phrase_slug("hello there"))

    def test_stable_and_prefixed(self):
        self.assertEqual(_phrase_slug("merged"), _phrase_slug("merged"))
        self.assertTrue(_phrase_slug("x").startswith("saylive_"))

    def test_vocab_phrases_have_distinct_slugs(self):
        slugs = {_phrase_slug(p) for p in VOCAB}
        self.assertEqual(len(slugs), len(VOCAB))


class RenderSayTests(unittest.TestCase):
    def test_builds_say_command_and_reports_success(self):
        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            Path(args[args.index("-o") + 1]).write_bytes(b"RIFF")  # simulate say writing a file
            return None

        orig = snd.subprocess.run
        snd.subprocess.run = fake_run
        try:
            with tempfile.TemporaryDirectory() as d:
                ok = snd.render_say_to_wav("hello", Path(d) / "out.wav", voice="Zoe")
            self.assertTrue(ok)
            self.assertIn("-v", calls[0])
            self.assertIn("Zoe", calls[0])
            self.assertIn("hello", calls[0])
        finally:
            snd.subprocess.run = orig


class SayCacheTests(unittest.TestCase):
    def _player(self, enabled=True, spoken_lines=True):
        sp = SoundPlayer.__new__(SoundPlayer)  # skip the heavy __init__
        sp.enabled = enabled
        sp.spoken_lines = spoken_lines
        sp.tts_voice = None
        sp._played = []
        sp._play_file = lambda p: sp._played.append(p)
        return sp

    def test_say_is_noop_when_disabled(self):
        sp = self._player(spoken_lines=False)
        sp.say("anything")
        self.assertEqual(sp._played, [])

    def test_cached_phrase_plays_without_rendering(self):
        sp = self._player()
        with tempfile.TemporaryDirectory() as d:
            orig_dir, orig_render = snd.SOUNDS_DIR, snd.render_say_to_wav
            snd.SOUNDS_DIR = Path(d)
            rendered = []
            snd.render_say_to_wav = lambda *a, **k: rendered.append(a)
            try:
                cached = Path(d) / f"{_phrase_slug('warm one')}.wav"
                cached.write_bytes(b"RIFF")
                sp._say_blocking("warm one")
            finally:
                snd.SOUNDS_DIR, snd.render_say_to_wav = orig_dir, orig_render
        self.assertEqual(sp._played, [cached])
        self.assertEqual(rendered, [])  # warm hit: no render

    def test_novel_phrase_renders_then_plays(self):
        sp = self._player()
        with tempfile.TemporaryDirectory() as d:
            orig_dir, orig_render = snd.SOUNDS_DIR, snd.render_say_to_wav
            snd.SOUNDS_DIR = Path(d)

            def fake_render(text, path, voice=None, **k):
                Path(path).write_bytes(b"RIFF")
                return True

            snd.render_say_to_wav = fake_render
            try:
                sp._say_blocking("a brand new phrase")
            finally:
                snd.SOUNDS_DIR, snd.render_say_to_wav = orig_dir, orig_render
        self.assertEqual(len(sp._played), 1)


if __name__ == "__main__":
    unittest.main()

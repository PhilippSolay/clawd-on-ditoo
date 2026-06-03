"""Unit tests for the PNG/GIF asset pipeline."""

import tempfile
import unittest
from pathlib import Path

from divoom_pet.render.assets import (
    AssetLibrary,
    build_assets,
    image_to_frames,
    load_manifest,
    save_manifest,
)
from divoom_pet.render.canvas import PIXELS

RED = (255, 0, 0)
GREEN = (0, 255, 0)


class ManifestRoundTripTests(unittest.TestCase):
    def test_save_load_round_trip(self):
        frames = [([RED] * PIXELS, 100), ([GREEN] * PIXELS, 120)]
        with tempfile.TemporaryDirectory() as d:
            path = save_manifest("clip", frames, out_dir=d)
            name, loaded, loop = load_manifest(path)
            self.assertEqual(name, "clip")
            self.assertEqual(loaded, frames)  # exact pixel + duration fidelity
            self.assertTrue(loop)


class AssetLibraryTests(unittest.TestCase):
    def test_loads_named_anims_sorted(self):
        frames = [([RED] * PIXELS, 100)]
        with tempfile.TemporaryDirectory() as d:
            save_manifest("b", frames, out_dir=d)
            save_manifest("a", frames, out_dir=d)
            lib = AssetLibrary.from_dir(d)
            self.assertEqual(lib.names(), ["a", "b"])
            self.assertEqual(lib.get("a"), frames)
            self.assertIsNone(lib.get("missing"))

    def test_missing_dir_is_empty(self):
        self.assertEqual(AssetLibrary.from_dir("/no/such/dir/xyz").names(), [])

    def test_load_manifest_drops_wrong_size_frames(self):
        import json
        good = [1, 2, 3] * PIXELS   # 256 px
        bad = [9, 9, 9] * 10        # 10 px — corrupt/truncated
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.json"
            p.write_text(json.dumps({
                "name": "x", "loop": True,
                "frames": [{"ms": 100, "px": good}, {"ms": 100, "px": bad}],
            }))
            _name, frames, _loop = load_manifest(p)
            self.assertEqual(len(frames), 1)              # the 10-px frame is dropped
            self.assertEqual(len(frames[0][0]), PIXELS)

    def test_corrupt_manifest_skipped(self):
        frames = [([GREEN] * PIXELS, 100)]
        with tempfile.TemporaryDirectory() as d:
            save_manifest("good", frames, out_dir=d)
            (Path(d) / "bad.json").write_text("{ not json")
            lib = AssetLibrary.from_dir(d)
            self.assertEqual(lib.names(), ["good"])  # bad one ignored, not fatal


class ImageConversionTests(unittest.TestCase):
    def _skip_without_pil(self):
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("PIL not installed")

    def test_static_image_becomes_one_16x16_frame(self):
        self._skip_without_pil()
        from PIL import Image

        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "x.png"
            Image.new("RGB", (32, 32), (10, 20, 30)).save(src)
            frames = image_to_frames(src)
            self.assertEqual(len(frames), 1)
            self.assertEqual(len(frames[0][0]), PIXELS)

    def test_build_assets_round_trips_through_library(self):
        self._skip_without_pil()
        from PIL import Image

        with tempfile.TemporaryDirectory() as d:
            srcdir = Path(d) / "assets"
            srcdir.mkdir()
            outdir = Path(d) / "out"
            Image.new("RGB", (16, 16), (1, 2, 3)).save(srcdir / "foo.png")
            written = build_assets(srcdir, outdir)
            self.assertEqual(len(written), 1)
            self.assertIn("foo", AssetLibrary.from_dir(outdir).names())


if __name__ == "__main__":
    unittest.main()

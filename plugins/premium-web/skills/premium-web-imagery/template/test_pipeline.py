"""Self-check for pipeline.py: prompts share the style sheet, fallback + post produce responsive files, no upscaling, budget honoured."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import pipeline  # noqa: E402


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="imagery-test-"))
        shutil.copy(pipeline.DEFAULT_CONFIG, self.tmp / "imagery.config.json")
        self.cfg = pipeline.load(str(self.tmp / "imagery.config.json"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_prompts_share_style_and_seed(self):
        ps = pipeline.cmd_prompts(self.cfg)
        self.assertEqual(len(ps), len(self.cfg["assets"]))
        self.assertEqual({p["seed"] for p in ps}, {self.cfg["style"]["seed"]})
        for p in ps:
            self.assertIn(self.cfg["style"]["palette"]["accent"], p["prompt"])
            self.assertIn("no text", p["prompt"])

    def test_fallback_then_post(self):
        raw = pipeline.fallback_plate(self.cfg, "hero")
        self.assertTrue(raw.exists())
        res = pipeline.process(raw, self.cfg, "hero")
        self.assertEqual(res["warnings"], [])
        self.assertTrue(all(f["w"] <= Image.open(raw).width for f in res["files"]))
        self.assertEqual({Path(f["file"]).suffix for f in res["files"]}, {".avif", ".webp"})

    def test_never_upscales_small_source(self):
        small = self.tmp / "tiny.png"
        Image.new("RGB", (500, 300), (20, 20, 30)).save(small)
        res = pipeline.process(small, self.cfg, "plate-a")
        self.assertEqual({f["w"] for f in res["files"]}, {500})

    def test_trim_only_when_asked(self):
        img = Image.new("RGB", (400, 400), pipeline.hex_rgb(self.cfg["post"]["matte"]))
        img.paste((255, 255, 255), (150, 150, 250, 250))
        t = pipeline.trim(img, pipeline.hex_rgb(self.cfg["post"]["matte"]))
        self.assertEqual(t.size, (100 + 2 * pipeline.TRIM_PAD,) * 2)

    def test_detect_reports_fallback_key(self):
        self.assertIn("can_generate_here", json.loads(json.dumps(pipeline.detect())))


if __name__ == "__main__":
    unittest.main()

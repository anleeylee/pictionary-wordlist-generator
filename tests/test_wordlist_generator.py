# -*- coding: utf-8 -*-
"""Tests for the Pictionary Wordlist Generator."""

import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wordlist_generator import (  # noqa: E402
    BRAND_BLACKLIST,
    SENSITIVE_BLACKLIST,
    build_library,
    grade_difficulty,
)


class TestGrading(unittest.TestCase):
    def test_easy_short_concrete(self):
        self.assertEqual(grade_difficulty("Cat"), "easy")
        self.assertEqual(grade_difficulty("Moon"), "easy")
        self.assertEqual(grade_difficulty("Pizza"), "easy")

    def test_medium_phrase(self):
        self.assertEqual(grade_difficulty("Flying Saucer"), "medium")
        self.assertEqual(grade_difficulty("Solar Eclipse"), "medium")

    def test_hard_idiom(self):
        self.assertEqual(grade_difficulty("Butterfly Effect"), "hard")
        self.assertEqual(grade_difficulty("Cognitive Dissonance"), "hard")


class TestPipeline(unittest.TestCase):
    def _seed(self):
        return {
            "theme": "space",
            "title": "Space",
            "categories": {
                "Nature": ["Moon", "Sun", "Star", "Comet", "Galaxy"],
                "Objects": ["Rocket", "Satellite", "Telescope", "Lunar Rover"],
                "People": ["Astronaut", "Cosmonaut"],
            },
        }

    def test_build_library_shape(self):
        lib = build_library(self._seed())
        self.assertEqual(lib["theme"], "space")
        self.assertEqual(lib["counts"]["total"], 11)
        for e in lib["entries"]:
            self.assertIn("prompt", e)
            self.assertIn("category", e)
            self.assertIn("difficulty", e)

    def test_compliance_filter(self):
        seed = self._seed()
        seed["categories"]["Objects"].append("Frisbee")  # brand -> filtered
        seed["categories"]["People"].append("Beer Bottle")  # sensitive -> filtered
        lib = build_library(seed)
        prompts = {e["prompt"] for e in lib["entries"]}
        self.assertNotIn("Frisbee", prompts)
        self.assertNotIn("Beer Bottle", prompts)
        self.assertEqual(lib["counts"]["total"], 11)

    def test_dedup_case_insensitive(self):
        seed = self._seed()
        seed["categories"]["Nature"].append("moon")  # duplicate of Moon
        lib = build_library(seed)
        prompts = [e["prompt"] for e in lib["entries"]]
        self.assertEqual(prompts.count("Moon"), 1)
        self.assertEqual(lib["counts"]["total"], 11)

    def test_category_balance(self):
        seed = self._seed()
        seed["categories"]["Nature"] = ["Moon"] * 50 + ["Sun", "Star"]
        lib = build_library(seed, max_per_category=3)
        from collections import Counter

        counts = Counter(e["category"] for e in lib["entries"])
        self.assertLessEqual(counts["Nature"], 3)

    def test_blacklists_are_lowercase(self):
        for word in BRAND_BLACKLIST | SENSITIVE_BLACKLIST:
            self.assertEqual(word, word.lower())


class TestCliOutput(TestPipeline):
    def test_generate_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed = Path(tmp) / "seed.json"
            out = Path(tmp) / "words" / "space.json"
            seed.write_text(json.dumps(self._seed()), encoding="utf-8")
            from wordlist_generator import main

            rc = main(["--seed", str(seed), "--out", str(out)])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["theme"], "space")
            self.assertGreater(data["counts"]["total"], 0)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pictionary Wordlist Generator
=============================

Batch-generate themed Pictionary word libraries as JSON.

A theme is described by a seed file (JSON) that maps category names to lists
of seed prompts. This tool:

  1. reads the seed file,
  2. optionally expands prompts from built-in templates,
  3. applies compliance filters (brand names, sensitive words),
  4. grades every prompt into easy / medium / hard,
  5. balances categories so no single category dominates,
  6. de-duplicates inside the library,
  7. writes `words/<slug>.json` plus a console report.

Output schema
-------------
{
  "theme": "space",
  "title": "Space",
  "entries": [
    {"prompt": "Moon", "category": "Nature", "difficulty": "easy"},
    ...
  ],
  "generated_at": "2026-10-12T05:10:00",
  "counts": {"easy": 40, "medium": 30, "hard": 30, "total": 100}
}

The resulting libraries are designed to feed a party-game word generator
such as the Pictionary Word Generator at https://pictionarywordgenerators.com/
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Compliance blacklists (small, illustrative sets; extend for production use)
# ---------------------------------------------------------------------------

# Words that name third-party brands/products rather than a drawable thing.
BRAND_BLACKLIST = {
    "nike", "adidas", "coca-cola", "pepsi", "mcdonald", "burger king",
    "kfc", "starbucks", "google", "apple iphone", "iphone", "ipad",
    "windows", "playstation", "xbox", "nintendo", "lego", "barbie",
    "harry potter", "star wars", "frisbee", "velcro", "band-aid",
    "kleenex", "xerox", "trampoline brand", "monopoly", "uno",
}

# Words that are inappropriate for family / kids libraries.
SENSITIVE_BLACKLIST = {
    "cigarette", "cigarette pack", "beer bottle", "wine bottle",
    "whiskey", "vodka", "marijuana", "syringe", "needle", "pistol",
    "rifle", "knife fight", "blood", "skull and crossbones", "bomb",
    "grenade", "suicide", "kill", "murder", "drugs", "heroin",
    "cocaine", "gambling", "casino", "strip club", "cigars",
}

# ---------------------------------------------------------------------------
# Difficulty heuristics
# ---------------------------------------------------------------------------

# Prompts a very young player recognises immediately. Used to pull a word
# down to "easy" even when its spelling is long.
EASY_SET = {
    "cat", "dog", "fish", "bird", "sun", "moon", "star", "tree",
    "flower", "rain", "snow", "apple", "banana", "cake", "pizza",
    "house", "chair", "table", "book", "hat", "shoe", "ball", "car",
    "boat", "plane", "train", "bus", "duck", "cow", "pig", "sheep",
    "rabbit", "frog", "bee", "ant", "spider", "mouse", "lion", "tiger",
    "bear", "elephant", "monkey", "giraffe", "zebra", "horse",
}

# Two-gram signals that usually mark a phrase (→ medium) or an idiom (→ hard).
IDIOM_MARKERS = [
    "cognitive", "existential", "paradox", "phenomenon", "syndrome",
    "dilemma", "metaphor", "allegory", "butterfly effect", "social",
    "political", "philosophical", "psychological",
]


def grade_difficulty(prompt: str) -> str:
    """Heuristic easy / medium / hard grade.

    Rules:
      - single word in EASY_SET            -> easy
      - short concrete word (<= 6 chars)   -> easy
      - phrase without idiom markers       -> medium
      - long prompt / idiom markers        -> hard
    """
    text = prompt.strip().lower()
    words = text.split()
    if text in EASY_SET:
        return "easy"
    if len(words) == 1 and len(text) <= 6:
        return "easy"
    lowered = text
    if any(marker in lowered for marker in IDIOM_MARKERS):
        return "hard"
    if len(text) > 22 or len(words) >= 5:
        return "hard"
    return "medium"


def normalize(prompt: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for comparisons."""
    return re.sub(r"\s+", " ", prompt.strip().lower())


# ---------------------------------------------------------------------------
# Template expansion (optional)
# ---------------------------------------------------------------------------

PREFIXES = ["mini", "giant", "flying", "crystal", "electric", "golden",
            "underwater", "steam", "laser", "cosmic"]
SUFFIXES = ["bot", "ship", "station", "cannon", "suit", "lab", "engine",
            "bridge", "dome", "creature"]


def expand_templates(seeds, max_extra=0):
    """Optionally create derived prompts from templates.

    With max_extra=0 (default) no expansion happens — the library is exactly
    the curated seed list, which keeps quality high.
    """
    if max_extra <= 0:
        return seeds
    extra = []
    for cat, words in seeds.items():
        base = [w for w in words if len(w.split()) == 1]
        for w in base:
            extra.append((f"{PREFIXES[hash(w) % len(PREFIXES)]} {w.title()}", cat))
            extra.append((f"{w.title()} {SUFFIXES[hash(w) % len(SUFFIXES)]}", cat))
        if len(extra) >= max_extra:
            break
    return extra


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def build_library(seed_data: dict, max_per_category: int = 100,
                  min_per_category: int = 20, expand: int = 0) -> dict:
    theme = seed_data["theme"]
    title = seed_data.get("title", theme.replace("-", " ").title())
    categories = seed_data["categories"]  # {category: [prompts]}

    entries = []
    seen = set()

    def add(prompt: str, category: str):
        key = normalize(prompt)
        if not prompt or not prompt.strip():
            return
        if key in seen:
            return
        if key in BRAND_BLACKLIST or key in SENSITIVE_BLACKLIST:
            return
        seen.add(key)
        entries.append({
            "prompt": prompt.strip(),
            "category": category,
            "difficulty": grade_difficulty(prompt),
        })

    for cat, prompts in categories.items():
        for p in prompts:
            add(p, cat)

    if expand > 0:
        for p, cat in expand_templates(categories, max_extra=expand):
            add(p, cat)

    # Category balancing: enforce a maximum per category, fill order preserved.
    counts = Counter(e["category"] for e in entries)
    balanced = []
    for e in entries:
        if counts[e["category"]] > max_per_category:
            counts[e["category"]] -= 1
            continue
        balanced.append(e)
    entries = balanced

    # Final safety: if a category fell below the floor, report it (do not invent words).
    final_counts = Counter(e["category"] for e in entries)
    low = {c: n for c, n in final_counts.items() if n < min_per_category}

    return {
        "theme": theme,
        "title": title,
        "entries": entries,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "counts": {
            "easy": sum(1 for e in entries if e["difficulty"] == "easy"),
            "medium": sum(1 for e in entries if e["difficulty"] == "medium"),
            "hard": sum(1 for e in entries if e["difficulty"] == "hard"),
            "total": len(entries),
        },
        "warnings": {
            "low_categories": low,
            "filtered": len(seed_data.get("_filtered_hits", [])),
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="wordlist_generator",
        description="Batch-generate themed Pictionary word libraries (JSON).")
    parser.add_argument("--seed", required=True,
                        help="Path to a seed JSON file (theme + categories).")
    parser.add_argument("--out", required=True,
                        help="Output path for the generated word library JSON.")
    parser.add_argument("--max-per-category", type=int, default=100,
                        help="Cap on entries per category (default 100).")
    parser.add_argument("--expand", type=int, default=0,
                        help="Optional template expansion count (0 = curated only).")
    args = parser.parse_args(argv)

    seed_path = Path(args.seed)
    try:
        seed_data = json.loads(seed_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report and exit
        print(f"error: cannot read seed file {seed_path}: {exc}", file=sys.stderr)
        return 1

    library = build_library(seed_data,
                            max_per_category=args.max_per_category,
                            expand=args.expand)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(library, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    c = library["counts"]
    print(f"theme      : {library['theme']}")
    print(f"total      : {c['total']}  (easy {c['easy']} / medium {c['medium']} / hard {c['hard']})")
    print(f"categories : {len(library['entries'])} entries across "
          f"{len({e['category'] for e in library['entries']})} categories")
    if library["warnings"]["low_categories"]:
        print(f"warning    : categories under floor -> "
              f"{library['warnings']['low_categories']}")
    print(f"written    : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

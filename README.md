# Pictionary Wordlist Generator

> **Batch-generate themed Pictionary word libraries (JSON) — difficulty grading, category balancing and compliance filtering for party-game word lists.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![CLI](https://img.shields.io/badge/CLI-ready-4B8BBE)](wordlist_generator.py)
[![No dependencies](https://img.shields.io/badge/deps-stdlib%20only-blueviolet)](requirements.txt)

---

## Links

- 🎲 **Try the live tool:** [Pictionary Word Generator — 7,000+ free drawing prompts](https://pictionarywordgenerators.com/)
- Read the Chinese version: [README.zh-CN.md](README.zh-CN.md)

---

## What it does

A themed Pictionary word library is a JSON file that feeds a party-game word
generator. Each library groups drawable prompts by category (Animals, Food,
Places, Abstract …) and difficulty (easy / medium / hard).

**This tool turns a small curated seed list into a complete, balanced,
compliance-checked word library in one command** — so you can ship a new
theme (Space, Kitchen, Sports, Holidays …) in minutes instead of hand-editing
thousands of rows.

It is built to produce libraries for online drawing-game generators such as
the [Pictionary Word Generator](https://pictionarywordgenerators.com/), where
every prompt must be drawable, family-safe and fairly balanced across
categories.

## The problem it solves

Curating word lists by hand is slow and inconsistent:

- One person writes **200 prompts**, another writes **2,000** — the difficulty
  mix drifts and players stall on obscure entries.
- Category counts skew: one theme quietly becomes 80% "Animals", so rounds on
  "All categories" feel repetitive.
- Brand names and inappropriate words sneak into family libraries and have to
  be swept out later (a "brand-name sweep" across 9 libraries is exactly the
  kind of cleanup a generator with compliance filters prevents at the source).

## Features

- **Seed → library in one command**: define a theme with a small JSON seed
  file (category → prompts) and get a complete library back.
- **Difficulty grading** (`easy` / `medium` / `hard`) by a documented
  heuristic: short concrete words and a built-in easy set → *easy*; plain
  phrases → *medium*; idioms and long prompts → *hard*.
- **Category balancing**: a configurable per-category cap (default 100) so no
  single category dominates a round.
- **Compliance filtering**: built-in brand-name and sensitive-word blacklists
  (extendable) keep libraries family-safe and free of third-party trademarks.
- **De-duplication**: case-insensitive, whitespace-normalised duplicates are
  removed inside a library.
- **No third-party dependencies**: pure Python standard library.
- **Reproducible output**: `generated_at` timestamp, counts and warnings ship
  with every library, so numbers on a site are always auditable.

## Install

```bash
# clone the repo
git clone https://github.com/anleeylee/pictionary-wordlist-generator.git
cd pictionary-wordlist-generator

# no pip install needed — standard library only
python wordlist_generator.py --help
```

## Usage

```bash
# generate the Space library from the bundled seed file
python wordlist_generator.py \
  --seed seeds/space.json \
  --out words/space.json
```

You can tighten or relax balancing per theme:

```bash
# cap every category at 40 entries
python wordlist_generator.py --seed seeds/space.json --out words/space.json \
  --max-per-category 40
```

Optional template expansion (off by default — curated seeds stay high quality):

```bash
python wordlist_generator.py --seed seeds/space.json --out words/space.json \
  --expand 20
```

### Seed file format

```json
{
  "theme": "space",
  "title": "Space",
  "categories": {
    "Nature": ["Moon", "Sun", "Star", "Comet"],
    "Objects": ["Rocket", "Satellite", "Telescope"]
  }
}
```

### Output file format

```json
{
  "theme": "space",
  "title": "Space",
  "entries": [
    {"prompt": "Moon", "category": "Nature", "difficulty": "easy"},
    {"prompt": "Solar Eclipse", "category": "Nature", "difficulty": "medium"}
  ],
  "generated_at": "2026-10-12T05:10:00+00:00",
  "counts": {"easy": 40, "medium": 30, "hard": 30, "total": 100},
  "warnings": {"low_categories": {}, "filtered": 0}
}
```

## How grading works

| Signal | Grade |
|---|---|
| Word in the built-in easy set (`cat`, `moon`, `pizza` …) | easy |
| Single word ≤ 6 characters | easy |
| Plain phrase (no idiom markers) | medium |
| Idiom marker (`cognitive`, `existential`, `butterfly effect` …) | hard |
| More than 22 characters / 5+ words | hard |

Grades are heuristics, not guarantees — the seed author stays the editor of
record. The tool never invents words to fill a category: if a category falls
below the floor it is reported in `warnings`, not silently padded.

## Why not just paste a giant static list?

Because the library is the *source of truth* for a site's word counts, and
published counts get audited. When every library ships with a reproducible
generation path, a change log, and a JSON schema, the numbers "7,958 entries",
"6,964 distinct prompts" and "24 libraries" become checkable facts instead of
marketing claims. This tool exists to make that pipeline repeatable.

## Tests

```bash
python -m unittest discover -s tests -v
```

Covers: difficulty grading, brand/sensitive filtering, de-duplication,
category balancing and end-to-end CLI JSON output.

## License

MIT — use it, extend it, and keep the attribution. The generated word
libraries are your content; the tool just makes them reproducible.

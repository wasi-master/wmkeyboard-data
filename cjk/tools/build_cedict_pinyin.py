#!/usr/bin/env python3
"""
Convert CC-CEDICT into a TSV file for WMKeyboard's ConversionDictionary format:
    reading <TAB> word <TAB> freq

Where:
  - reading: toneless Pinyin of the whole entry with syllables concatenated
    (lowercase ASCII, no spaces, no tone marks/digits, no apostrophes).
  - word: Simplified Hanzi character or word/phrase.
  - freq: integer frequency (higher = commoner).

Usage:
  python3 tools/dictionaries/build_cedict_pinyin.py [--cedict PATH] [--out PATH]
"""

import argparse
import gzip
import os
import re
import sys
import urllib.request
from pathlib import Path

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"

# Hanzi character regex (Unified Ideographs + Extension A + Extension B)
HANZI_RE = re.compile(r"^[\u4e00-\u9fff\u3400-\u4dbf\ud840-\ud869\uded6-\udf00]+$")

# Tone marks to plain ascii map
TONE_MAP = str.maketrans(
    "āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛ",
    "aaaaeeeeiiiioooouuuuvvvvaaaaeeeeiiiioooouuuuvvvv"
)


def clean_pinyin(raw_py: str) -> str:
    """Converts CC-CEDICT pinyin bracket content to toneless ASCII concatenated pinyin."""
    s = raw_py.lower()
    s = s.replace("u:", "v").replace("ü", "v").replace("ü", "v")
    s = s.translate(TONE_MAP)
    s = re.sub(r"[0-9]", "", s)
    s = re.sub(r"[^a-z]", "", s)
    return s


def load_seed_frequencies(seed_path: Path) -> dict:
    """Loads frequency seeds from existing dictionary if present."""
    seed_freq = {}
    if not seed_path.exists():
        return seed_freq
    with open(seed_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                w = parts[1].strip()
                try:
                    f_val = int(parts[2].strip())
                    seed_freq[w] = max(seed_freq.get(w, 0), f_val)
                except ValueError:
                    pass
    return seed_freq


def fetch_or_load_cedict(cedict_path: Path = None) -> str:
    """Loads CC-CEDICT text from local file or downloads from official MDBG URL."""
    if cedict_path and cedict_path.exists():
        print(f"Reading CC-CEDICT from local file: {cedict_path}")
        if str(cedict_path).endswith(".gz"):
            with gzip.open(cedict_path, "rt", encoding="utf-8") as f:
                return f.read()
        else:
            return cedict_path.read_text(encoding="utf-8")

    print(f"Downloading CC-CEDICT from {CEDICT_URL}...")
    req = urllib.request.Request(CEDICT_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return gzip.decompress(resp.read()).decode("utf-8")


def convert_cedict(content: str, seed_freq: dict) -> list:
    """Parses CC-CEDICT entries into (reading, word, freq) tuples."""
    lines = content.splitlines()
    total_lines = len(lines)
    entry_map = {}  # (reading, word) -> freq

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        m = re.match(r"^(\S+)\s+(\S+)\s+\[(.*?)\]\s+/(.*)/$", line)
        if not m:
            continue

        trad, simp, py, defs = m.groups()
        reading = clean_pinyin(py)

        if not reading or not HANZI_RE.match(simp):
            continue

        if simp in seed_freq:
            freq = seed_freq[simp]
        else:
            w_len = len(simp)
            if w_len == 1:
                base = 80
            elif w_len == 2:
                base = 60
            elif w_len == 3:
                base = 40
            elif w_len == 4:
                base = 25
            else:
                base = 10

            decay = int((idx / total_lines) * 30)
            freq = max(1, base - decay)

        key = (reading, simp)
        if key not in entry_map or freq > entry_map[key]:
            entry_map[key] = freq

    # Sort entries by reading, then freq descending, then word
    sorted_entries = sorted(
        entry_map.items(),
        key=lambda x: (x[0][0], -x[1], x[0][1])
    )
    return [(r, w, f) for (r, w), f in sorted_entries]


def main():
    parser = argparse.ArgumentParser(description="Convert CC-CEDICT to ConversionDictionary TSV format.")
    parser.add_argument("--cedict", type=Path, help="Path to local cedict_1_0_ts_utf-8_mdbg.txt.gz or .txt file")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("app/src/main/assets/dictionaries/pinyin.tsv"),
        help="Target output TSV path (default: app/src/main/assets/dictionaries/pinyin.tsv)",
    )
    args = parser.parse_args()

    seed_freq = load_seed_frequencies(args.out)
    content = fetch_or_load_cedict(args.cedict)
    entries = convert_cedict(content, seed_freq)

    out_lines = [
        "# CC-CEDICT Chinese-English Dictionary (CC BY-SA 4.0)",
        "# Format: reading\tword\tfreq",
    ]
    out_lines.extend(f"{r}\t{w}\t{f}" for r, w, f in entries)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"Successfully wrote {len(entries)} entries to {args.out}")


if __name__ == "__main__":
    main()

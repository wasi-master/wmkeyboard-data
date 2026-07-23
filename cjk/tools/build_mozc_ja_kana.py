#!/usr/bin/env python3
"""
Convert Google Mozc open-source dictionary into a TSV file for WMKeyboard's ConversionDictionary format:
    reading <TAB> word <TAB> freq

Where:
  - reading: HIRAGANA reading (no spaces, Katakana converted to Hiragana).
  - word: Kanji / Kana surface form.
  - freq: integer frequency (higher = commoner, derived from Mozc cost).

Usage:
  python3 tools/dictionaries/build_mozc_ja_kana.py [--out PATH]
"""

import argparse
import concurrent.futures
import hashlib
import os
import re
import sys
import urllib.request
from pathlib import Path

MOZC_BASE_URL = "https://raw.githubusercontent.com/google/mozc/master/src/data/dictionary_oss"
HIRAGANA_RE = re.compile(r"^[\u3041-\u309fー]+$")


def kata_to_hira(text: str) -> str:
    """Converts Katakana characters in text to Hiragana."""
    res = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            res.append(chr(code - 0x60))
        else:
            res.append(ch)
    return "".join(res)


def fetch_file(index: int) -> str:
    url = f"{MOZC_BASE_URL}/dictionary0{index}.txt"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="Convert Mozc dictionary to ConversionDictionary TSV format.")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("app/src/main/assets/dictionaries/ja_kana.tsv"),
        help="Target output TSV path (default: app/src/main/assets/dictionaries/ja_kana.tsv)",
    )
    args = parser.parse_args()

    print("Downloading Mozc dictionary files (00..09)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        file_contents = list(executor.map(fetch_file, range(10)))

    entry_map = {}  # (reading, word) -> freq

    for content in file_contents:
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 5:
                continue

            raw_reading, lid, rid, cost_str, word = parts[0], parts[1], parts[2], parts[3], parts[4]
            try:
                cost = int(cost_str)
            except ValueError:
                continue

            reading = kata_to_hira(raw_reading).replace(" ", "").replace("　", "")
            word = word.strip()

            if not reading or not HIRAGANA_RE.match(reading) or not word:
                continue

            freq = max(1, 30000 - cost)
            key = (reading, word)
            if key not in entry_map or freq > entry_map[key]:
                entry_map[key] = freq

    # Sort entries by reading, then freq descending, then word
    sorted_entries = sorted(
        entry_map.items(),
        key=lambda x: (x[0][0], -x[1], x[0][1])
    )

    out_lines = [
        "# Mozc Japanese Dictionary (BSD 3-Clause / OSS)",
        "# Format: reading\tword\tfreq",
    ]
    out_lines.extend(f"{r}\t{w}\t{f}" for (r, w), f in sorted_entries)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_data = "\n".join(out_lines) + "\n"
    out_bytes = out_data.encode("utf-8")
    args.out.write_bytes(out_bytes)

    byte_size = len(out_bytes)
    sha256_hex = hashlib.sha256(out_bytes).hexdigest()

    print(f"Successfully wrote {len(sorted_entries)} entries to {args.out}")
    print(f"File Byte Size: {byte_size} bytes")
    print(f"SHA-256 Hex: {sha256_hex}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
build_jyutping_dict.py — Convert rime-cantonese & CC-Canto into WMKeyboard's Jyutping dictionary TSV.

Format:
  reading<TAB>word<TAB>freq

where:
  reading = TONELESS Jyutping, lowercase a-z only (tone digits 1-6 stripped, concatenated with NO separator)
  word    = Traditional Han characters
  freq    = integer frequency (higher = more common)

Output:
  cjk/jyutping.tsv
"""

import argparse
import hashlib
import io
import os
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

# Data Sources
RIME_URLS = [
    ("chars", "https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.chars.dict.yaml"),
    ("words", "https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.words.dict.yaml"),
    ("lettered", "https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.lettered.dict.yaml"),
]

CANTO_URL = "https://cantonese.org/cccanto-170202.zip"

SCRIPT_DIR = Path(__file__).resolve().parent
CJK_DIR = SCRIPT_DIR.parent
DEFAULT_OUT = CJK_DIR / "jyutping.tsv"
DEFAULT_SYLLABLES = CJK_DIR / "jyutping_syllables.txt"


def clean_reading(raw_jp: str):
    """Strips tone digits 1-6 and converts to concatenated toneless ASCII lowercase."""
    if not raw_jp:
        return None, None
    syls = [re.sub(r"[1-6]", "", s.lower()).strip() for s in raw_jp.split()]
    if not syls or not all(s.isalpha() and s.isascii() for s in syls):
        return None, None
    return "".join(syls), syls


def load_syllable_inventory(syllables_path: Path) -> set:
    """Loads toneless Jyutping syllable inventory."""
    if not syllables_path.exists():
        # Fallback path in app repo if needed
        alt_path = Path("/Users/wasimaster/Work/WMKeyboard/app/src/main/assets/dictionaries/jyutping_syllables.txt")
        if alt_path.exists():
            syllables_path = alt_path
        else:
            raise FileNotFoundError(f"Syllable inventory file not found: {syllables_path}")

    print(f"Loading syllable inventory from {syllables_path}...")
    syllables = set()
    with open(syllables_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()
            if line and not line.startswith("#"):
                syllables.add(line)
    return syllables


def segment_greedy(reading: str, syl_set: set) -> bool:
    """Greedily splits reading longest-first against valid syllable set."""
    idx = 0
    n = len(reading)
    while idx < n:
        match_len = 0
        for l in range(min(6, n - idx), 0, -1):
            if reading[idx : idx + l] in syl_set:
                match_len = l
                break
        if match_len == 0:
            return False
        idx += match_len
    return True


def fetch_rime_data():
    """Fetches rime-cantonese dictionary YAML files."""
    data = {}
    for name, url in RIME_URLS:
        print(f"Fetching rime-cantonese {name} from {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "WMKeyboard-DictBuilder/1.0"})
        with urllib.request.urlopen(req) as resp:
            data[name] = resp.read().decode("utf-8")
    return data


def fetch_cccanto_data():
    """Fetches CC-Canto text file from zip distribution."""
    print(f"Fetching CC-Canto from {CANTO_URL}...")
    req = urllib.request.Request(CANTO_URL, headers={"User-Agent": "WMKeyboard-DictBuilder/1.0"})
    with urllib.request.urlopen(req) as resp:
        zf = zipfile.ZipFile(io.BytesIO(resp.read()))
        return zf.read("cccanto-webdist.txt").decode("utf-8")


def parse_and_build(rime_data: dict, canto_text: str):
    """Parses source data into unique (reading, word) entries with frequencies."""
    entry_map = {}

    # Process rime-cantonese entries
    for name in ["chars", "words", "lettered"]:
        text = rime_data.get(name, "")
        lines = text.splitlines()
        total_l = len(lines)
        in_header = True

        for idx, line in enumerate(lines):
            line = line.strip()
            if line == "...":
                in_header = False
                continue
            if in_header or not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) >= 2:
                word = parts[0].strip()
                raw_jp = parts[1].strip()
                wt_str = parts[2].strip() if len(parts) >= 3 else ""

                reading, syls = clean_reading(raw_jp)
                if not reading or not word:
                    continue

                w_len = len(word)
                if w_len == 1:
                    base = 100
                elif w_len == 2:
                    base = 80
                elif w_len == 3:
                    base = 60
                elif w_len == 4:
                    base = 40
                else:
                    base = 20

                wt_val = 0
                if wt_str.endswith("%"):
                    try:
                        wt_val = int(wt_str[:-1])
                    except ValueError:
                        pass
                elif wt_str.isdigit():
                    wt_val = int(wt_str)

                decay = int((idx / max(1, total_l)) * 30)
                freq = max(1, base + wt_val - decay)

                key = (reading, word)
                if key not in entry_map or freq > entry_map[key]:
                    entry_map[key] = freq

    # Process CC-Canto entries
    lines_c = canto_text.splitlines()
    total_lc = len(lines_c)
    for idx, line in enumerate(lines_c):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        m = re.match(r"^(\S+)\s+(\S+)\s+\[.*?\]\s+\{(.*?)\}", line)
        if m:
            trad, simp, raw_jp = m.groups()
            reading, syls = clean_reading(raw_jp)
            if not reading or not trad:
                continue

            w_len = len(trad)
            if w_len == 1:
                base = 90
            elif w_len == 2:
                base = 75
            elif w_len == 3:
                base = 55
            elif w_len == 4:
                base = 35
            else:
                base = 15

            decay = int((idx / max(1, total_lc)) * 25)
            freq = max(1, base - decay)

            key = (reading, trad)
            if key not in entry_map or freq > entry_map[key]:
                entry_map[key] = freq

    # Sort entries by reading, then frequency descending, then word
    sorted_items = sorted(
        entry_map.items(),
        key=lambda x: (x[0][0], -x[1], x[0][1])
    )
    return [(r, w, f) for (r, w), f in sorted_items]


def main():
    parser = argparse.ArgumentParser(description="Build Cantonese Jyutping dictionary TSV for WMKeyboard.")
    parser.add_argument("--syllables", type=Path, default=DEFAULT_SYLLABLES, help="Path to jyutping_syllables.txt")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output TSV file path")
    args = parser.parse_args()

    syllables = load_syllable_inventory(args.syllables)
    rime_data = fetch_rime_data()
    canto_text = fetch_cccanto_data()

    print("Parsing and processing entries...")
    entries = parse_and_build(rime_data, canto_text)

    # Cross-check greedy segmentation against jyutping_syllables.txt
    print("Performing greedy segmentation cross-check...")
    unsegmentable_readings = set()
    unsegmentable_details = []

    for reading, word, freq in entries:
        if not segment_greedy(reading, syllables):
            unsegmentable_readings.add(reading)
            unsegmentable_details.append((reading, word))

    failed_list = sorted(unsegmentable_readings)

    if failed_list:
        print(f"\n[FAIL LOUDLY / CROSS-CHECK REPORT] {len(failed_list)} readings failed greedy segmentation against syllable inventory:")
        for r in failed_list:
            matching_words = [w for rd, w in unsegmentable_details if rd == r]
            print(f"  - {r} (words: {', '.join(matching_words[:5])})")
    else:
        print("\nAll readings passed greedy segmentation cross-check!")

    # Write output file
    out_path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    header = [
        "# Cantonese Jyutping Dictionary (rime-cantonese CC BY 4.0 / CC-Canto CC BY-SA 3.0)",
        "# Format: reading\tword\tfreq",
    ]

    print(f"\nWriting {len(entries)} rows to {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n")
        for r, w, f_val in entries:
            f.write(f"{r}\t{w}\t{f_val}\n")

    # Statistics
    distinct_readings = len(set(r for r, w, f_val in entries))
    file_size = out_path.stat().st_size

    hasher = hashlib.sha256()
    with open(out_path, "rb") as f:
        hasher.update(f.read())
    sha256_hex = hasher.hexdigest()

    print("\n================ REPORT WHEN DONE ================")
    print(f"Total rows: {len(entries)}")
    print(f"Distinct readings: {distinct_readings}")
    print(f"Failed segmentation readings count: {len(failed_list)}")
    print(f"Output File: {out_path}")
    print(f"Size: {file_size} bytes")
    print(f"SHA-256: {sha256_hex}")
    print("==================================================")


if __name__ == "__main__":
    main()

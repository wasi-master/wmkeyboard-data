#!/usr/bin/env python3
"""
Generate ml_rom.txt.gz transliterated wordlist for Malayalam using ml2en.
Reads data/ml/ml_full.txt.gz, transliterates words to Roman script,
combines frequencies for duplicate transliterated words, and saves
the output to data/ml/ml_rom.txt.gz.
"""

import gzip
import re
import sys
from pathlib import Path
from collections import defaultdict

# Ensure ml2en is installed and monkey-patch Python 3 regex bug if present
try:
    import ml2en
except ImportError:
    print("ml2en module not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ml2en"])
    import ml2en

# Fix ml2en python backreference bug in site-packages if needed
ml2en_file = getattr(ml2en, "__file__", None)
if ml2en_file:
    ml2en_py = Path(ml2en_file).parent / "ml2en.py"
    if ml2en_py.exists():
        with open(ml2en_py, "r", encoding="utf-8") as f:
            content = f.read()
        if "v + '\\1'" in content or "v + '\\x01'" in content:
            content_fixed = content.replace("v + '\\1'", "v + r'\\1'").replace("v + '\\x01'", "v + r'\\1'")
            with open(ml2en_py, "w", encoding="utf-8") as f:
                f.write(content_fixed)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INPUT_FILE = DATA_DIR / "ml" / "ml_full.txt.gz"
OUTPUT_FILE = DATA_DIR / "ml" / "ml_rom.txt.gz"

def main():
    print(f"Reading input file: {INPUT_FILE}")
    if not INPUT_FILE.exists():
        print(f"Error: Input file {INPUT_FILE} does not exist.")
        sys.exit(1)

    converter = ml2en.ml2en()
    freq_map = defaultdict(int)
    total_input_words = 0
    skipped_words = 0

    with gzip.open(INPUT_FILE, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                word, freq_str = parts
                try:
                    freq = int(float(freq_str))
                except ValueError:
                    freq = 1
            else:
                word = parts[0]
                freq = 1

            total_input_words += 1

            # Transliterate to Roman script
            rom = converter.transliterate(word).lower().strip()

            # Filter out empty or non-alphabetic/symbol-only artifacts
            # Keep words with valid latin characters
            rom = re.sub(r"[^\w'-]", "", rom)
            if not rom or not any(c.isalpha() for c in rom):
                skipped_words += 1
                continue

            freq_map[rom] += freq

    # Sort results by frequency descending, then word ascending
    sorted_entries = sorted(freq_map.items(), key=lambda item: (-item[1], item[0]))

    print(f"Total input Malayalam words: {total_input_words}")
    print(f"Skipped invalid/empty words: {skipped_words}")
    print(f"Unique transliterated Roman words: {len(sorted_entries)}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT_FILE, "wt", encoding="utf-8") as f:
        for word, freq in sorted_entries:
            f.write(f"{word} {freq}\n")

    print(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

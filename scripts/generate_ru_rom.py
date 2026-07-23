#!/usr/bin/env python3
"""
Generate russian_rom.txt.gz transliterated wordlist for Russian.
Reads data/ru/ru_full.txt.gz, transliterates words to Roman script,
combines frequencies for duplicate transliterated words, and saves
the output to data/ru/russian_rom.txt.gz.
"""

import gzip
import re
import sys
from pathlib import Path
from collections import defaultdict

MAPPING = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
}

def transliterate(text):
    return "".join(MAPPING.get(c, c) for c in text)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INPUT_FILE = DATA_DIR / "ru" / "ru_full.txt.gz"
OUTPUT_FILE = DATA_DIR / "ru" / "russian_rom.txt.gz"

def main():
    print(f"Reading input file: {INPUT_FILE}")
    if not INPUT_FILE.exists():
        print(f"Error: Input file {INPUT_FILE} does not exist.")
        sys.exit(1)

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

            rom = transliterate(word).lower().strip()
            rom = re.sub(r"[^\w'-]", "", rom)
            if not rom or not any(c.isalpha() for c in rom):
                skipped_words += 1
                continue

            freq_map[rom] += freq

    sorted_entries = sorted(freq_map.items(), key=lambda item: (-item[1], item[0]))

    print(f"Total input Russian words: {total_input_words}")
    print(f"Skipped invalid/empty words: {skipped_words}")
    print(f"Unique transliterated Roman words: {len(sorted_entries)}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT_FILE, "wt", encoding="utf-8") as f:
        for word, freq in sorted_entries:
            f.write(f"{word} {freq}\n")

    print(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

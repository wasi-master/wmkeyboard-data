#!/usr/bin/env python3

"""Build cjk/ja_glide_counts.tsv: how often each kana reading is written, for
the keyboard's Kana JIS swipe (WM Keyboard #958, its KanaGlide).

    reading<TAB>count, most common first, 20,000 rows

A swipe over the kana board decodes into a reading, weighted by how common
the reading is. The conversion table (cjk/ja_kana.tsv) has no counts, only
30000 minus Mozc's word cost, and the cost of a reading on its own is a poor
guide: the table's top rows are inflection pieces whose real cost lives in
Mozc's connection matrix. This list counts readings in running text instead.
Each word of data/ja/ja_full.txt.gz (MeCab-segmented, counted) is read as
itself when it is kana (katakana folded to hiragana) and through
cjk/furigana/ja_furigana.tsv (a word's commonest reading) when it holds
kanji, and a reading's count is the sum over its words. Only readings the
conversion table holds at the score KanaGlide keeps (24000 and up, two kana
or more) are listed, so every row can be swiped.

    python3 -I scripts/build_ja_glide_counts.py
"""

import gzip
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROWS = 20_000
FLOOR = 24_000


def is_reading(text):
    return all("ぁ" <= c <= "ゖ" or c == "ー" for c in text)


def hiragana(text):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in text)


def main():
    readings = set()
    with open(ROOT / "cjk" / "ja_kana.tsv", encoding="utf-8") as table:
        for line in table:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3 or not parts[2].isdigit():
                continue
            reading, score = parts[0], int(parts[2])
            if score >= FLOOR and len(reading) >= 2 and is_reading(reading):
                readings.add(reading)
    furigana = {}
    with open(ROOT / "cjk" / "furigana" / "ja_furigana.tsv", encoding="utf-8") as table:
        for line in table:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                furigana[parts[0]] = parts[1]
    counts = defaultdict(int)
    with gzip.open(ROOT / "data" / "ja" / "ja_full.txt.gz", "rt", encoding="utf-8") as words:
        for line in words:
            parts = line.split()
            if len(parts) != 2 or not parts[1].isdigit():
                continue
            word, count = parts[0], int(parts[1])
            reading = hiragana(word)
            if not is_reading(reading):
                reading = furigana.get(word)
            if reading in readings:
                counts[reading] += count
    rows = sorted(counts.items(), key=lambda row: (-row[1], row[0]))[:ROWS]
    out = ROOT / "cjk" / "ja_glide_counts.tsv"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for reading, count in rows:
            f.write(f"{reading}\t{count}\n")
    print(f"{len(readings)} swipeable readings, {len(counts)} counted, {len(rows)} written to {out}")


if __name__ == "__main__":
    main()

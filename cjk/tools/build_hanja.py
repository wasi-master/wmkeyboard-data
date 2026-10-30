#!/usr/bin/env python3
"""Builds hanja.tsv (reading<TAB>word<TAB>freq) from libhangul's data/hanja/hanja.txt.

    build_hanja.py <hanja.txt> <hanja.tsv>

The source is sorted commonest first within a reading and carries no counts the
app can read, so the frequency is the row's rank under its reading. Readings that
are not whole Hangul syllables (ㄱ자집) and rows with no Han character are left out.
"""
import sys


def has_han(word):
    return any(0x3400 <= ord(c) <= 0x9FFF or 0xF900 <= ord(c) <= 0xFAFF or ord(c) > 0xFFFF for c in word)


seen = {}
with open(sys.argv[1], encoding="utf-8") as src, open(sys.argv[2], "w", encoding="utf-8", newline="\n") as out:
    for line in src:
        if line.startswith("#") or not line.strip():
            continue
        parts = line.rstrip("\n").split(":")
        if len(parts) < 2:
            continue
        reading, word = parts[0], parts[1]
        if not reading or not all(0xAC00 <= ord(c) <= 0xD7A3 for c in reading) or not has_han(word):
            continue
        rank = seen.get(reading, 0)
        seen[reading] = rank + 1
        out.write(f"{reading}\t{word}\t{max(1, 1000 - rank)}\n")

#!/usr/bin/env python3
"""de_aosp_v2: AOSP's German list with the words of spoken German lifted.

AOSP counted written text, so `ich` and `du` sit at 139 next to `mit` at 198: a
hundred times rarer, in a language where people type them all day. A stroke for
`mir` lost to `mit`, `wir` to `wie` (issue #1051 of wmkeyboard). The counted list
(data/de/de_full.txt.gz, from subtitles) has the opposite lean, so neither alone:

  - a word the counted list holds at least 20,000 times and 16 times over AOSP's
    figure goes to the geometric mean of the two;
  - a lower-case word AOSP lacks at 5,000 or more goes in at a quarter of its
    count (`verstehst`), unless it is English, under three letters, offensive or
    subtitle OCR.

Measured on FUTO's 2,588 German strokes (Wikipedia sentences, so the kind of text
AOSP was counted on): 80.49 % -> 80.37 %, top-1. Lifting to the counted figure
outright cost 80.49 % -> 79.79 %, and strokes for `die` started reading `dir`.

Usage: build_de_aosp_v2.py <en word list, the app's app/dictionaries-src/en.txt>
"""
import gzip
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data" / "de"
TOP_LOG2 = 28.0  # AospScores in the app
STEPS = 8.59
NOISE = {"lhr", "lhre", "lhn", "lhm", "lhnen", "äh", "ähm", "nen", "ner", "nem"}


def count(f):
    return 2 ** (TOP_LOG2 + (f - 255) / STEPS)


def score(n):
    return max(0, min(255, round(255 + STEPS * (math.log2(n) - TOP_LOG2))))


def main():
    header, aosp = [], {}
    for line in gzip.open(ROOT / "de_aosp.txt.gz", "rt", encoding="utf-8"):
        if line.startswith("#"):
            header.append(line)
        elif line.strip():
            word, f = line.split()
            aosp[word] = int(f)
    counted = {}
    for line in gzip.open(ROOT / "de_full.txt.gz", "rt", encoding="utf-8"):
        parts = line.split()
        if len(parts) == 2 and not line.startswith("#"):
            counted[parts[0]] = int(parts[1])
    offensive = {
        line.strip().lower()
        for line in gzip.open(ROOT / "de_offensive.txt.gz", "rt", encoding="utf-8")
    }
    english = {
        line.split()[0].lower()
        for line in open(sys.argv[1], encoding="utf-8")
        if line.strip()
    }
    written = {word.lower(): word for word in aosp}
    out = dict(aosp)
    lifted = added = 0
    for word, n in counted.items():
        own = written.get(word)
        if own is not None:
            if n >= 20_000 and n > 16 * count(aosp[own]):
                out[own] = max(aosp[own], score(math.sqrt(count(aosp[own]) * n)))
                lifted += 1
        elif (
            n >= 5_000 and len(word) >= 3 and word.isalpha() and word == word.lower()
            and word not in english and word not in offensive and word not in NOISE
        ):
            out[word] = score(n / 4)
            added += 1
    target = ROOT / "de_aosp_v2.txt.gz"
    with gzip.GzipFile(target, "wb", mtime=0) as raw:
        for line in header:
            raw.write(line.encode())
        raw.write(b"# Spoken German lifted from de_full (FrequencyWords, MIT): scripts/build_de_aosp_v2.py\n")
        for word, f in sorted(out.items(), key=lambda kv: (-kv[1], kv[0])):
            raw.write(f"{word} {f}\n".encode())
    print(f"{len(out)} words, {lifted} lifted, {added} added, {target.stat().st_size} bytes")


main()

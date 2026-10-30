#!/usr/bin/env python3
"""Merge the Dakshina dataset into the romanized word lists.

    python scripts/merge_dakshina_rom.py DAKSHINA_DIR [LANG ...]

DAKSHINA_DIR is an unpacked dakshina_dataset_v1.0 (only its lexicons/ and
romanized/ folders are read):
https://storage.googleapis.com/gresearch/dakshina/dakshina_dataset_v1.0.tar

Reads data/<lang>/<lang>_rom.txt.gz and writes data/<lang>/<lang>_rom_v2.txt.gz.
The old file stays, for the app versions that fetch it.

Dakshina has two things the Aksharantar lists lack. Its lexicons are the
romanizations native speakers wrote for words sampled from Wikipedia, and its
romanized folder is running text, which is the only real usage count any of
these lists has: Aksharantar's training half leaves out hai, nahi and kya,
and its counts are the number of native spellings a word has, so its top words
are foreign names (encephalitis 40, constantine 36).

A word's count is its old count + WEIGHT * (lexicon attestations + running-text
occurrences). A word only the running text has must occur MIN_RUNNING times,
since one annotator's one-off is as likely a slip as a spelling. Single letters
come from the lexicon only: in running text they are mostly initials.

Equal counts put Dakshina's words first, so a download's word cap cuts the
words nobody attested before the ones somebody did.
"""

import collections
import gzip
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# The languages this repo has a romanized list for. Dakshina's twelfth, Sindhi,
# has none.
LANGUAGES = "bn gu hi kn ml mr pa si ta te ur".split()

WEIGHT = 3
MIN_RUNNING = 2

# Words this script would add and shouldn't: Wikipedia has them, a keyboard's
# suggestions don't need them. Only words a list already had stay. The offensive
# lists can't do this: they hold bahut, are and bangladesh.
REFUSED = {
    "bn": {"bhoda", "mchod-tern", "porn", "porno", "pornografy", "pornographi", "pornographir",
           "pornography", "pornographyr", "sex", "voda"},
    "hi": {"randi"},
}

TOKEN = re.compile(r"[a-z]+(?:['-][a-z]+)*")


def read_list(path):
    counts = {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            word, count = line.rsplit(" ", 1)
            counts[word] = int(count)
    return counts


def read_lexicon(root, lang):
    """Romanization -> attestations."""
    attested = collections.Counter()
    for split in ("train", "dev", "test"):
        path = root / lang / "lexicons" / f"{lang}.translit.sampled.{split}.tsv"
        with open(path, encoding="utf-8") as f:
            for line in f:
                fields = line.rstrip("\n").split("\t")
                if len(fields) != 3 or not fields[1]:
                    continue
                latin = fields[1].lower()
                if TOKEN.fullmatch(latin):
                    attested[latin] += int(fields[2])
    return attested


def read_running(root, lang, keep=lambda line_number: True):
    """Lowercased word counts over the romanized sentences."""
    running = collections.Counter()
    path = root / lang / "romanized" / f"{lang}.romanized.rejoined.tsv"
    with open(path, encoding="utf-8") as f:
        for number, line in enumerate(f):
            fields = line.rstrip("\n").split("\t")
            if len(fields) >= 2 and keep(number):
                running.update(TOKEN.findall(fields[1].lower()))
    return running


def merge(old, attested, running, refused=frozenset(), weight=WEIGHT, min_running=MIN_RUNNING):
    """(word, count) rows in file order: count down, attested first, then the word."""
    merged = dict(old)
    dakshina = set()
    for word in attested.keys() | running.keys():
        if word in refused and word not in old:
            continue
        if word not in attested and (len(word) == 1 or running[word] < min_running):
            continue
        merged[word] = merged.get(word, 0) + weight * (attested[word] + running[word])
        dakshina.add(word)
    return sorted(merged.items(), key=lambda row: (-row[1], row[0] not in dakshina, row[0]))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root = Path(sys.argv[1])
    for lang in sys.argv[2:] or LANGUAGES:
        old = read_list(DATA / lang / f"{lang}_rom.txt.gz")
        rows = merge(old, read_lexicon(root, lang), read_running(root, lang), REFUSED.get(lang, frozenset()))
        out = DATA / lang / f"{lang}_rom_v2.txt.gz"
        with open(out, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as f:
            f.write("".join(f"{word} {count}\n" for word, count in rows).encode("utf-8"))
        print(f"{lang}: {len(old):,} -> {len(rows):,} words, {out.stat().st_size:,} bytes, top {[w for w, _ in rows[:8]]}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build the Canadian and Australian English word lists, data/en/en_ca_aosp.txt.gz
and data/en/en_au_aosp.txt.gz, in the same `word frequency` form and 0..255
scale as the AOSP lists scripts/import_aosp.py writes.

AOSP LatinIME itself ships only en_US and en_GB, so each list starts from the
nearest one there is and is respelled with the English Speller Database
(ESDB, the successor of SCOWL, https://github.com/en-wl/wordlist):

- en_CA: AOSP's en_US list (Apache-2.0, Copyright (C) The Android Open Source
  Project), respelled from American (ESDB spelling `A`) to Canadian (`C`).
- en_AU: LineageOS LatinIME's en_AU list (Apache-2.0; LineageOS made it from
  AOSP's en_GB in 2015, adding ute, mozzie and G'day and zeroing slurs),
  respelled from British (`B`) to Australian (`D`).

Respelling keeps the source's frequencies, which is the point: ESDB says
which spelling a region uses but carries no frequencies of its own. A word
that is the source region's spelling and one the target region does not use
(ESDB variant level 4 or above there) is replaced, inflections included, by
the target region's own spelling, at the replaced word's frequency (`center`
-> `centre`, `centered` -> `centred`). A word that is regional in one sense
only (`check`, which is `cheque` in banking) stays, and the regional spelling
is added only where another AOSP list (en_GB for Canada, en_US for
Australia) has a frequency for it. Names, words ESDB does not know, and
respellings no AOSP English list has are left as they are.

Changes from the sources, as Apache-2.0 section 4(b) asks them to be stated:
the respelling above, plus everything scripts/import_aosp.py does
(not_a_word records and shortcuts dropped, re-sorted by frequency).

ESDB's notice (Copyright 2000-2026 by Kevin Atkinson; Australian spellings
Copyright 2016 by Benjamin Titze) is in NOTICE. Only spelling codes are read
from it, not its larger word lists, so its UKACD terms do not apply.

Usage:
    git clone --depth 1 -b v2 https://github.com/en-wl/wordlist.git esdb
    (cd esdb && make scowl.db)
    python3 scripts/import_aosp_regional_en.py esdb/scowl.db
"""

import gzip
import sqlite3
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_aosp  # noqa: E402

DATA_DIR = import_aosp.DATA_DIR
LINEAGE_AU = ("https://github.com/LineageOS/android_packages_inputmethods_LatinIME/"
              "raw/lineage-21.0/dictionaries/en_AU_wordlist.combined.gz")

# ESDB variant levels 0 (non-variant) and 1 (equal, included by default) are
# the spellings a region's default speller accepts. A word is replaced only
# from level 4 (a common variant there) up, or with no level for the region:
# levels 2 and 3 are spellings the region uses about as much (`learned` and
# `learnt`, `among` and `amongst`), which are not the list's to choose.
PREFERRED = 1
REPLACE_FROM = 4

# ESDB groups a few forms that are grammar, not spelling: Australian `got` for
# `gotten` (or `sawn` for `sawed`) would take every `gotten` away rather than
# respell it. `sher` is a name and a word part, not a misspelt `shoer`.
KEEP = {"gotten", "sawed", "strived", "sher"}


def lineage_au() -> bytes:
    with urllib.request.urlopen(LINEAGE_AU, timeout=60) as resp:
        return resp.read()


class Spellings:
    """ESDB's variant level of each word, per sense (group and part of speech) and region."""

    def __init__(self, db: Path):
        con = sqlite3.connect(db)
        # (group, pos) -> word -> spelling code -> level. `_` marks a sense with
        # no regional spellings at all, which every region uses alike.
        self.senses: dict[tuple[int, str], dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
        self.keys: dict[str, set[tuple[int, str]]] = defaultdict(set)
        for g, pos, word, spelling, level in con.execute(
            "select group_id, pos, word, spelling, variant_level from words_w_variant_info"
        ):
            codes = self.senses[(g, pos)][word]
            codes[spelling] = min(level, codes.get(spelling, 9))
            self.keys[word].add((g, pos))

    def level(self, key, word: str, spelling: str) -> int:
        codes = self.senses[key].get(word, {})
        return min(codes.get(spelling, 9), codes.get("_", 9))

    def regional(self, key, source: str, target: str) -> set[str]:
        """The spellings of [key] the target region uses and the source region does not."""
        return {
            w for w in self.senses[key]
            if self.level(key, w, target) <= PREFERRED and self.level(key, w, source) > PREFERRED
            # One word, not two: `percent` stays rather than become `per cent`.
            and " " not in w
        }


def respell(entries, esdb: Spellings, source: str, target: str, other: dict[str, int], known: set[str]):
    """
    Swap [source]-region spellings in [entries] for [target]-region ones. Only a
    sense where the word is the source region's spelling and the target uses
    another counts, so variants neither region prefers (`esp`/`esp.`,
    `foci`/`focuses`) are left as the list has them. A respelling must also be
    a word in one of AOSP's English lists ([known]), which keeps out ESDB's
    stray classical forms (`stele` -> `stelae`, `performative` -> `preformative`).
    """
    out = dict(entries)
    replaced, added = [], []
    for word, f in entries:
        # Names keep their own spelling (ESDB would turn Manila into Manilla).
        if word in KEEP or word[:1].isupper():
            continue
        keys = esdb.keys.get(word, ())
        regional = {
            k: alts for k in keys
            if esdb.level(k, word, source) <= PREFERRED
            and esdb.level(k, word, target) >= REPLACE_FROM
            and (alts := esdb.regional(k, source, target) & known)
        }
        if not regional:
            continue
        if len(regional) < len(keys) and any(esdb.level(k, word, target) < REPLACE_FROM for k in keys):
            # Used in the target region in another sense (`check`, `cheque` in
            # banking): keep it, and add the regional spelling where the other
            # AOSP list has a frequency for it.
            for alt in set().union(*regional.values()):
                if alt not in out and alt in other:
                    out[alt] = other[alt]
                    added.append((word, alt))
            continue
        alts = set().union(*regional.values())
        del out[word]
        for alt in alts:
            # A word the source list zeroed (a slur) stays zeroed.
            out[alt] = 0 if out.get(alt) == 0 else max(out.get(alt, 0), f)
        replaced.append((word, sorted(alts)))
    # Stable on ties, like import_aosp: the source's own order breaks them.
    order = {w: i for i, (w, _) in enumerate(entries)}
    result = sorted(out.items(), key=lambda kv: (-kv[1], order.get(kv[0], len(order))))
    return result, replaced, added


def write(target: Path, entries, preamble: str) -> None:
    body = "".join(f"{w} {f}\n" for w, f in entries)
    with open(target, "wb") as fh:
        with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0, compresslevel=9) as gz:
            gz.write((preamble + body).encode("utf-8"))
    print(f"{target.relative_to(DATA_DIR.parent)}\t{len(entries)}\t{target.stat().st_size}")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    db = Path(sys.argv[1])
    _, us = import_aosp.words(import_aosp.fetch("en_US", None))
    _, gb = import_aosp.words(import_aosp.fetch("en_GB", None))
    _, au = import_aosp.words(lineage_au())

    esdb = Spellings(db)
    known = {w for lst in (us, gb, au) for w, _ in lst}
    jobs = [
        ("en_ca", us, "A", "C", dict(gb),
         "# Canadian English: AOSP LatinIME en_US_wordlist.combined, Apache-2.0, "
         "Copyright (C) The Android Open Source Project,\n"
         "# respelled American -> Canadian with the English Speller Database "
         "(Copyright 2000-2026 Kevin Atkinson).\n"),
        ("en_au", au, "B", "D", dict(us),
         "# Australian English: LineageOS LatinIME en_AU_wordlist.combined (lineage-21.0), Apache-2.0,\n"
         "# Copyright (C) The Android Open Source Project and The LineageOS Project,\n"
         "# respelled British -> Australian with the English Speller Database "
         "(Copyright 2000-2026 Kevin Atkinson; Australian data Copyright 2016 Benjamin Titze).\n"),
    ]
    for stem, entries, source, target, other, credit in jobs:
        result, replaced, added = respell(entries, esdb, source, target, other, known)
        preamble = credit + (
            f"# {len(replaced)} words respelled, {len(added)} regional spellings added; "
            "frequencies are AOSP's 0..255 log scale.\n"
        )
        write(DATA_DIR / "en" / f"{stem}_aosp.txt.gz", result, preamble)
        # The full change list, for review; beside the database, not in the repo.
        with open(db.parent / f"{stem}_changes.tsv", "w") as fh:
            for w, alts in replaced:
                fh.write(f"replaced\t{w}\t{' '.join(alts)}\n")
            for w, alt in added:
                fh.write(f"added\t{w}\t{alt}\n")


if __name__ == "__main__":
    main()

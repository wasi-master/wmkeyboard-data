#!/usr/bin/env python3
"""
Import the AOSP LatinIME word lists as data/<lang>/<stem>_aosp.txt.gz.

Source: platform/packages/inputmethods/LatinIME, dictionaries/*_wordlist.combined.gz
(https://android.googlesource.com/platform/packages/inputmethods/LatinIME/+/refs/heads/main/dictionaries/),
Copyright (C) The Android Open Source Project, Apache License 2.0. The license
text is data/LICENSE-AOSP-APACHE-2.0.txt and the attribution is in NOTICE.

The .combined source is one `word=` record per word, with the frequency on
AOSP's own 0..255 log scale, plus shortcut records under some of them. This
writes the words alone, in the plain `word frequency` form every other list
here uses, sorted by frequency descending so the app can stop reading at its
size cap. The frequency is copied as it is, still 0..255: the app knows these
files by name and puts them on its own scale when it reads them, so the
conversion lives in one place.

Changes from the source, as Apache-2.0 section 4(b) asks them to be stated:
- Records marked `not_a_word=true` are dropped. They are misspellings that
  exist only to carry a correction (`aint` -> `ain't`), not words.
- Shortcut records and every field but the word and its frequency are dropped.
- Lines are re-sorted by frequency (the generic `en` list is not sorted; the
  app imports en_US and en_GB instead of it).

Usage:
    python3 scripts/import_aosp.py            # fetch from googlesource
    python3 scripts/import_aosp.py DIR        # read <code>_wordlist.combined.gz from DIR
"""

import base64
import gzip
import re
import sys
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BASE = ("https://android.googlesource.com/platform/packages/inputmethods/LatinIME/"
        "+/refs/heads/main/dictionaries/")

# AOSP list code -> (data folder, file stem). Hebrew is `iw` there; the English
# and Portuguese regional lists sit beside this repo's own lists for them.
LISTS = {
    "cs": ("cs", "cs"),
    "da": ("da", "da"),
    "de": ("de", "de"),
    "el": ("el", "el"),
    "en_US": ("en", "en"),
    "en_GB": ("en", "en_gb"),
    "es": ("es", "es"),
    "fi": ("fi", "fi"),
    "fr": ("fr", "fr"),
    "hr": ("hr", "hr"),
    "it": ("it", "it"),
    "iw": ("he", "he"),
    "lt": ("lt", "lt"),
    "lv": ("lv", "lv"),
    "nb": ("nb", "nb"),
    "nl": ("nl", "nl"),
    "pl": ("pl", "pl"),
    "pt_BR": ("pt_br", "pt_br"),
    "pt_PT": ("pt", "pt"),
    "ro": ("ro", "ro"),
    "ru": ("ru", "ru"),
    "sl": ("sl", "sl"),
    "sr": ("sr", "sr"),
    "sv": ("sv", "sv"),
    "tr": ("tr", "tr"),
}

WORD = re.compile(r"^ word=([^,]*),f=(\d+)")


def fetch(code: str, local: Path | None) -> bytes:
    name = f"{code}_wordlist.combined.gz"
    if local is not None:
        return (local / name).read_bytes()
    # googlesource serves raw files only base64-encoded, behind ?format=TEXT.
    with urllib.request.urlopen(BASE + name + "?format=TEXT", timeout=60) as resp:
        return base64.b64decode(resp.read())


def words(raw: bytes) -> tuple[str, list[tuple[str, int]]]:
    lines = gzip.decompress(raw).decode("utf-8").splitlines()
    header = lines[0]
    out: dict[str, int] = {}
    for line in lines[1:]:
        m = WORD.match(line)
        if not m or "not_a_word=true" in line:
            continue
        word, f = m.group(1), int(m.group(2))
        if word and (word not in out or out[word] < f):
            out[word] = f
    # Stable on ties: the source's own order breaks them.
    return header, sorted(out.items(), key=lambda kv: -kv[1])


def main() -> None:
    local = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    for code, (folder, stem) in LISTS.items():
        header, entries = words(fetch(code, local))
        target = DATA_DIR / folder / f"{stem}_aosp.txt.gz"
        target.parent.mkdir(parents=True, exist_ok=True)
        body = "".join(f"{w} {f}\n" for w, f in entries)
        preamble = (
            f"# AOSP LatinIME {code}_wordlist.combined, Apache-2.0, "
            f"Copyright (C) The Android Open Source Project\n"
            f"# {header}\n"
            f"# Frequencies are AOSP's 0..255 log scale; not_a_word records removed.\n"
        )
        # mtime=0 so a rerun on the same source writes the same bytes.
        with open(target, "wb") as fh:
            with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0, compresslevel=9) as gz:
                gz.write((preamble + body).encode("utf-8"))
        print(f"{target.relative_to(DATA_DIR.parent)}\t{len(entries)}\t{target.stat().st_size}")


if __name__ == "__main__":
    main()

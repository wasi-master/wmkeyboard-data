#!/usr/bin/env python3
"""
Import languages from Devanagari Documentation (motaitalic/devanagari-documentation)
and save as gzip wordlists in data/<lang>/<lang>_full.txt.gz.

License: MIT License (https://github.com/motaitalic/devanagari-documentation/blob/main/LICENSE)
"""

import gzip
import sys
import urllib.request
import ssl
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TARGETS = {
    "bho": {
        "name": "Bhojpuri",
        "url": "https://motaitalic.github.io/devanagari-documentation/languages/bhojpuri/basic-info/bhojpuri-word-frequency.txt",
    },
    "brx": {
        "name": "Bodo",
        "url": "https://motaitalic.github.io/devanagari-documentation/languages/bodo/basic-info/bodo-word-frequency.txt",
    },
    "doi": {
        "name": "Dogri",
        "url": "https://motaitalic.github.io/devanagari-documentation/languages/dogri/basic-info/dogri-word-frequency.txt",
    },
    "raj": {
        "name": "Rajasthani",
        "url": "https://motaitalic.github.io/devanagari-documentation/languages/rajasthani/basic-info/rajasthani-word-frequency.txt",
    },
    "mai": {
        "name": "Maithili",
        "url": "https://motaitalic.github.io/devanagari-documentation/languages/maithili/basic-info/maithili-word-frequency.txt",
    },
    "ks": {
        "name": "Kashmiri",
        "url": "https://motaitalic.github.io/devanagari-documentation/languages/kashmiri/basic-info/kashmiri-word-frequency.txt",
    },
}

def import_language(code: str):
    if code not in TARGETS:
        print(f"Unknown language code: {code}")
        return

    info = TARGETS[code]
    name = info["name"]
    url = info["url"]

    out_dir = DATA_DIR / code
    out_file = out_dir / f"{code}_full.txt.gz"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"Fetching {name} ({code}) from {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        content = resp.read().decode("utf-8")

    raw_lines = [l.strip() for l in content.splitlines() if l.strip()]
    print(f"Fetched {len(raw_lines)} raw entries for {name}.")

    word_freqs = {}
    total_entries = len(raw_lines)

    for rank, raw_word in enumerate(raw_lines):
        word = unicodedata.normalize("NFKC", raw_word).strip()
        if not word:
            continue
        
        freq = total_entries - rank
        if word not in word_freqs:
            word_freqs[word] = freq

    sorted_words = sorted(word_freqs.items(), key=lambda x: (-x[1], x[0]))

    out_dir.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_file, "wt", encoding="utf-8") as f:
        for word, freq in sorted_words:
            f.write(f"{word} {freq}\n")

    print(f"Successfully saved {len(sorted_words)} {name} words to {out_file}")

def main():
    codes = sys.argv[1:] if len(sys.argv) > 1 else list(TARGETS.keys())
    for code in codes:
        import_language(code)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Builds wubi86.tsv (code<TAB>word<TAB>freq) from ibus-table-chinese's Wubi 86 table.

    build_wubi_dict.py [wubi-jidian86.txt] [wubi86.tsv]

With no source given it fetches the pinned revision. The table's weights are web
hit counts for characters and phrases alike, so they rank the two against each
other as they stand; halved, because the largest (4,250,000,000) does not fit the
signed 32-bit number the app reads.

Left out: `z` codes (punctuation and letters behind a prefix; `z` is the wildcard
key here), rows outside Han (private-use glyphs, degree signs), and anything using
a character past U+FFFF, 42.7k rows no stock Android font draws that would each
cost heap in a table loaded whole.
"""
import sys
import urllib.request

REVISION = "44301450e681c23d60301747856c74b5b9d1312e"
SOURCE = (
    "https://raw.githubusercontent.com/mike-fabian/ibus-table-chinese/"
    f"{REVISION}/tables/wubi-jidian/wubi-jidian86.txt"
)


def is_han(word):
    return all(0x3400 <= ord(c) <= 0x9FFF or c == "〇" for c in word)


def read_source(path):
    if path:
        with open(path, encoding="utf-8") as src:
            return src.read()
    with urllib.request.urlopen(SOURCE) as response:
        return response.read().decode("utf-8")


def rows(text):
    in_table = False
    for line in text.splitlines():
        if line == "BEGIN_TABLE":
            in_table = True
        elif line == "END_TABLE":
            in_table = False
        elif in_table:
            parts = line.split("\t")
            if len(parts) >= 3:
                yield parts[0], parts[1], int(parts[2])


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else None
    target = sys.argv[2] if len(sys.argv) > 2 else "wubi86.tsv"
    best = {}
    for code, word, hits in rows(read_source(source)):
        if len(code) > 4 or not all("a" <= c <= "y" for c in code) or not is_han(word):
            continue
        best[(code, word)] = max(best.get((code, word), 0), hits // 2)
    with open(target, "w", encoding="utf-8", newline="\n") as out:
        out.write(f"# Wubi 86, from ibus-table-chinese {REVISION[:12]}. See LICENSE_wubi.txt.\n")
        for (code, word), freq in sorted(best.items(), key=lambda kv: (kv[0][0], -kv[1], kv[0][1])):
            out.write(f"{code}\t{word}\t{freq}\n")


if __name__ == "__main__":
    main()

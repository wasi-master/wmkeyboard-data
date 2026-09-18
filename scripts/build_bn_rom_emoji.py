#!/usr/bin/env python3
"""Build the Banglish emoji dictionary, `data/bn/bn_rom_emoji.json.gz`.

Banglish (`bn_rom` in the app) is Bengali typed in Latin letters, so its emoji
keywords are the Bengali ones, spelt the way people write them in a chat:
হাসি → hasi, hashi; ভালোবাসা → valobasha, bhalobasa. English rides alongside,
because a Banglish typist writes "love" and "heart" as often as "bhalobasa".

Per emoji, from the existing Bengali and English packs:

* every Bengali keyword is transliterated word by word. A word takes the
  spellings people actually use for it, found by inverting the app's
  romanised spelling map (`bn_rom.tsv`, plus the loanword map `en_bn.tsv`,
  which turns কম্পিউটার back into "computer") and ranking them by how often
  each appears in the Banglish corpus (`bn/bn_rom.txt.gz`). A word the maps
  do not know falls back to the pronunciation rules of the app's own
  `BengaliRomanizer`, ported below, so a rebuild gives the same spellings the
  keyboard's Bangla → Banglish conversion does;
* the English keywords and name are appended as they are;
* the name is the Bengali name in its best Banglish spelling.

A multi-word keyword takes the best spelling of each word; the variants are
single words, so "dento hasi" and "hashi" both land.

Usage:
  python3 scripts/build_bn_rom_emoji.py --app ../WMKeyboard
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# At most this many spellings per Bengali word: the best, and the variants a
# fair share of people type instead.
MAX_SPELLINGS = 3
# A variant must be at least this common, relative to the best spelling. The
# chat corpus has its share of mislabelled pairs (hossi for হাসি, garit for
# গাড়ি), and they are all rare next to the real spelling.
VARIANT_SHARE = 0.25
# Shorter than this is chat shorthand (tmr, amk), not a spelling anyone
# searches with — unless the rules produce it too (ki, na).
MIN_READABLE = 4
TRIPLED = re.compile(r"(.)\1\1")
# The letters Banglish spells both ways (ভ is bh or v, শ is sh or s). A rule
# spelling respelt with these counts as a variant when the corpus has it, so
# a word the maps do not list still gets hashi beside hasi.
RESPELLINGS = (("bh", "v"), ("sh", "s"), ("s", "sh"), ("chh", "ch"), ("ph", "f"))
# Corpus hits below this are noise, however they compare to the best.
MIN_VARIANT_COUNT = 5

# ---------------------------------------------------------------------------
# BengaliRomanizer, ported from
# core/language/.../transliteration/BengaliRomanizer.kt. Keep the two in step.
# ---------------------------------------------------------------------------

HASANTA = "\u09CD"
NUKTA = "\u09BC"
CANDRABINDU = "\u0981"
ANUSVARA = "\u0982"
VISARGA = "\u0983"
ZWJ, ZWNJ = "\u200D", "\u200C"

CONSONANTS = {
    "ক": "k", "খ": "kh", "গ": "g", "ঘ": "gh", "ঙ": "ng",
    "চ": "ch", "ছ": "chh", "জ": "j", "ঝ": "jh", "ঞ": "n",
    "ট": "t", "ঠ": "th", "ড": "d", "ঢ": "dh", "ণ": "n",
    "ত": "t", "থ": "th", "দ": "d", "ধ": "dh", "ন": "n",
    "প": "p", "ফ": "ph", "ব": "b", "ভ": "bh", "ম": "m",
    "য": "j", "র": "r", "ল": "l", "শ": "sh", "ষ": "sh",
    "স": "s", "হ": "h", "\u09DC": "r", "\u09DD": "rh", "\u09DF": "y",
    "ৎ": "t", "ৰ": "r", "ৱ": "w",
}
VOWELS = {
    "অ": "o", "আ": "a", "ই": "i", "ঈ": "i", "উ": "u", "ঊ": "u",
    "ঋ": "ri", "ঌ": "li", "এ": "e", "ঐ": "oi", "ও": "o", "ঔ": "ou",
}
MATRAS = {
    "া": "a", "ি": "i", "ী": "i", "ু": "u", "ূ": "u", "ৃ": "ri", "ৄ": "ri",
    "ৢ": "li", "ৣ": "li", "ে": "e", "ৈ": "oi", "ো": "o", "ৌ": "ou", "ৗ": "u",
}
KEEP_FINAL_O = {"ভ", "হ", "\u09DC", "\u09DD"}
B_STAYS_B = {"ম", "ল", "ন", "ণ", "ড", "ঙ"}


def normalize(text: str) -> str:
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c in (ZWJ, ZWNJ):
            i += 1
        elif nxt == NUKTA and c in "ডঢয":
            out.append({"ড": "\u09DC", "ঢ": "\u09DD", "য": "\u09DF"}[c])
            i += 2
        elif nxt == NUKTA:
            out.append(c)
            i += 2
        elif c == "ে" and nxt == "া":
            out.append("ো")
            i += 2
        elif c == "ে" and nxt == "ৗ":
            out.append("ৌ")
            i += 2
        elif c == "অ" and nxt == "া":
            out.append("আ")
            i += 2
        elif c == NUKTA:
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _plain(chars: list[str]) -> str:
    return "".join(CONSONANTS[c] for c in chars)


def _doubled(chars: list[str]) -> str:
    last = CONSONANTS[chars[-1]]
    return _plain(chars[:-1]) + last[0] + last


def _cluster(chars: list[str], initial: bool) -> tuple[str, bool, bool, bool]:
    """(text, yPhala, geminated, dead) for one consonant cluster."""
    if len(chars) == 1:
        return CONSONANTS[chars[0]], False, False, chars[0] == "ৎ"
    if chars == ["ক", "ষ"]:
        return ("kh" if initial else "kkh"), False, not initial, False
    if chars == ["জ", "ঞ"]:
        return "gg", False, True, False
    if chars == ["ঙ", "গ"]:
        return "ng", False, False, False
    last, base = chars[-1], chars[:-1]
    if last == "য":
        if initial:
            return _plain(base) + "y", True, False, False
        if base[-1] == "র":
            return _plain(base[:-1]) + "rj", False, True, False
        return _doubled(base), False, True, False
    if last == "ব" and base[0] != "ব":
        if initial:
            return _plain(base) + "w", False, False, False
        if base[-1] in B_STAYS_B:
            return _plain(base) + "b", False, False, False
        return _doubled(base), False, True, False
    return _plain(chars), False, False, False


def romanize_word(word: str) -> str:
    w = normalize(word)
    out: list[str] = []
    geminate_next = False
    i, n = 0, len(w)
    while i < n:
        c = w[i]
        if c in CONSONANTS:
            cluster = [c]
            j = i + 1
            while j + 1 < n and w[j] == HASANTA and w[j + 1] in CONSONANTS:
                cluster.append(w[j + 1])
                j += 2
            dangling = j < n and w[j] == HASANTA
            if dangling:
                j += 1
            initial = not out
            text, y_phala, geminated, dead = _cluster(cluster, initial)
            base_len = len(text)
            if geminate_next:
                text = text[0] + text
                geminate_next = False
            out.append(text)
            nxt = w[j] if j < n else None
            if nxt is not None and nxt in MATRAS:
                out.append(MATRAS[nxt])
                j += 1
            elif not (dangling or dead):
                strong = len(cluster) > 1 or geminated or len(text) > base_len
                if nxt is None:
                    keep = strong or cluster[-1] in KEEP_FINAL_O
                elif nxt in CONSONANTS:
                    after = w[j + 1] if j + 1 < n else None
                    keep = strong or initial or nxt == "হ" or after not in MATRAS
                else:
                    keep = True
                if keep:
                    out.append("a" if y_phala else "o")
            i = j
        elif c in VOWELS:
            out.append(VOWELS[c])
            i += 1
        elif c in MATRAS:
            out.append(MATRAS[c])
            i += 1
        elif c == ANUSVARA:
            out.append("ng")
            i += 1
        elif c == CANDRABINDU:
            out.append("n")
            i += 1
        elif c == VISARGA:
            if i == n - 1:
                out.append("h")
            else:
                geminate_next = True
            i += 1
        elif c == HASANTA:
            i += 1
        elif "০" <= c <= "৯":
            out.append(str(ord(c) - ord("০")))
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# Spellings people actually use
# ---------------------------------------------------------------------------


def read_map(path: Path) -> list[tuple[str, str]]:
    """(latin, bengali) rows of one of the app's TSV spelling maps."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        rows.append((parts[0].strip().lower(), normalize(unicodedata.normalize("NFC", parts[1].strip()))))
    return rows


def read_frequencies(path: Path) -> dict[str, int]:
    freq: dict[str, int] = {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                freq[parts[0]] = int(parts[1])
    return freq


class Speller:
    def __init__(self, chat_map: Path, loanword_map: Path, freq: dict[str, int]):
        self.freq = freq
        self.known: dict[str, set[str]] = {}
        # The loanword map is hand-curated, so its English spelling is kept
        # however rare the corpus says it is: কম্পিউটার is "computer".
        self.loanwords: dict[str, set[str]] = {}
        for path, into in ((chat_map, self.known), (loanword_map, self.loanwords)):
            for latin, bengali in read_map(path):
                if " " in bengali or not latin.isascii() or not latin.isalpha():
                    continue
                if TRIPLED.search(latin):
                    continue
                into.setdefault(bengali, set()).add(latin)
                if into is self.loanwords:
                    self.known.setdefault(bengali, set()).add(latin)
        self.cache: dict[str, list[str]] = {}

    @staticmethod
    def respellings(rule: str) -> set[str]:
        """[rule] with every mix of [RESPELLINGS] applied, itself included."""
        out = {""}
        i = 0
        while i < len(rule):
            options = [(rule[i], 1)]
            for src, dst in RESPELLINGS:
                # "s" must not split an "sh" that is already there.
                if rule.startswith(src, i) and not (src == "s" and rule.startswith("sh", i)):
                    options.append((dst, len(src)))
            step = max(n for _, n in options)
            # Consume the longest match; a one-letter option stands in for the
            # rest of it (b of bh) only through its own mapping.
            options = [(t + rule[i + n:i + step], step) for t, n in options]
            out = {o + t for o in out for t, _ in options}
            if len(out) > 64:
                return {rule}
            i += step
        return out

    def spellings(self, word: str) -> list[str]:
        """Best first; never empty for a Bengali word."""
        word = normalize(word)
        hit = self.cache.get(word)
        if hit is not None:
            return hit
        rule = romanize_word(word)
        candidates = {s for s in self.known.get(word, ()) if len(s) >= MIN_READABLE or s == rule}
        candidates.add(rule)
        candidates |= {s for s in self.respellings(rule) if self.freq.get(s, 0) >= MIN_VARIANT_COUNT}
        ranked = sorted(candidates, key=lambda s: (-self.freq.get(s, 0), s != rule, len(s), s))
        best_freq = self.freq.get(ranked[0], 0)
        out = [ranked[0]]
        for s in ranked[1:]:
            if len(out) >= MAX_SPELLINGS:
                break
            # The rule spelling always stays: it is what the keyboard's own
            # converter writes, so search must find it.
            if s == rule or s in self.loanwords.get(word, ()) or self.freq.get(s, 0) >= best_freq * VARIANT_SHARE > 0:
                out.append(s)
        self.cache[word] = out
        return out

    def best(self, text: str) -> str:
        """[text] with every Bengali run in its best spelling."""
        text = unicodedata.normalize("NFC", text)
        return re.sub(r"[\u0980-\u09FF\u200C\u200D]+", lambda m: self.spellings(m.group())[0], text)


def is_bengali(text: str) -> bool:
    return any("ঀ" <= c <= "৿" for c in text)


def clean_keyword(text: str) -> str:
    # Hyphenated CLDR compounds (মাঝারি-কালো) search better as words.
    return re.sub(r"\s+", " ", text.replace("-", " ").replace(":", " ")).strip().lower()


def load_pack(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def build(bn: list[dict], en: list[dict], speller: Speller) -> list[dict]:
    english = {row["emoji"]: row for row in en}
    out = []
    for row in bn:
        emoji = row["emoji"]
        keywords: list[str] = []
        for kw in row.get("keywords", []):
            if not is_bengali(kw):
                keywords.append(clean_keyword(kw))
                continue
            words = re.findall(r"[\u0980-\u09FF\u200C\u200D]+", unicodedata.normalize("NFC", kw))
            keywords.append(clean_keyword(speller.best(kw)))
            if len(words) == 1:
                keywords.extend(speller.spellings(words[0])[1:])
        name = speller.best(row.get("name", "")).strip()
        # The name as a keyword too: CLDR leaves the country out of a flag's
        # keywords (🇧🇩 is only "flag"), and the name is where it lives.
        keywords.append(clean_keyword(name))
        en_row = english.get(emoji)
        if en_row is not None:
            keywords.extend(clean_keyword(k) for k in en_row.get("keywords", []))
            keywords.append(clean_keyword(en_row.get("name", "")))
        keywords = [k for k in dict.fromkeys(keywords) if k and k.isascii()]
        if not keywords:
            continue
        out.append({
            "emoji": emoji,
            "name": name,
            "keywords": keywords,
            "category": row.get("category", ""),
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app", type=Path, required=True, help="WMKeyboard checkout (for its spelling maps)")
    parser.add_argument("--out", type=Path, default=ROOT / "data/bn/bn_rom_emoji.json.gz")
    args = parser.parse_args()

    maps_dir = args.app / "app/src/main/assets/dictionaries"
    speller = Speller(
        maps_dir / "bn_rom.tsv",
        maps_dir / "en_bn.tsv",
        read_frequencies(ROOT / "data/bn/bn_rom.txt.gz"),
    )
    rows = build(
        load_pack(ROOT / "data/bn/bn_emoji.json.gz"),
        load_pack(ROOT / "data/en/en_emoji.json.gz"),
        speller,
    )
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # mtime=0 so an unchanged rebuild is byte-identical.
    with open(args.out, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
        gz.write(payload)
    print(f"wrote {len(rows)} emoji to {args.out} ({args.out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

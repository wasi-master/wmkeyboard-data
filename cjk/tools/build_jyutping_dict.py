#!/usr/bin/env python3
"""
build_jyutping_dict.py — Convert rime-cantonese & CC-Canto into WMKeyboard's Jyutping dictionary TSV.

Format:
  reading<TAB>word<TAB>freq

where:
  reading = TONELESS Jyutping, lowercase a-z only (tone digits 1-6 stripped, concatenated with NO separator)
  word    = Traditional Han characters
  freq    = integer frequency (higher = more common)

Output:
  cjk/jyutping.tsv
"""

import argparse
import gzip
import hashlib
import io
import math
import os
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

# Data Sources
RIME_URLS = [
    ("chars", "https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.chars.dict.yaml"),
    ("words", "https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.words.dict.yaml"),
    ("lettered", "https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.lettered.dict.yaml"),
]

CANTO_URL = "https://cantonese.org/cccanto-170202.zip"

SCRIPT_DIR = Path(__file__).resolve().parent
CJK_DIR = SCRIPT_DIR.parent
REPO_DIR = CJK_DIR.parent
DEFAULT_OUT = CJK_DIR / "jyutping.tsv"
DEFAULT_SYLLABLES = CJK_DIR / "jyutping_syllables.txt"
# Traditional-script corpus counts (hermitdave/FrequencyWords, OpenSubtitles
# 2018). Neither Cantonese source carries usable frequencies — see the note on
# `score_corpus` — so this supplies the only real evidence in the file.
DEFAULT_CORPUS = REPO_DIR / "data" / "zh_tw" / "zh_tw_full.txt.gz"

# Frequency bands. Kept disjoint so the *kind* of evidence behind a row always
# outranks the within-band grading, and so a row's band is readable from its
# number alone when debugging a bad candidate order.
CORPUS_MIN, CORPUS_MAX = 101, 1000  # attested in the corpus, log-scaled by count
CANTO_MIN, CANTO_MAX = 51, 100      # in rime-cantonese's curated lexicon only
TAIL_MIN, TAIL_MAX = 1, 50          # CC-Canto only: no frequency evidence at all

# Coverage-layer limits. Words rarer than this in a 617k-word corpus are not
# worth the rows, and a word needing more than a few readings is one whose
# characters are ambiguous enough that guessing does more harm than good.
GEN_MIN_COUNT = 50
GEN_MAX_WORD_LEN = 4
GEN_MAX_READINGS = 4

# How much in-word evidence a single character needs before its corpus weight
# is believed at all. The subtitle corpus is dirty at the rare end — 礛 is
# listed 9913 times standalone, more often than 藍 — so a lone character's own
# count cannot be trusted; see `char_evidence`.
MIN_CHAR_EVIDENCE = 50


def clean_reading(raw_jp: str):
    """Strips tone digits 1-6 and converts to concatenated toneless ASCII lowercase."""
    if not raw_jp:
        return None, None
    syls = [re.sub(r"[1-6]", "", s.lower()).strip() for s in raw_jp.split()]
    if not syls or not all(s.isalpha() and s.isascii() for s in syls):
        return None, None
    return "".join(syls), syls


# Han ideographs (basic, Ext A/B/C, compatibility) plus the CJK punctuation that
# legitimately appears inside a headword.
_HAN_RANGES = (
    (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
    (0x20000, 0x2A6DF), (0x2A700, 0x2EBEF), (0x2F800, 0x2FA1F),
)
_CJK_PUNCT = set("\u3000、。〃〈〉《》「」『』【】〔〕〖〗・…—‧")


def is_han_word(word: str) -> bool:
    """
    True only if every character is Han or CJK punctuation.

    CC-Canto carries entries whose headword is English or mixed — 亞head, IP,
    uncle, 開Band, 豬仔Plan, and bare % signs — which are meaningless in a
    Chinese IME and are dropped. Checking a whitelist of Han rather than
    blacklisting [A-Za-z] matters: a good share of them use FULLWIDTH Latin
    (ｐｏｗｅｒ, Ｖａｎ仔), which a naive ASCII test walks straight past.
    """
    if not word:
        return False
    return all(
        any(lo <= ord(c) <= hi for lo, hi in _HAN_RANGES) or c in _CJK_PUNCT
        for c in word
    )


def load_syllable_inventory(syllables_path: Path) -> set:
    """Loads toneless Jyutping syllable inventory."""
    if not syllables_path.exists():
        # Fallback path in app repo if needed
        alt_path = Path("/Users/wasimaster/Work/WMKeyboard/app/src/main/assets/dictionaries/jyutping_syllables.txt")
        if alt_path.exists():
            syllables_path = alt_path
        else:
            raise FileNotFoundError(f"Syllable inventory file not found: {syllables_path}")

    print(f"Loading syllable inventory from {syllables_path}...")
    syllables = set()
    with open(syllables_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()
            if line and not line.startswith("#"):
                syllables.add(line)
    return syllables


def segment_greedy(reading: str, syl_set: set) -> bool:
    """Greedily splits reading longest-first against valid syllable set."""
    idx = 0
    n = len(reading)
    while idx < n:
        match_len = 0
        for l in range(min(6, n - idx), 0, -1):
            if reading[idx : idx + l] in syl_set:
                match_len = l
                break
        if match_len == 0:
            return False
        idx += match_len
    return True


def fetch_rime_data():
    """Fetches rime-cantonese dictionary YAML files."""
    data = {}
    for name, url in RIME_URLS:
        print(f"Fetching rime-cantonese {name} from {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "WMKeyboard-DictBuilder/1.0"})
        with urllib.request.urlopen(req) as resp:
            data[name] = resp.read().decode("utf-8")
    return data


def fetch_cccanto_data():
    """Fetches CC-Canto text file from zip distribution."""
    print(f"Fetching CC-Canto from {CANTO_URL}...")
    req = urllib.request.Request(CANTO_URL, headers={"User-Agent": "WMKeyboard-DictBuilder/1.0"})
    with urllib.request.urlopen(req) as resp:
        zf = zipfile.ZipFile(io.BytesIO(resp.read()))
        return zf.read("cccanto-webdist.txt").decode("utf-8")


def load_corpus_counts(corpus_path: Path) -> dict:
    """
    Loads `word count` pairs from a gzipped frequency list, Han headwords only.

    The list is Traditional script, which is what this dictionary emits, so the
    join is direct — no Simplified/Traditional mapping to get wrong.
    """
    if not corpus_path.exists():
        print(f"WARNING: corpus not found at {corpus_path} — every row will fall")
        print("         back to the no-evidence bands and candidate order will be")
        print("         close to arbitrary. Pass --corpus to fix.")
        return {}

    print(f"Loading corpus frequencies from {corpus_path}...")
    counts = {}
    with gzip.open(corpus_path, "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) != 2:
                continue
            word, raw = parts
            if not is_han_word(word):
                continue
            try:
                n = int(raw)
            except ValueError:
                continue
            if n > 0:
                counts[word] = max(counts.get(word, 0), n)
    print(f"  {len(counts)} Han words with counts")
    return counts


def parse_char_readings(chars_text: str) -> dict:
    """
    Per-character toneless readings from rime-cantonese's chars dictionary,
    ordered primary-first, each with the share of that character's usage.

    The `%` column marks a **minor** reading — 䕥 nei5 5% means nei5 is a rare
    way to read 䕥, and a character's ordinary reading carries no percentage at
    all (你 nei5). Reading it as a bonus, as this script once did, promotes
    exactly the characters that should sink: it is why 䕥/儞/呢 outranked 你.
    Unmarked readings split whatever the marked ones leave.
    """
    listed = {}
    in_header = True
    for line in chars_text.splitlines():
        line = line.rstrip("\n")
        if line == "...":
            in_header = False
            continue
        if in_header or not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        word = parts[0].strip()
        if len(word) != 1:
            continue
        reading, _ = clean_reading(parts[1].strip())
        if not reading:
            continue
        pct = None
        if len(parts) >= 3 and parts[2].strip().endswith("%"):
            try:
                pct = int(parts[2].strip()[:-1])
            except ValueError:
                pct = None
        # A character can list the same toneless reading twice (nei5/nei6);
        # keep the most generous share, and treat "unmarked" as dominant.
        prev = listed.setdefault(word, {}).get(reading, -1)
        share = 100 if pct is None else pct
        if share > prev:
            listed[word][reading] = share
        if pct is None:
            listed[word][reading] = 100

    out = {}
    for word, readings in listed.items():
        marked = {r: p for r, p in readings.items() if p != 100}
        unmarked = [r for r, p in readings.items() if p == 100]
        remainder = max(0, 100 - sum(marked.values()))
        shares = dict(marked)
        if unmarked:
            each = remainder / len(unmarked) if remainder else 1.0
            for r in unmarked:
                shares[r] = each
        # Primary first, so the coverage layer can take the likeliest reading.
        out[word] = sorted(shares.items(), key=lambda kv: (-kv[1], kv[0]))
    return out


def char_evidence(corpus: dict, rime_data: dict):
    """
    Two independent per-character frequency signals, since neither alone is
    trustworthy for this dictionary.

    A character's own count in the subtitle corpus is noise at the rare end —
    礛 appears 9913 times, 胊 1801, both far above 藍 at 794 — because a corpus
    that size collects OCR and encoding debris that never occurs in real words.
    Summing the counts of the multi-character *words* a character appears in
    throws that away completely: 礛 scores 7 and 胊 scores 1, while 藍 scores
    3148 and 男 24582.

    That signal is Mandarin, though, and says nothing about 佢, 嘅, 喺 or 嘢 —
    the words a Cantonese speaker types most. The Cantonese half is the same
    trick over rime-cantonese's own word list: how many multi-character
    Cantonese words a character appears in. It separates just as cleanly (佢
    372, 嘢 415, 唔 1595, against 0 for every noise character above), and no
    corpus of Cantonese is needed to get it.

    Returns (standard, cantonese) — both {char: weight}.
    """
    standard = {}
    for word, count in corpus.items():
        if len(word) < 2:
            continue
        for ch in set(word):
            standard[ch] = standard.get(ch, 0) + count

    cantonese = {}
    for name in ["words", "lettered"]:
        in_header = True
        for line in rime_data.get(name, "").splitlines():
            line = line.strip()
            if line == "...":
                in_header = False
                continue
            if in_header or not line or line.startswith("#"):
                continue
            word = line.split("\t")[0].strip()
            if len(word) < 2 or not is_han_word(word):
                continue
            for ch in set(word):
                cantonese[ch] = cantonese.get(ch, 0) + 1

    return standard, cantonese


def score_corpus(count: int, lo: int, hi: int) -> int:
    """
    Maps a corpus count onto [CORPUS_MIN, CORPUS_MAX], log-scaled.

    Log rather than linear because word frequency is Zipfian: on a linear scale
    的 alone would flatten everything below the top hundred into one value, and
    the ordering that actually decides candidate lists is the one *among* the
    ordinary words further down.
    """
    if hi <= lo:
        return CORPUS_MAX
    t = (math.log(count) - math.log(lo)) / (math.log(hi) - math.log(lo))
    return CORPUS_MIN + int(round((CORPUS_MAX - CORPUS_MIN) * t))


def band_score(word: str, share: float, lo: int, hi: int) -> int:
    """
    A row's place inside one of the no-evidence bands.

    Shorter words score higher: they compete for shorter buffers, where being
    passed over is most visible, and a longer word covering the same input wins
    on span in the decoder anyway. [share] then demotes minor readings.
    """
    span = hi - lo
    length_part = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.45}.get(len(word), 0.3)
    scale = length_part * (0.35 + 0.65 * (share / 100.0))
    return max(lo, min(hi, lo + int(round(span * scale))))


class Scorer:
    """
    Turns a (word, reading) pair into a frequency, from whatever evidence the
    sources actually support for it.

    Single characters and multi-character words are scored from different
    signals on purpose. A two-character word is self-validating — corpus debris
    almost never forms one — so its own count is usable. A lone character's
    count is not, so it is scored from `char_evidence` instead.
    """

    def __init__(self, corpus: dict, char_readings: dict, standard: dict, cantonese: dict):
        self.corpus = corpus
        self.char_readings = char_readings
        self.standard = standard
        self.cantonese = cantonese
        self.word_lo = min((c for w, c in corpus.items() if len(w) >= 2), default=0)
        self.word_hi = max((c for w, c in corpus.items() if len(w) >= 2), default=0)
        self.std_lo, self.std_hi = MIN_CHAR_EVIDENCE, max(standard.values(), default=0)
        self.can_lo, self.can_hi = 1, max(cantonese.values(), default=0)

    def share(self, word: str, reading: str) -> float:
        """How much of [word]'s usage this reading accounts for, 0-100."""
        if len(word) != 1:
            return 100.0
        for r, sh in self.char_readings.get(word, ()):
            if r == reading:
                return sh
        return 100.0

    def evidence_score(self, word: str) -> int:
        """The 101-1000 corpus-band score for [word], or 0 if unevidenced."""
        if len(word) >= 2:
            count = self.corpus.get(word, 0)
            if count and self.word_hi:
                return score_corpus(max(count, self.word_lo), self.word_lo, self.word_hi)
            return 0
        # A character is believed if *either* corpus says so. Taking the max
        # rather than a blend keeps a core Cantonese character from being
        # dragged down by a Mandarin corpus that simply never uses it.
        best = 0
        std = self.standard.get(word, 0)
        if std >= MIN_CHAR_EVIDENCE and self.std_hi:
            best = max(best, score_corpus(std, self.std_lo, self.std_hi))
        can = self.cantonese.get(word, 0)
        if can >= self.can_lo and self.can_hi:
            best = max(best, score_corpus(can, self.can_lo, self.can_hi))
        return best

    def score(self, word: str, reading: str, fallback_lo: int, fallback_hi: int) -> int:
        share = self.share(word, reading)
        freq = self.evidence_score(word)
        if freq:
            # A minor reading of a common character must not inherit the whole
            # character's weight — that is how 䕥 (nei5 at 5%) came to outrank
            # 你 in the first place.
            if share < 100:
                freq = max(CORPUS_MIN, int(freq * (0.4 + 0.6 * share / 100.0)))
            return freq
        return band_score(word, share, fallback_lo, fallback_hi)


def parse_and_build(rime_data: dict, canto_text: str, scorer: "Scorer"):
    """Parses source data into unique (reading, word) entries with frequencies."""
    entry_map = {}

    def record(reading: str, word: str, freq: int):
        key = (reading, word)
        if key not in entry_map or freq > entry_map[key]:
            entry_map[key] = freq

    # Process rime-cantonese entries
    for name in ["chars", "words", "lettered"]:
        in_header = True
        for line in rime_data.get(name, "").splitlines():
            line = line.strip()
            if line == "...":
                in_header = False
                continue
            if in_header or not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) < 2:
                continue
            word = parts[0].strip()
            reading, _ = clean_reading(parts[1].strip())
            if not reading or not word or not is_han_word(word):
                continue

            # Unevidenced rime entries land in the Cantonese band rather than
            # the tail: being in a curated Cantonese lexicon is itself weak
            # evidence, which a CC-Canto-only rarity does not have.
            record(reading, word, scorer.score(word, reading, CANTO_MIN, CANTO_MAX))

    # Process CC-Canto entries
    for line in canto_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(\S+)\s+(\S+)\s+\[.*?\]\s+\{(.*?)\}", line)
        if not m:
            continue
        trad, _simp, raw_jp = m.groups()
        reading, _ = clean_reading(raw_jp)
        if not reading or not trad or not is_han_word(trad):
            continue

        record(reading, trad, scorer.score(trad, reading, TAIL_MIN, TAIL_MAX))

    return entry_map


def build_coverage_layer(entry_map: dict, corpus: dict, scorer: "Scorer", syllables: set) -> int:
    """
    Adds readings for corpus words neither Cantonese source lists, in place.

    Both sources are deliberately Cantonese-specific — rime-cantonese leans
    colloquial and CC-Canto is a *supplement* to CC-CEDICT carrying only
    distinctly Cantonese entries — so the standard vocabulary a Cantonese
    speaker still types every day falls through the gap between them. 你好 was
    the case that surfaced this: the pack had 你好煩 and 你好嘢 but no `neihou`,
    so typing the commonest greeting in the language returned nothing.

    Readings are assembled per character, likeliest first, which is how a word
    without its own attested reading has to be spelled. Returns the row count
    added.
    """
    have_word = {w for _r, w in entry_map}
    added = 0

    for word, count in corpus.items():
        if count < GEN_MIN_COUNT or not 2 <= len(word) <= GEN_MAX_WORD_LEN:
            continue
        if word in have_word:
            continue
        per_char = [scorer.char_readings.get(ch) for ch in word]
        if not all(per_char):
            continue

        readings = [""]
        for options in per_char:
            readings = [
                prefix + reading
                for prefix in readings
                for reading, _share in options
            ][:GEN_MAX_READINGS]

        # A synthetic reading the app's segmenter cannot split is a row nobody
        # can ever type. Attested rows are reported instead of dropped — a real
        # source disagreeing with the inventory is worth seeing — but there is
        # nothing to learn from a spelling this script invented.
        readings = [r for r in readings if segment_greedy(r, syllables)]

        freq = scorer.evidence_score(word)
        if not freq:
            continue
        for rank, reading in enumerate(readings):
            # Only the likeliest spelling keeps the word's full weight; the
            # rest are guesses and should not outrank an attested reading.
            key = (reading, word)
            if key in entry_map:
                continue
            entry_map[key] = freq if rank == 0 else max(CORPUS_MIN, freq // (rank + 1))
            added += 1

    return added


def sort_entries(entry_map: dict):
    """Sorts by reading, then frequency descending, then word."""
    return [
        (r, w, f)
        for (r, w), f in sorted(entry_map.items(), key=lambda x: (x[0][0], -x[1], x[0][1]))
    ]


def main():
    parser = argparse.ArgumentParser(description="Build Cantonese Jyutping dictionary TSV for WMKeyboard.")
    parser.add_argument("--syllables", type=Path, default=DEFAULT_SYLLABLES, help="Path to jyutping_syllables.txt")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output TSV file path")
    parser.add_argument(
        "--corpus", type=Path, default=DEFAULT_CORPUS,
        help="Gzipped Traditional-script `word count` frequency list",
    )
    parser.add_argument(
        "--no-coverage", action="store_true",
        help="Skip the generated standard-vocabulary layer (rime + CC-Canto only)",
    )
    args = parser.parse_args()

    syllables = load_syllable_inventory(args.syllables)
    corpus = load_corpus_counts(args.corpus)
    rime_data = fetch_rime_data()
    canto_text = fetch_cccanto_data()

    char_readings = parse_char_readings(rime_data.get("chars", ""))
    print(f"Character reading table: {len(char_readings)} characters")

    standard, cantonese = char_evidence(corpus, rime_data)
    print(f"Character evidence: {len(standard)} from corpus words, {len(cantonese)} from rime words")
    scorer = Scorer(corpus, char_readings, standard, cantonese)

    print("Parsing and processing entries...")
    entry_map = parse_and_build(rime_data, canto_text, scorer)
    attested = len(entry_map)

    generated = 0
    if args.no_coverage:
        print("Coverage layer skipped (--no-coverage)")
    elif not corpus:
        print("Coverage layer skipped (no corpus)")
    else:
        print("Building coverage layer for standard vocabulary...")
        generated = build_coverage_layer(entry_map, corpus, scorer, syllables)
        print(f"  {generated} rows added")

    entries = sort_entries(entry_map)

    # Cross-check greedy segmentation against jyutping_syllables.txt
    print("Performing greedy segmentation cross-check...")
    unsegmentable_readings = set()
    unsegmentable_details = []

    for reading, word, freq in entries:
        if not segment_greedy(reading, syllables):
            unsegmentable_readings.add(reading)
            unsegmentable_details.append((reading, word))

    failed_list = sorted(unsegmentable_readings)

    if failed_list:
        print(f"\n[FAIL LOUDLY / CROSS-CHECK REPORT] {len(failed_list)} readings failed greedy segmentation against syllable inventory:")
        for r in failed_list:
            matching_words = [w for rd, w in unsegmentable_details if rd == r]
            print(f"  - {r} (words: {', '.join(matching_words[:5])})")
    else:
        print("\nAll readings passed greedy segmentation cross-check!")

    # Write output file
    out_path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    header = [
        "# Cantonese Jyutping Dictionary (rime-cantonese CC BY 4.0 / CC-Canto CC BY-SA 3.0)",
        "# Frequencies and standard-vocabulary coverage derived from the zh_tw",
        "# frequency list (hermitdave/FrequencyWords, OpenSubtitles 2018, CC BY-SA 4.0)",
        "# Format: reading\tword\tfreq",
    ]

    print(f"\nWriting {len(entries)} rows to {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n")
        for r, w, f_val in entries:
            f.write(f"{r}\t{w}\t{f_val}\n")

    # Statistics
    distinct_readings = len(set(r for r, w, f_val in entries))
    file_size = out_path.stat().st_size

    hasher = hashlib.sha256()
    with open(out_path, "rb") as f:
        hasher.update(f.read())
    sha256_hex = hasher.hexdigest()

    banded = {"corpus": 0, "canto": 0, "tail": 0}
    for _r, _w, f_val in entries:
        if f_val >= CORPUS_MIN:
            banded["corpus"] += 1
        elif f_val >= CANTO_MIN:
            banded["canto"] += 1
        else:
            banded["tail"] += 1

    print("\n================ REPORT WHEN DONE ================")
    print(f"Total rows: {len(entries)}")
    print(f"  attested (rime + CC-Canto): {attested}")
    print(f"  generated coverage layer:   {generated}")
    print(f"Frequency bands:")
    print(f"  {CORPUS_MIN}-{CORPUS_MAX} corpus-attested: {banded['corpus']}")
    print(f"  {CANTO_MIN}-{CANTO_MAX} rime-cantonese only: {banded['canto']}")
    print(f"  {TAIL_MIN}-{TAIL_MAX} no evidence:         {banded['tail']}")
    print(f"Distinct readings: {distinct_readings}")
    print(f"Failed segmentation readings count: {len(failed_list)}")
    print(f"Output File: {out_path}")
    print(f"Size: {file_size} bytes")
    print(f"SHA-256: {sha256_hex}")
    print("==================================================")


if __name__ == "__main__":
    main()

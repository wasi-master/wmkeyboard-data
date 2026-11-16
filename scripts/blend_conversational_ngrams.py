#!/usr/bin/env python3

"""Blend conversational word pairs into a language's existing n-gram lists.

The Leipzig-built lists (see import_leipzig_ngrams.py) are mostly news, web
and encyclopedia prose, so what they expect after a word is what a newspaper
writes after it: French `est` is followed by `un, une, le` rather than `très`,
`mon` by `père, frère, fils`, English `is` by `a, the, not` rather than
`very`. A keyboard predicts what people say to each other. Film and TV
subtitles are the largest open source of that register, so this counts word
pairs and triples over OpenSubtitles 2018 (via OPUS) and adds them to the
existing counts.

    python3 scripts/blend_conversational_ngrams.py --lang fr \
        --text https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/mono/fr.txt.gz \
        --lines 20000000 --weight 3 --out-suffix _v2

Steps:

  1. Count. The first --lines lines of --text (a URL or a local file, plain
     or gzip, one sentence a line; only the head of a URL is fetched) are
     tokenized exactly as import_leipzig_ngrams.py's `generic` tokenizer
     tokenizes Leipzig sentences, gated on a vocabulary: every word the
     existing lists already hold, plus the first --vocab-words words of
     data/<lang>/<lang>_full.txt.gz when there is one. Counts are cached in
     --cache, so the blend can be redone with another weight for free.

  2. Blend. The conversational counts are scaled so that, over the rows
     kept, they carry --weight times the existing lists' total mass, then
     added to them. --weight 1 makes subtitles and the old corpora equal
     partners; the existing lists' own rows are never dropped, only
     outranked.

  3. Write data/<lang>/<prefix>_bigrams<suffix>.txt.gz and the trigrams,
     count-descending, at most --max-bigrams / --max-trigrams rows (the app
     reads the first 150,000 and 75,000).

OpenSubtitles 2018: P. Lison and J. Tiedemann, "OpenSubtitles2016: Extracting
Large Parallel Corpora from Movie and TV Subtitles", LREC 2016; text from
http://www.opensubtitles.org/, distributed by OPUS (https://opus.nlpl.eu/).
Only counts of word pairs and triples are published, never text.
"""

import argparse
import gzip
import io
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_leipzig_ngrams import (  # noqa: E402
    GENERIC_MAX_TOKEN_LEN,
    MEMORY_VOCAB_LIMIT,
    GenericTokenizer,
    MemorySink,
    generic_alphabet,
    load_vocab,
    normalize_generic,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def read_counts(path: Path, arity: int):
    counts = {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) != arity + 1:
                continue
            try:
                counts[tuple(parts[:arity])] = counts.get(tuple(parts[:arity]), 0) + int(parts[-1])
            except ValueError:
                continue
    return counts


# Python lowercases I to i and İ to i + U+0307, which in Turkish spells a
# different word and no word at all; Romanian subtitles still write the
# cedilla letters the word lists spell with a comma below.
TURKIC = {"tr", "az"}
TURKIC_CASE = str.maketrans({"\u0130": "i", "I": "\u0131"})
ROMANIAN_COMMAS = str.maketrans("\u015f\u0163\u015e\u0162", "\u0219\u021b\u0218\u021a")


def lines_of(source: str, limit: int):
    if source.startswith(("http://", "https://")):
        raw = urllib.request.urlopen(source)  # noqa: S310 - fixed corpus URL
    else:
        raw = open(source, "rb")
    stream = gzip.GzipFile(fileobj=raw) if source.endswith(".gz") else raw
    text = io.TextIOWrapper(stream, encoding="utf-8", errors="replace")
    n = 0
    try:
        for line in text:
            if n >= limit:
                break
            line = line.strip()
            if line.startswith("-"):
                line = line.lstrip("- ")
            if line:
                n += 1
                yield line
    except (EOFError, OSError):
        return
    finally:
        raw.close()


def count(lang, prefix, sources, limit, vocab_words, cache: Path, base_suffix=""):
    bi_cache = cache / f"{prefix}_conv_bigrams.txt.gz"
    tri_cache = cache / f"{prefix}_conv_trigrams.txt.gz"
    if bi_cache.exists() and tri_cache.exists():
        print(f"{lang}: cached conversational counts in {cache}")
        return bi_cache, tri_cache
    words = set()
    for name in (f"{prefix}_bigrams{base_suffix}.txt.gz", f"{prefix}_trigrams{base_suffix}.txt.gz"):
        with gzip.open(DATA_DIR / lang / name, "rt", encoding="utf-8") as f:
            for line in f:
                words.update(line.split()[:-1])
    full = DATA_DIR / lang / f"{lang}_full.txt.gz"
    if full.exists() and vocab_words:
        words.update(load_vocab(full, normalize_generic, vocab_words))
    words = sorted(w for w in words if w and len(w) <= GENERIC_MAX_TOKEN_LEN)[:MEMORY_VOCAB_LIMIT]
    vocab = frozenset(words)
    tokenize = GenericTokenizer(generic_alphabet(words), GENERIC_MAX_TOKEN_LEN, vocab=vocab)
    sink = MemorySink(words)
    sink.begin_group(1)
    n = tokens = 0
    lines = (line for source in sources for line in lines_of(source, limit // len(sources)))
    for line in lines:
        n += 1
        if lang in TURKIC:
            line = line.translate(TURKIC_CASE)
        elif lang == "ro":
            line = line.translate(ROMANIAN_COMMAS)
        for run in tokenize(line):
            tokens += len(run)
            sink.add(run)
    sink.end_group()
    print(f"{lang}: {n} lines, {tokens} tokens counted over a {len(words)}-word vocabulary")
    cache.mkdir(parents=True, exist_ok=True)
    sink.write_bigrams(bi_cache, 2, 0)
    sink.write_trigrams(tri_cache, 2, 0)
    return bi_cache, tri_cache


# Pair occurrences (after the count-2 floor) behind a full --weight. A smaller
# sample gets a share of the weight in proportion, so a few hundred thousand
# words of Afrikaans subtitles are not blown up into the equal of a corpus.
FULL_WEIGHT_MASS = 30_000_000


def effective_weight(extra: dict, weight: float, full_mass: float = FULL_WEIGHT_MASS) -> float:
    return weight * min(1.0, sum(extra.values()) / full_mass)


def blend(base: dict, extra: dict, weight: float, max_items: int):
    base_mass = sum(base.values())
    extra_mass = sum(extra.values())
    scale = weight * base_mass / extra_mass if extra_mass else 0.0
    out = dict(base)
    for key, value in extra.items():
        out[key] = out.get(key, 0) + value * scale
    rows = sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))
    rows = [(k, max(1, round(v))) for k, v in rows[:max_items]]
    rows.sort(key=lambda kv: (-kv[1], kv[0]))
    return rows


def write(rows, path: Path):
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as f:
        for key, value in rows:
            f.write(f"{' '.join(key)} {value}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--lang", required=True, help="data/<lang> folder")
    ap.add_argument("--prefix", help="list stem prefix (default: --lang)")
    ap.add_argument("--text", required=True, action="append",
                    help="sentence text, URL or path, plain or .gz; repeat to split --lines between several")
    ap.add_argument("--lines", type=int, default=20_000_000)
    ap.add_argument("--vocab-words", type=int, default=200_000)
    ap.add_argument("--weight", type=float, default=3.0)
    ap.add_argument("--full-mass", type=float, default=FULL_WEIGHT_MASS,
                    help="pair occurrences behind the full --weight; a smaller sample gets a share")
    ap.add_argument("--min-weight", type=float, default=0.3,
                    help="write nothing when the sample is too small to earn this much weight")
    ap.add_argument("--max-bigrams", type=int, default=400_000)
    ap.add_argument("--max-trigrams", type=int, default=200_000)
    ap.add_argument("--base-suffix", default="", help="the existing lists' stem suffix, e.g. _v2")
    ap.add_argument("--out-suffix", default="_v2", help="appended to the stems, e.g. _v2")
    ap.add_argument("--out-dir", type=Path, help="default: data/<lang>")
    ap.add_argument("--base-dir", type=Path, help="where the existing lists are; default: data/<lang>")
    ap.add_argument("--cache", type=Path, default=Path("/tmp/wmkb-conv-ngrams"))
    a = ap.parse_args()

    prefix = a.prefix or a.lang
    bi_cache, tri_cache = count(a.lang, prefix, a.text, a.lines, a.vocab_words, a.cache, a.base_suffix)
    out_dir = a.out_dir or DATA_DIR / a.lang
    out_dir.mkdir(parents=True, exist_ok=True)
    for arity, name, cached, cap in (
        (2, "bigrams", bi_cache, a.max_bigrams),
        (3, "trigrams", tri_cache, a.max_trigrams),
    ):
        base = read_counts((a.base_dir or DATA_DIR / a.lang) / f"{prefix}_{name}{a.base_suffix}.txt.gz", arity)
        extra = read_counts(cached, arity)
        weight = effective_weight(extra, a.weight, a.full_mass)
        if arity == 2 and weight < a.min_weight:
            print(f"{a.lang}: {sum(extra.values())} pair occurrences earn weight {weight:.2f}, "
                  f"under --min-weight {a.min_weight}; lists left as they are")
            return
        rows = blend(base, extra, weight, cap)
        out = out_dir / f"{prefix}_{name}{a.out_suffix}.txt.gz"
        write(rows, out)
        print(f"{a.lang}: {len(base)} + {len(extra)} {name} at weight {weight:.2f} -> {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()

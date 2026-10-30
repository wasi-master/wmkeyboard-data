#!/usr/bin/env python3

"""Give a bare word list real frequencies, counted over Leipzig Corpora
Collection sentence corpora.

Some lists in data/ are wordlists wearing the frequency format: every word of
data/bn/bn_full.txt.gz says `1`. This counts how often each of the list's words
occurs in the corpora and writes the list back out in the usual form,

    word count

sorted by count, descending, ties in code-point order so a rebuild is
byte-identical. Every word of the input list is written, seen or not: a word
the corpora never use is still a word (chat verb forms like বানাইছি are in the
list on purpose), so each count has --floor added and an unseen word ends at
the floor, above the app's noise cut of 2 (WordlistDownloadManager.MIN_FREQUENCY).

Tokenizing is import_leipzig_ngrams.py's, so a word is counted exactly where
the n-gram lists would have counted it, and sources are weighted the same way:
`URL#3` adds each occurrence three times.

Usage:
    python3 scripts/import_leipzig_unigrams.py --script bengali \\
        --vocab data/bn/bn_full.txt.gz --out data/bn/bn_full_v2.txt.gz \\
        --keep-corpora /path/to/corpora \\
        https://downloads.wortschatz-leipzig.de/corpora/ben-bd_web_2017_1M.tar.gz#3 \\
        https://downloads.wortschatz-leipzig.de/corpora/ben_newscrawl_2017_1M.tar.gz

A source that names an existing file is read from disk instead of downloaded.
"""

import argparse
import gzip
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_leipzig_ngrams import (  # noqa: E402
    download,
    load_vocab,
    make_tokenizer,
    normalize_generic,
    parse_source,
    sentences_from_tarball,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Count a word list's words over Leipzig sentence corpora")
    parser.add_argument("sources", nargs="+", help="corpus tarball URLs or paths, optionally suffixed #weight")
    parser.add_argument("--vocab", required=True, help="the word list to give frequencies to")
    parser.add_argument("--out", required=True, help="the ranked list to write (gzip)")
    parser.add_argument("--script", default="latin", choices=("latin", "bengali", "generic"))
    parser.add_argument("--floor", type=int, default=2, help="added to every count (default: 2)")
    parser.add_argument("--keep-corpora", help="download into this directory and keep the tarballs")
    args = parser.parse_args()

    normalize = normalize_generic if args.script == "generic" else None
    words = load_vocab(Path(args.vocab), normalize)
    vocab = frozenset(words)
    print(f"Word list: {len(words)} words from {args.vocab}")
    tokenize = make_tokenizer(args.script, vocab)

    keep_dir = Path(args.keep_corpora) if args.keep_corpora else None
    if keep_dir:
        keep_dir.mkdir(parents=True, exist_ok=True)

    counts = Counter()
    n_sentences = 0
    n_tokens = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for location, weight in (parse_source(spec) for spec in args.sources):
            local = Path(location)
            if local.is_file():
                tarball, temporary = local, False
            else:
                tarball = (keep_dir or tmp_path) / local.name
                temporary = keep_dir is None
                if not tarball.is_file():
                    print(f"Downloading {location} ...")
                    download(location, tarball)
            print(f"Counting {tarball.name} (weight {weight}) ...")
            for sentence in sentences_from_tarball(tarball, tmp_path):
                n_sentences += 1
                for run in tokenize(sentence):
                    n_tokens += len(run)
                    for token in run:
                        counts[token] += weight
            if temporary:
                tarball.unlink()

    print(f"Processed {n_sentences} sentences, {n_tokens} listed tokens, {len(counts)} distinct words seen")
    ranked = sorted(((counts[w] + args.floor, w) for w in words), key=lambda p: (-p[0], p[1]))
    with gzip.open(args.out, "wt", encoding="utf-8") as out:
        for frequency, word in ranked:
            out.write(f"{word} {frequency}\n")
    unseen = sum(1 for w in words if w not in counts)
    print(f"Wrote {len(ranked)} words -> {args.out} ({unseen} never seen, at {args.floor})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""Build word bigram/trigram frequency lists from Leipzig Corpora Collection
sentence corpora, in the same format as the bn_rom n-gram files:

    <word1> <word2> <count>
    <word1> <word2> <word3> <count>

sorted by count, descending. Output is written to:

    data/<lang>/<prefix>_bigrams.txt.gz
    data/<lang>/<prefix>_trigrams.txt.gz

N-grams never cross sentence boundaries. Counts from multiple corpora are
summed. Tokenization is aimed at latin-script languages: text is lowercased,
curly apostrophes are normalized, and only tokens matching [a-z]+(?:'[a-z]+)*
(e.g. "don't") are kept; an out-of-vocabulary token breaks the n-gram window.

Usage:
    python3 scripts/import_leipzig_ngrams.py --lang en \
        https://downloads.wortschatz-leipzig.de/corpora/eng_news_2024_1M.tar.gz \
        https://downloads.wortschatz-leipzig.de/corpora/eng-com_web-public_2018_1M.tar.gz

    Options:
        --prefix        output filename prefix (default: same as --lang)
        --min-bigram    minimum count to keep a bigram (default: 5)
        --min-trigram   minimum count to keep a trigram (default: 5)
        --max-bigrams   keep at most N bigrams, 0 = unlimited (default: 0)
        --max-trigrams  keep at most N trigrams, 0 = unlimited (default: 0)
"""

import argparse
import gzip
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+)*")
MAX_TOKEN_LEN = 24


def download(url: str, dest: Path) -> None:
    """Download file using aria2c."""
    command = [
        "aria2c",
        "--console-log-level=warn",
        "--summary-interval=1",
        "-x", "16",
        "-s", "16",
        "--min-split-size=1M",
        "-d", str(dest.parent),
        "-o", str(dest.name),
        url,
    ]
    subprocess.run(command, check=True)


def sentences_from_tarball(tarball: Path, tmp_path: Path):
    """Extract the *-sentences.txt member and yield sentence strings."""
    with tarfile.open(tarball, "r:gz") as tar:
        member = None
        for m in tar.getmembers():
            if m.name.endswith("-sentences.txt"):
                member = m
                break
        if member is None:
            raise RuntimeError(f"no *-sentences.txt found inside {tarball.name}")
        tar.extract(member, tmp_path, filter="data")
        extracted = tmp_path / member.name

    with open(extracted, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t", 1)
            yield parts[1] if len(parts) == 2 else parts[0]
    extracted.unlink()


def tokenize(sentence: str):
    """Return token runs; an out-of-vocabulary token splits the run so
    n-grams never span it."""
    sentence = sentence.lower().replace("’", "'").replace("ʼ", "'")
    runs = []
    run = []
    pos = 0
    for m in TOKEN_RE.finditer(sentence):
        # Anything non-space between the previous token and this one (digits,
        # punctuation other than the apostrophe) breaks adjacency.
        gap = sentence[pos:m.start()]
        if gap.strip() and run:
            runs.append(run)
            run = []
        tok = m.group(0)
        if len(tok) <= MAX_TOKEN_LEN:
            run.append(tok)
        elif run:
            runs.append(run)
            run = []
        pos = m.end()
    if run:
        runs.append(run)
    return runs


def count_and_write(raw_path: Path, out_gz: Path, min_count: int, max_items: int, tmp_dir: Path) -> int:
    """sort | uniq -c the raw n-gram file (disk-based, low memory), apply the
    count threshold, sort by count descending, and write the gzip output."""
    counted = tmp_dir / (raw_path.name + ".counted")
    pipeline = (
        f"LC_ALL=C sort -S 1G -T {tmp_dir} {raw_path} | LC_ALL=C uniq -c | "
        f"awk -v min={min_count} '$1 >= min' | "
        f"LC_ALL=C sort -S 1G -T {tmp_dir} -k1,1nr > {counted}"
    )
    subprocess.run(["sh", "-c", pipeline], check=True)

    written = 0
    with open(counted, "r", encoding="utf-8") as inf, gzip.open(out_gz, "wt", encoding="utf-8") as outf:
        for line in inf:
            if max_items and written >= max_items:
                break
            parts = line.split()
            count, words = parts[0], parts[1:]
            outf.write(f"{' '.join(words)} {count}\n")
            written += 1
    counted.unlink()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build n-gram lists from Leipzig sentence corpora")
    parser.add_argument("urls", nargs="+", help="Leipzig corpus tarball URLs")
    parser.add_argument("--lang", required=True, help="target data/<lang> folder")
    parser.add_argument("--prefix", help="output filename prefix (default: --lang)")
    parser.add_argument("--min-bigram", type=int, default=5)
    parser.add_argument("--min-trigram", type=int, default=5)
    parser.add_argument("--max-bigrams", type=int, default=0)
    parser.add_argument("--max-trigrams", type=int, default=0)
    args = parser.parse_args()

    prefix = args.prefix or args.lang
    out_dir = DATA_DIR / args.lang
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_bi = tmp_path / "bigrams.raw"
        raw_tri = tmp_path / "trigrams.raw"
        n_sentences = 0
        n_tokens = 0

        with open(raw_bi, "w", encoding="utf-8") as bi_f, open(raw_tri, "w", encoding="utf-8") as tri_f:
            for url in args.urls:
                tarball = tmp_path / Path(url).name
                print(f"Downloading {url} ...")
                download(url, tarball)
                print(f"Extracting n-grams from {tarball.name} ...")
                for sentence in sentences_from_tarball(tarball, tmp_path):
                    n_sentences += 1
                    for run in tokenize(sentence):
                        n_tokens += len(run)
                        for i in range(len(run) - 1):
                            bi_f.write(f"{run[i]} {run[i + 1]}\n")
                        for i in range(len(run) - 2):
                            tri_f.write(f"{run[i]} {run[i + 1]} {run[i + 2]}\n")
                tarball.unlink()

        print(f"Processed {n_sentences} sentences, {n_tokens} tokens")

        bi_gz = out_dir / f"{prefix}_bigrams.txt.gz"
        tri_gz = out_dir / f"{prefix}_trigrams.txt.gz"

        print("Counting bigrams ...")
        n_bi = count_and_write(raw_bi, bi_gz, args.min_bigram, args.max_bigrams, tmp_path)
        print(f"Wrote {n_bi} bigrams -> {bi_gz}")

        print("Counting trigrams ...")
        n_tri = count_and_write(raw_tri, tri_gz, args.min_trigram, args.max_trigrams, tmp_path)
        print(f"Wrote {n_tri} trigrams -> {tri_gz}")


if __name__ == "__main__":
    main()

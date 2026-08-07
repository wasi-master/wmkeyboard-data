#!/usr/bin/env python3

"""Build word bigram/trigram frequency lists from Leipzig Corpora Collection
sentence corpora, in the same format as the bn_rom n-gram files:

    <word1> <word2> <count>
    <word1> <word2> <word3> <count>

sorted by count, descending. Output is written to:

    data/<lang>/<prefix>_bigrams.txt.gz
    data/<lang>/<prefix>_trigrams.txt.gz

N-grams never cross sentence boundaries, and within a sentence anything
non-space between two tokens (a digit, a comma, a danda) breaks the window too,
so a pair is only ever recorded for words that were genuinely adjacent.

Two tokenizers ship, chosen with --script:

  latin    (default) text is lowercased, curly apostrophes are normalized, and
           only tokens matching [a-z]+(?:'[a-z]+)* — e.g. "don't" — are kept.

  bengali  text is NFKC- then NFC-normalized and zero-width joiners are
           deleted, which is what data/<lang>/<lang>_full.txt.gz was built with;
           tokens are runs of Bengali letters and signs, structurally validated
           (see is_valid_bengali) so mis-segmented and mojibake fragments never
           reach the output.

Sources may be weighted. A corpus written `URL#3` contributes each of its
counts three times, which is how a register the keyboard actually has to
predict (web, conversation) is made to outrank one it merely borrows
vocabulary from (news, encyclopedia). Weighting matters because the app reads
only the *head* of these files — see NgramPackDownloadManager's caps — so which
corpus wins a tie decides what ships to the device.

A source that names an existing file is read from disk instead of downloaded,
so a corpus fetched once can be re-milled with different weights for free.

Usage:
    python3 scripts/import_leipzig_ngrams.py --lang en \
        https://downloads.wortschatz-leipzig.de/corpora/eng_news_2024_1M.tar.gz \
        https://downloads.wortschatz-leipzig.de/corpora/eng-com_web-public_2018_1M.tar.gz

    python3 scripts/import_leipzig_ngrams.py --lang bn --script bengali \
        --vocab data/bn/bn_full.txt.gz \
        https://downloads.wortschatz-leipzig.de/corpora/ben-bd_web_2017_1M.tar.gz#3 \
        https://downloads.wortschatz-leipzig.de/corpora/ben_newscrawl_2017_1M.tar.gz

    Options:
        --script        latin (default) or bengali
        --prefix        output filename prefix (default: same as --lang)
        --vocab         word list (gzip, `word count` lines); a token outside it
                        breaks the n-gram window
        --counter       disk (default) or memory; see below
        --min-bigram    minimum count to keep a bigram (default: 5)
        --min-trigram   minimum count to keep a trigram (default: 5)
        --max-bigrams   keep at most N bigrams, 0 = unlimited (default: 0)
        --max-trigrams  keep at most N trigrams, 0 = unlimited (default: 0)
        --keep-corpora  directory to download into and keep (default: temporary)

Two counting backends produce identical output:

  disk    (default) writes every n-gram occurrence to a scratch file and runs
          `sort | uniq -c` over it. Needs no particular vocabulary, but a few
          million sentences means several GB of scratch space.

  memory  needs --vocab, and uses it to turn each word into an id, each n-gram
          into one int64, and the whole corpus into a numpy array it sorts in
          place. Counts are exact, scratch space is nil and it is much the
          faster of the two; the cost is holding roughly 8 bytes per n-gram
          *occurrence* in RAM (a 5M-sentence corpus wants about 2 GB).
"""

import argparse
import gzip
import re
import subprocess
import sys
import tarfile
import tempfile
import unicodedata
from array import array
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

LATIN_TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+)*")
LATIN_MAX_TOKEN_LEN = 24

# ----------------------------------------------------------------------
# Bengali
# ----------------------------------------------------------------------
# The alphabet is the one data/bn/bn_full.txt.gz actually uses, which is the
# NFC form: U+09DC/U+09DD/U+09DF (ড় ঢ় য়) are Unicode composition exclusions, so
# NFC leaves them as base + U+09BC NUKTA and they never appear here. Bengali
# digits, the danda, currency and fraction signs are all deliberately outside
# the class, so they break the window like any other punctuation.
BENGALI_BASE_RANGES = (
    (0x0985, 0x098C),  # অ ঌ  independent vowels
    (0x098F, 0x0990),  # এ ঐ
    (0x0993, 0x09A8),  # ও ঔ, ক–ন
    (0x09AA, 0x09B0),  # প–র
    (0x09B2, 0x09B2),  # ল
    (0x09B6, 0x09B9),  # শ ষ স হ
    (0x09CE, 0x09CE),  # ৎ khanda ta
)
BENGALI_MARK_RANGES = (
    (0x0981, 0x0983),  # ঁ ং ঃ
    (0x09BC, 0x09BC),  # ় nukta
    (0x09BE, 0x09C4),  # া ি ী ু ূ ৃ ৄ
    (0x09C7, 0x09C8),  # ে ৈ
    (0x09CB, 0x09CD),  # ো ৌ ্
)

BENGALI_BASE = frozenset(
    chr(c) for lo, hi in BENGALI_BASE_RANGES for c in range(lo, hi + 1)
)
BENGALI_VOWEL_SIGN = frozenset(
    chr(c)
    for lo, hi in ((0x09BE, 0x09C4), (0x09C7, 0x09C8), (0x09CB, 0x09CC))
    for c in range(lo, hi + 1)
)
BENGALI_NUKTA = "\u09BC"
BENGALI_VIRAMA = "\u09CD"
# The only three letters a nukta legitimately attaches to. Anything else
# carrying one is mojibake or a stray combining mark.
BENGALI_NUKTA_BASES = frozenset("\u09A1\u09A2\u09AF")  # ড ঢ য

BENGALI_TOKEN_RE = re.compile(
    "["
    + "".join(
        f"\\u{lo:04X}-\\u{hi:04X}"
        for lo, hi in BENGALI_BASE_RANGES + BENGALI_MARK_RANGES
    )
    + "]+"
)
# Longest word in bn_full is 37 characters and its 99.99th percentile is 24;
# past 32 a "word" is two words a crawler ran together.
BENGALI_MAX_TOKEN_LEN = 32

# Deleted rather than treated as separators: a ZWNJ or ZWJ sits *inside* a word,
# steering how a conjunct renders, and breaking on one would file two fragments
# as real words. bn_full contains none, so dropping them is also what makes a
# token comparable to a dictionary entry.
ZERO_WIDTH = str.maketrans("", "", "\u200b\u200c\u200d\ufeff\u00ad")


def is_valid_bengali(token: str) -> bool:
    """Reject the ways a Bengali token comes out malformed.

    Measured against all 451,348 words of bn_full: these rules refuse 0.03% of
    them, and every refusal is a genuinely broken entry (অতিারকা, উঁচুু, এই্্্).
    """
    if not token or len(token) > BENGALI_MAX_TOKEN_LEN:
        return False
    # A word cannot open on a combining mark; one that appears to is the tail of
    # a word whose first letters were lost.
    if token[0] not in BENGALI_BASE:
        return False
    previous = ""
    for char in token:
        if char == BENGALI_NUKTA and previous not in BENGALI_NUKTA_BASES:
            return False
        if char == BENGALI_VIRAMA and previous == BENGALI_VIRAMA:
            return False
        if char in BENGALI_VOWEL_SIGN and previous == BENGALI_VIRAMA:
            return False
        if char in BENGALI_VOWEL_SIGN and previous in BENGALI_VOWEL_SIGN:
            return False
        previous = char
    return True


def normalize_bengali(sentence: str) -> str:
    sentence = sentence.translate(ZERO_WIDTH)
    if not unicodedata.is_normalized("NFKC", sentence):
        sentence = unicodedata.normalize("NFKC", sentence)
    if not unicodedata.is_normalized("NFC", sentence):
        sentence = unicodedata.normalize("NFC", sentence)
    return sentence


class Tokenizer:
    """Splits a sentence into runs of adjacent words.

    A run is a maximal stretch of words with nothing but spaces between them:
    n-grams are read off within a run and never across the break, so a rejected
    token, a digit or any punctuation ends the run it interrupts.
    """

    def __init__(self, pattern, max_length, prepare=None, accept=None, vocab=None):
        self.pattern = pattern
        self.max_length = max_length
        self.prepare = prepare
        self.accept = accept
        self.vocab = vocab

    def __call__(self, sentence: str):
        if self.prepare is not None:
            sentence = self.prepare(sentence)
        runs = []
        run = []
        pos = 0
        for match in self.pattern.finditer(sentence):
            if sentence[pos:match.start()].strip() and run:
                runs.append(run)
                run = []
            token = match.group(0)
            ok = len(token) <= self.max_length
            if ok and self.accept is not None:
                ok = self.accept(token)
            if ok and self.vocab is not None:
                ok = token in self.vocab
            if ok:
                run.append(token)
            elif run:
                runs.append(run)
                run = []
            pos = match.end()
        if run:
            runs.append(run)
        return runs


def prepare_latin(sentence: str) -> str:
    return sentence.lower().replace("\u2019", "'").replace("\u02BC", "'")


def make_tokenizer(script: str, vocab):
    if script == "latin":
        return Tokenizer(LATIN_TOKEN_RE, LATIN_MAX_TOKEN_LEN, prepare_latin, None, vocab)
    if script == "bengali":
        return Tokenizer(
            BENGALI_TOKEN_RE,
            BENGALI_MAX_TOKEN_LEN,
            normalize_bengali,
            is_valid_bengali,
            vocab,
        )
    raise ValueError(f"unknown --script {script}")


def load_vocab(path: Path):
    """The accepted words, sorted so a word's id is reproducible across runs."""
    opener = gzip.open if path.suffix == ".gz" else open
    words = set()
    with opener(path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            words.add(line.rsplit(" ", 1)[0])
    return sorted(words)


def download(url: str, dest: Path) -> None:
    """Download file using aria2c."""
    command = [
        "aria2c",
        "--console-log-level=warn",
        "--summary-interval=1",
        "-x", "16",
        "-s", "16",
        "--min-split-size=1M",
        "--continue=true",
        "--auto-file-renaming=false",
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


def parse_source(spec: str):
    """`URL#3` or `path/to.tar.gz` -> (location, weight)."""
    location, _, weight = spec.rpartition("#")
    if not location:
        return spec, 1
    try:
        return location, int(weight)
    except ValueError:
        return spec, 1


class DiskSink:
    """Streams every n-gram occurrence to a scratch file per weight group and
    lets `sort | uniq -c` do the counting."""

    def __init__(self, tmp_dir: Path):
        self.tmp_dir = tmp_dir
        self.bigram_kv = []
        self.trigram_kv = []
        self._weight = None
        self._bi = None
        self._tri = None

    def begin_group(self, weight: int) -> None:
        self._weight = weight
        self._bi = open(self.tmp_dir / f"bigrams.w{weight}.raw", "w", encoding="utf-8")
        self._tri = open(self.tmp_dir / f"trigrams.w{weight}.raw", "w", encoding="utf-8")

    def add(self, run) -> None:
        for i in range(len(run) - 1):
            self._bi.write(f"{run[i]} {run[i + 1]}\n")
        for i in range(len(run) - 2):
            self._tri.write(f"{run[i]} {run[i + 1]} {run[i + 2]}\n")

    def end_group(self) -> None:
        bi_path = Path(self._bi.name)
        tri_path = Path(self._tri.name)
        self._bi.close()
        self._tri.close()
        print(f"Counting weight group x{self._weight} ...")
        self.bigram_kv.append(count_weighted(bi_path, self._weight, self.tmp_dir))
        self.trigram_kv.append(count_weighted(tri_path, self._weight, self.tmp_dir))

    def write_bigrams(self, out_gz, min_count, max_items):
        return combine(self.bigram_kv, out_gz, min_count, max_items, self.tmp_dir)

    def write_trigrams(self, out_gz, min_count, max_items):
        return combine(self.trigram_kv, out_gz, min_count, max_items, self.tmp_dir)


class MemorySink:
    """Counts n-grams as int64 word-id keys, sorted in place by numpy.

    A word is its index in the vocabulary and an n-gram is those indices in
    base len(vocab), so a trigram over the 451k-word Bengali list is one number
    below 2^57 and the whole corpus is one flat array. Counting is then a sort
    and a run-length pass — exact, and with no scratch file to find room for.
    """

    def __init__(self, words):
        self.words = words
        self.ids = {word: index for index, word in enumerate(words)}
        self.radix = len(words)
        self.bigrams = {}
        self.trigrams = {}
        self._weight = None

    def begin_group(self, weight: int) -> None:
        self._weight = weight
        self.bigrams.setdefault(weight, array("q"))
        self.trigrams.setdefault(weight, array("q"))

    def add(self, run) -> None:
        ids = [self.ids[word] for word in run]
        radix = self.radix
        if len(ids) >= 2:
            self.bigrams[self._weight].extend(
                a * radix + b for a, b in zip(ids, ids[1:])
            )
        if len(ids) >= 3:
            self.trigrams[self._weight].extend(
                (a * radix + b) * radix + c for a, b, c in zip(ids, ids[1:], ids[2:])
            )

    def end_group(self) -> None:
        pass

    @staticmethod
    def _run_starts(keys):
        """Index of the first element of each equal run in a sorted array."""
        import numpy as np

        if keys.size == 0:
            return np.zeros(0, dtype=np.intp)
        change = np.empty(keys.size, dtype=bool)
        change[0] = True
        np.not_equal(keys[1:], keys[:-1], out=change[1:])
        return np.flatnonzero(change)

    def _collapse(self, groups, min_count, max_items):
        import numpy as np

        key_parts = []
        count_parts = []
        for weight in sorted(groups):
            keys = np.frombuffer(groups.pop(weight), dtype=np.int64).copy()
            keys.sort()
            starts = self._run_starts(keys)
            lengths = np.diff(np.append(starts, keys.size)).astype(np.int64)
            key_parts.append(keys[starts])
            count_parts.append(lengths * weight)
            del keys, starts, lengths

        keys = np.concatenate(key_parts)
        counts = np.concatenate(count_parts)
        del key_parts, count_parts
        order = np.argsort(keys, kind="stable")
        keys = keys[order]
        counts = counts[order]
        del order
        starts = self._run_starts(keys)
        unique = keys[starts]
        summed = (
            np.add.reduceat(counts, starts)
            if starts.size
            else np.zeros(0, dtype=np.int64)
        )
        del keys, counts, starts

        keep = summed >= min_count
        unique = unique[keep]
        summed = summed[keep]
        # Count descending, then key ascending: ties resolve the same way on
        # every run, so rebuilding the list produces an identical file.
        order = np.lexsort((unique, -summed))
        if max_items:
            order = order[:max_items]
        return unique[order], summed[order]

    def _write(self, groups, out_gz: Path, arity: int, min_count: int, max_items: int) -> int:
        keys, counts = self._collapse(groups, min_count, max_items)
        radix = self.radix
        words = self.words
        written = 0
        with gzip.open(out_gz, "wt", encoding="utf-8") as outf:
            for key, count in zip(keys.tolist(), counts.tolist()):
                parts = []
                for _ in range(arity):
                    key, index = divmod(key, radix)
                    parts.append(words[index])
                parts.reverse()
                outf.write(f"{' '.join(parts)} {count}\n")
                written += 1
        return written

    def write_bigrams(self, out_gz, min_count, max_items):
        return self._write(self.bigrams, out_gz, 2, min_count, max_items)

    def write_trigrams(self, out_gz, min_count, max_items):
        return self._write(self.trigrams, out_gz, 3, min_count, max_items)


def count_weighted(raw_path: Path, weight: int, tmp_dir: Path) -> Path:
    """Collapse one weight group's raw n-grams to `ngram<TAB>weighted count`,
    ordered by n-gram, ready for the merge in [combine]."""
    out = raw_path.with_suffix(".kv")
    pipeline = (
        f"LC_ALL=C sort -S 1G -T {tmp_dir} {raw_path} | LC_ALL=C uniq -c | "
        f"awk -v w={weight} "
        "'{ c = $1 * w; sub(/^ *[0-9]+ /, \"\"); print $0 \"\\t\" c }' "
        f"> {out}"
    )
    subprocess.run(["sh", "-c", pipeline], check=True)
    raw_path.unlink()
    return out


def combine(kv_paths, out_gz: Path, min_count: int, max_items: int, tmp_dir: Path) -> int:
    """Sum the weight groups, drop what falls under the threshold, and write the
    count-descending gzip list.

    `sort -m` is safe here without re-sorting: every key holds only letters and
    single spaces, and the TAB that ends it is byte 0x09 — below every byte a
    key can contain — so ordering `key<TAB>count` lines on the first field
    reproduces the whole-line order the group files were built in.
    """
    counted = tmp_dir / (out_gz.name + ".counted")
    inputs = " ".join(str(p) for p in kv_paths)
    merge = (
        f"LC_ALL=C sort -m -t '\t' -k1,1 {inputs} | "
        "awk -F'\\t' -v min=" + str(min_count) + " "
        "'{ if ($1 != key) { if (key != \"\" && sum >= min) print sum \"\\t\" key; "
        "key = $1; sum = 0 } sum += $2 } "
        "END { if (key != \"\" && sum >= min) print sum \"\\t\" key }' | "
        f"LC_ALL=C sort -S 1G -T {tmp_dir} -k1,1nr > {counted}"
    )
    subprocess.run(["sh", "-c", merge], check=True)

    written = 0
    with open(counted, "r", encoding="utf-8") as inf, gzip.open(out_gz, "wt", encoding="utf-8") as outf:
        for line in inf:
            if max_items and written >= max_items:
                break
            count, _, ngram = line.rstrip("\n").partition("\t")
            outf.write(f"{ngram} {count}\n")
            written += 1
    counted.unlink()
    for path in kv_paths:
        path.unlink()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build n-gram lists from Leipzig sentence corpora")
    parser.add_argument("sources", nargs="+", help="corpus tarball URLs or paths, optionally suffixed #weight")
    parser.add_argument("--lang", required=True, help="target data/<lang> folder")
    parser.add_argument("--script", default="latin", choices=("latin", "bengali"))
    parser.add_argument("--prefix", help="output filename prefix (default: --lang)")
    parser.add_argument("--vocab", help="word list a token must appear in")
    parser.add_argument("--counter", default="disk", choices=("disk", "memory"))
    parser.add_argument("--min-bigram", type=int, default=5)
    parser.add_argument("--min-trigram", type=int, default=5)
    parser.add_argument("--max-bigrams", type=int, default=0)
    parser.add_argument("--max-trigrams", type=int, default=0)
    parser.add_argument("--keep-corpora", help="download into this directory and keep the tarballs")
    args = parser.parse_args()

    prefix = args.prefix or args.lang
    out_dir = DATA_DIR / args.lang
    out_dir.mkdir(parents=True, exist_ok=True)

    words = None
    vocab = None
    if args.vocab:
        words = load_vocab(Path(args.vocab))
        vocab = frozenset(words)
        print(f"Vocabulary gate: {len(words)} words from {args.vocab}")
    if args.counter == "memory" and words is None:
        parser.error("--counter memory needs --vocab to map words to ids")
    tokenize = make_tokenizer(args.script, vocab)

    sources = [parse_source(spec) for spec in args.sources]
    groups = sorted({weight for _, weight in sources})
    print("Weight groups: " + ", ".join(f"x{w}" for w in groups))

    keep_dir = Path(args.keep_corpora) if args.keep_corpora else None
    if keep_dir:
        keep_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sink = MemorySink(words) if args.counter == "memory" else DiskSink(tmp_path)
        n_sentences = 0
        n_tokens = 0

        for weight in groups:
            sink.begin_group(weight)
            for location, source_weight in sources:
                if source_weight != weight:
                    continue
                local = Path(location)
                if local.is_file():
                    tarball = local
                    temporary = False
                else:
                    tarball = (keep_dir or tmp_path) / Path(location).name
                    temporary = keep_dir is None
                    if not tarball.is_file():
                        print(f"Downloading {location} ...")
                        download(location, tarball)
                print(f"Extracting n-grams from {tarball.name} (weight {weight}) ...")
                for sentence in sentences_from_tarball(tarball, tmp_path):
                    n_sentences += 1
                    for run in tokenize(sentence):
                        n_tokens += len(run)
                        sink.add(run)
                if temporary:
                    tarball.unlink()
            sink.end_group()

        print(f"Processed {n_sentences} sentences, {n_tokens} tokens")

        bi_gz = out_dir / f"{prefix}_bigrams.txt.gz"
        tri_gz = out_dir / f"{prefix}_trigrams.txt.gz"

        print("Merging bigrams ...")
        n_bi = sink.write_bigrams(bi_gz, args.min_bigram, args.max_bigrams)
        print(f"Wrote {n_bi} bigrams -> {bi_gz}")

        print("Merging trigrams ...")
        n_tri = sink.write_trigrams(tri_gz, args.min_trigram, args.max_trigrams)
        print(f"Wrote {n_tri} trigrams -> {tri_gz}")


if __name__ == "__main__":
    main()

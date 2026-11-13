#!/usr/bin/env python3

"""Build the Hinglish (romanized Hindi) bigram and trigram lists:

    data/hi/hi_rom_bigrams.txt.gz    word word count
    data/hi/hi_rom_trigrams.txt.gz   word word word count

Sorted by count, descending, and cut at the app's read caps (150,000 and
75,000 rows), so the published size is what a phone downloads.

The text is MADLAD-400's `hi_Latn` clean split (ODC-BY): about 26,700 web
documents and 29 million words of Hindi written in Latin letters, mostly
blogs and how-to pages ("Google chrome me password kaise lagaye"). That is
the register people type Hinglish in, English words and all, which is why
English is not filtered out: a pair like `office ja` is exactly what the
keyboard should predict.

A word is kept when the Hinglish list (`hi_rom_v2`) or the English list
(`en_full`, first 200,000 words) knows it, since the keyboard can only offer
a word its dictionaries hold; any other word ends the n-gram rather than
joining it. Sentences end at . ! ? | and line breaks, and pairs never cross
one.

The crawl carries keyword-stuffed pages ("size matters" 122,000 times in 564
pages, "barn door hardware" pages in English), so three filters run first:

- a document needs at least 10% of its words to be common Hindi function
  words (hai, ke, ki, aur, nahi...), which drops the English pages;
- a document whose most repeated pair of content words makes up 3% or more
  of its pairs, 20 times or more, is stuffed and dropped whole;
- a document with three or more explicit words (EXPLICIT: the sex-story
  sites are a large share of Hinglish on the web) is dropped, and no
  n-gram naming one is written, whatever page it came from;
- inside a document an n-gram counts three times at most, and lines repeated
  word for word count once, which drops site boilerplate.

    curl -LO https://huggingface.co/datasets/allenai/MADLAD-400/resolve/main/data/hi_Latn/hi_Latn_clean_0000.jsonl.gz
    python3 -I scripts/build_hi_rom_ngrams.py hi_Latn_clean_0000.jsonl.gz
"""

import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
MAX_BIGRAMS = 150_000
MAX_TRIGRAMS = 75_000
ENGLISH_WORDS = 200_000
FLOOR = 3
PER_DOC = 3
MIN_HINDI = 0.10
STUFFED_SHARE = 0.03
STUFFED_COUNT = 20

EXPLICIT = frozenset(
    "lund lun lauda lawda loda lode lavde chut choot chuth chud chudai chudi chudwa chudwane chudwaya chudne "
    "chodo chod chodna chodne choda chodi chodta chodte chodu chodkar bhosda bhosdi bhosde bhosdike gand gaand "
    "gandu randi randee chuchi chuchiyan chuchiya chuche boobs boob nangi nanga sex sexy porn porno xxx "
    "penis vagina viagra pussy dick cock fuck fucking fucked madarchod behenchod bhenchod bsdk muth jhant "
    "jhaant suhagraat chikni".split()
)

HINDI = frozenset(
    "hai hain ke ki ka ko se me mein men aur ye yah kya nahi nahin bhi kar ho tha thi the "
    "ek apne aap liye jata hota karne raha rahe rahi gaya hum tum main mujhe".split()
)

SENTENCE = re.compile(r"[.!?|।\n:;()\[\]\"“”]+")
TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?|\S+")
WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")


def read_list(path, limit=None):
    words = set()
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        for index, line in enumerate(lines):
            if limit and index >= limit:
                break
            word = line.split(" ", 1)[0].strip().lower()
            if word:
                words.add(word)
    return words


def documents(path):
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as lines:
        for line in lines:
            text = json.loads(line).get("text") or ""
            # MADLAD prefixes each document with its quality signals, then BODY=.
            _, found, body = text.partition("BODY=")
            text = body if found else text
            # MADLAD keeps its line breaks as a literal backslash-n.
            yield text.replace("\\n", "\n").replace("\\t", " ").replace('\\"', '"').replace("\\", " ")


def main():
    vocab = read_list(DATA / "hi" / "hi_rom_v2.txt.gz") | read_list(DATA / "en" / "en_full.txt.gz", ENGLISH_WORDS)
    bigrams = Counter()
    trigrams = Counter()
    seen_lines = set()
    docs = dropped = tokens = 0
    for path in sys.argv[1:]:
        for doc in documents(path):
            docs += 1
            runs = []
            for line in doc.lower().split("\n"):
                line = line.strip()
                if not line or hash(line) in seen_lines:
                    continue
                seen_lines.add(hash(line))
                for sentence in SENTENCE.split(line):
                    run = []
                    for token in TOKEN.findall(sentence):
                        if WORD.fullmatch(token) and token in vocab:
                            run.append(token)
                            continue
                        if run:
                            runs.append(run)
                        run = []
                    if run:
                        runs.append(run)
            doc_bi = Counter()
            doc_tri = Counter()
            for run in runs:
                count_run(run, doc_bi, doc_tri)
            words = sum(len(run) for run in runs)
            explicit = sum(w in EXPLICIT for run in runs for w in run)
            hindi = sum(w in HINDI for run in runs for w in run)
            if not words or hindi < MIN_HINDI * words or explicit >= 3 or stuffed(doc_bi):
                dropped += 1
                continue
            tokens += words
            for key, n in doc_bi.items():
                bigrams[key] += min(n, PER_DOC)
            for key, n in doc_tri.items():
                trigrams[key] += min(n, PER_DOC)
    out = DATA / "hi"
    n_bi = write(out / "hi_rom_bigrams.txt.gz", bigrams, MAX_BIGRAMS)
    n_tri = write(out / "hi_rom_trigrams.txt.gz", trigrams, MAX_TRIGRAMS)
    print(f"{docs} documents, {dropped} dropped; {tokens} words counted; "
          f"{n_bi} bigrams and {n_tri} trigrams written")


def stuffed(doc_bi):
    total = sum(doc_bi.values())
    content = [n for (a, b), n in doc_bi.items() if a not in HINDI and b not in HINDI]
    top = max(content, default=0)
    return top >= STUFFED_COUNT and top >= STUFFED_SHARE * total


def count_run(run, bigrams, trigrams):
    for a, b in zip(run, run[1:]):
        bigrams[a, b] += 1
    for a, b, c in zip(run, run[1:], run[2:]):
        trigrams[a, b, c] += 1


def write(path, counts, cap):
    rows = sorted(((n, key) for key, n in counts.items() if n >= FLOOR and not EXPLICIT.intersection(key)), key=lambda row: (-row[0], row[1]))[:cap]
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as packed:
        for n, key in rows:
            packed.write((" ".join(key) + f" {n}\n").encode("utf-8"))
    return len(rows)


if __name__ == "__main__":
    main()

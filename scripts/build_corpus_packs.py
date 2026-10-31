#!/usr/bin/env python3

"""Build a word list and bigram/trigram lists for a language from open web
corpora, for languages whose lists came from a small Wikipedia or Tatoeba count:

    data/<folder>/<folder>_full_v2.txt.gz      word count
    data/<folder>/<folder>_bigrams[_v2].txt.gz word word count
    data/<folder>/<folder>_trigrams[_v2].txt.gz word word word count

Each sorted by count, descending. A list that was already published keeps its
file and the rebuild takes a `_v2` name, because released apps fetch the old one.
Sources are read in the order scripts/corpus_packs.json gives until the language
reaches its token budget:

  s:<dir>     AI4Bharat Sangraha, verified/<dir> (CC BY 4.0)
  h:<config>  HPLT 2.0 cleaned (CC0)
  m:<code>    MADLAD-400 clean (ODC-BY)
  w:<wiki>    a Wikipedia articles dump (CC BY-SA 4.0)
  t:<iso3>    Tatoeba sentences (CC BY 2.0 FR), weighted x3 and always read:
              it is the one register here close to people talking

Nothing is kept on disk: a shard is downloaded, read and deleted.

Counting is a single pass. A word becomes an id as it is first seen and an
n-gram becomes one int64, so a corpus is two flat arrays that numpy sorts and
run-length counts at the end, as in import_leipzig_ngrams.py. Deciding which
words are real happens after that, once their counts are known; dropping every
n-gram that names a rejected word gives the same result as having broken the
window at that word.

A word the language's existing list already has is always kept. A word only the
corpus has must be in the language's script, reach a floor that grows with the
corpus, and not look borrowed: web text in a small language is full of its
neighbours' languages, so a word the reference lists know (English, French,
Hindi, Russian...) is dropped unless this corpus uses it at least 0.3 times as
often as that language does, and that goes for the old list's words too, since
it counted the same kind of text. Whole documents are dropped when they read as Hindi
or Bengali (a Dogri or Meitei crawl has plenty) or when they are Zawgyi Burmese,
and lines repeated word for word count once, which removes boilerplate.

Thai, Lao, Khmer and Burmese are cut into words by wm-engine's segmenter, the
same LSTM the keyboard reads context with, so that the keys match. Build it with
`cargo build --release --example segment_lines` in WMKeyboard/native/wm-engine
and pass the binary as --segmenter.

    python3 scripts/build_corpus_packs.py --only mai,sa --work /tmp/packs --jobs 3
"""

import argparse
import bz2
import gzip
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from array import array
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONFIG = Path(__file__).resolve().parent / "corpus_packs.json"

HF = "https://huggingface.co/datasets"
RADIX_BITS = 21
MAX_IDS = (1 << RADIX_BITS) - 1
MAX_WORD = 32
TOKEN_BUDGET = 30_000_000
SEGMENTED_BUDGET = 8_000_000
MIN_TOKENS = 100_000
KEEP_LIST_ABOVE = 300_000
MAX_LIST = 500_000
MAX_BIGRAMS = 150_000
MAX_TRIGRAMS = 75_000
MAX_SHORT_REPEATS = 100
MIN_FREE_BYTES = 3 << 29
SEGMENTED = {"THAI", "LAO", "KHMER", "MYANMAR"}
KEEP_COMPAT = {"THAI", "LAO", "TIBETAN"}  # NFKC would split sara am and Tibetan vowels

REFERENCES = {
    "LATIN": ["en", "fr", "es", "pt", "de", "id"],
    "CYRILLIC": ["ru"],
    "ARABIC": ["ar", "fa", "ur"],
    "DEVANAGARI": ["hi"],
    "BENGALI": ["bn"],
    "MYANMAR": ["my"],
}
# Function words that are common in the language named, and rare in its smaller
# neighbours: at 3% of a document's words, the document is in the language named.
TELLS = {
    "DEVANAGARI": frozenset("है हैं और की का हो इस".split()),
    "BENGALI": frozenset("এবং করে হয় এই থেকে".split()),
}
TELL_EXEMPT = {"hi", "mr", "ne", "bn", "as", "new", "sa"}
MOJIBAKE = re.compile("[\u00c3\u00c5\u00c4][\u0080-\u00bf]")
# Letters typed with the keyboard to hand: Latin lookalikes inside Cyrillic words
# and the other way round. Only ever applied next to a letter of the real script.
LATIN_IN_CYRILLIC = dict(zip("aAcCeEoOpPxXyKkMHTB", "\u0430\u0410\u0441\u0421\u0435\u0415\u043e\u041e\u0440\u0420\u0445\u0425\u0443\u041a\u043a\u041c\u041d\u0422\u0412"))
CYRILLIC_IN_LATIN = dict(zip("\u0430\u0435\u0456\u043e\u0440\u0441\u0445\u0443\u0410\u0415\u0406\u041e\u0420\u0421\u0425", "aeiopcxyAEIOPCX"))
LOOKALIKES = {
    "mn": {"r": "\u0433", "b": "\u044c", "n": "\u043f", "m": "\u0442"},
    "cv": dict(zip("\u0103\u0115\u00e7\u00ff\u0102\u0114\u00c7\u0178", "\u04d1\u04d7\u04ab\u04f3\u04d0\u04d6\u04aa\u04f2")),
    "os": dict(zip("\u00e6\u00c6\u0153\u0152", "\u04d5\u04d4\u04d5\u04d4")),
    "kv": dict(zip("\u00f6\u00d6iI", "\u04e7\u04e6\u0456\u0406")),
    "koi": dict(zip("\u00f6\u00d6iI", "\u04e7\u04e6\u0456\u0406")),
}
# Palochka, which Caucasian web text writes with whatever looks like it.
PALOCHKA_LANGUAGES = {"ady", "kbd", "av", "lez", "inh", "ce", "tab", "lbe", "dar", "kum"}
PALOCHKA = dict.fromkeys("Il1|\u0399\u0406\u0456", "\u04cf")
ZAWGYI = re.compile("(?:^|\\s)\u1031|[\u1060-\u1097]")

WIKI_DROP = [
    re.compile(r"<(ref|gallery|math|code|pre|timeline|syntaxhighlight)\b.*?</\1>", re.S),
    re.compile(r"<!--.*?-->", re.S),
    re.compile(r"\{\|.*?\|\}", re.S),
    re.compile(r"\[\[[^\]|:]{1,30}:[^\[\]]*(?:\[\[[^\]]*\]\][^\[\]]*)*\]\]"),
    re.compile(r"\{\{[^{}]*\}\}"),
    re.compile(r"\{\{[^{}]*\}\}"),
    re.compile(r"\{\{[^{}]*\}\}"),
    re.compile(r"<[^>]{1,200}>"),
    re.compile(r"^[=*#:;|!{}].*$", re.M),
]
WIKI_LINK = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
WIKI_PAGE = re.compile(r"<ns>(\d+)</ns>.*?<text\b[^>]*>(.*?)</text>", re.S)


def log(message):
    print(time.strftime("%H:%M:%S"), message, flush=True)


def fetch(url, dest):
    """Download [url] to [dest]; False when it does not exist."""
    while shutil.disk_usage(dest.parent).free < MIN_FREE_BYTES:
        log("waiting for disk space")
        time.sleep(60)
    for attempt in range(8):
        done = subprocess.run(
            ["curl", "-sSL", "--fail", "-C", "-", "--retry", "2", "-o", str(dest), "-w", "%{http_code}", url],
            capture_output=True, text=True,
        )
        code = done.stdout.strip()
        if done.returncode == 0:
            return True
        if code in ("404", "401", "403"):
            dest.unlink(missing_ok=True)
            return False
        if code == "416":  # already whole, from an earlier attempt
            return True
        time.sleep(30 * (attempt + 1))
    dest.unlink(missing_ok=True)
    return False


def parquet_texts(path):
    for batch in pq.ParquetFile(path).iter_batches(batch_size=256, columns=["text"]):
        for text in batch.column(0).to_pylist():
            if text:
                yield text


def sangraha(name, tmp):
    for index in range(200):
        shard = tmp / f"s{index}.parquet"
        if not fetch(f"{HF}/ai4bharat/sangraha/resolve/main/verified/{name}/data-{index}.parquet", shard):
            return
        yield from parquet_texts(shard)
        shard.unlink()


def hplt(spec, tmp):
    config, _, shards = spec.partition("#")
    total = int(shards or 1)
    for index in range(total):
        shard = tmp / f"h{index}.parquet"
        if not fetch(f"{HF}/HPLT/HPLT2.0_cleaned/resolve/main/{config}/train-{index:05d}-of-{total:05d}.parquet", shard):
            return
        yield from parquet_texts(shard)
        shard.unlink()


def madlad(code, tmp):
    for index in range(10000):
        shard = tmp / f"m{index}.jsonl.gz"
        if not fetch(f"{HF}/allenai/MADLAD-400/resolve/main/data/{code}/{code}_clean_{index:04d}.jsonl.gz", shard):
            return
        with gzip.open(shard, "rt", encoding="utf-8", errors="ignore") as lines:
            for line in lines:
                text = json.loads(line).get("text")
                if text:
                    # MADLAD keeps its line breaks as a literal backslash-n.
                    yield text.replace("\\n", "\n").replace("\\t", " ").replace('\\"', '"').replace("\\", " ")
        shard.unlink()


def strip_wikitext(text):
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&")
    text = text.replace("&nbsp;", " ")
    for pattern in WIKI_DROP:
        text = pattern.sub("\n", text)
    return WIKI_LINK.sub(r"\1", text).replace("'''", "").replace("''", "")


def wikipedia(wiki, tmp):
    dump = tmp / "wiki.xml.bz2"
    url = f"https://dumps.wikimedia.org/{wiki}wiki/latest/{wiki}wiki-latest-pages-articles.xml.bz2"
    if not fetch(url, dump):
        return
    with bz2.open(dump, "rt", encoding="utf-8", errors="ignore") as xml:
        buffer = ""
        while True:
            chunk = xml.read(1 << 22)
            if not chunk:
                break
            buffer += chunk
            end = 0
            for match in WIKI_PAGE.finditer(buffer):
                end = match.end()
                # Articles only: Module: pages are Lua, and "end if then local"
                # would top a small wiki's counts.
                body = match.group(2)
                if match.group(1) == "0" and not body.lstrip().startswith("#"):
                    yield strip_wikitext(body)
            buffer = buffer[end:]
    dump.unlink()


def tatoeba(iso3, tmp):
    dump = tmp / "tatoeba.tsv.bz2"
    url = f"https://downloads.tatoeba.org/exports/per_language/{iso3}/{iso3}_sentences.tsv.bz2"
    if not fetch(url, dump):
        return
    with bz2.open(dump, "rt", encoding="utf-8", errors="ignore") as lines:
        for line in lines:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                yield parts[2]
    dump.unlink()


READERS = {"s": sangraha, "h": hplt, "m": madlad, "w": wikipedia, "t": tatoeba}


def script_of(char):
    try:
        return unicodedata.name(char).split()[0]
    except ValueError:
        return ""


def read_list(path):
    """A `word count` list as written, in file order."""
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as lines:
        for line in lines:
            word, _, count = line.strip().rpartition(" ")
            if word and count.isdigit():
                yield word, int(count)


def dominant_script(words):
    tally = {}
    for word in words:
        for char in word:
            if unicodedata.category(char)[0] == "L":
                name = script_of(char)
                tally[name] = tally.get(name, 0) + 1
    return max(tally, key=tally.get) if tally else None


def lookalike_fixer(script, folder):
    """Rewrites a foreign lookalike letter wherever it touches a real letter."""
    if script == "CYRILLIC":
        table = {**LATIN_IN_CYRILLIC, **LOOKALIKES.get(folder, {})}
        if folder in PALOCHKA_LANGUAGES:
            table.update(PALOCHKA)
        real = "\u0400-\u052f"
    elif script == "LATIN":
        table = CYRILLIC_IN_LATIN
        real = "A-Za-z\u00c0-\u024f"
    else:
        return None
    letters = "".join(re.escape(c) for c in table)
    pattern = re.compile(f"(?<=[{real}])[{letters}]+|[{letters}]+(?=[{real}])")

    def fix(text):
        for _ in range(2):
            text = pattern.sub(lambda m: "".join(table[c] for c in m.group()), text)
        return text

    return fix


class Normalizer:
    def __init__(self, script, zwnj, folder="", okina=False):
        self.fix = lookalike_fixer(script, folder)
        self.form = "NFC" if script in KEEP_COMPAT else None
        drop = "\u200b\u200d\u200e\u200f\u202a\u202b\u202c\u202d\u202e\ufeff\u00ad" + ("" if zwnj else "\u200c")
        glottal = "\u02bb" if okina else "'"
        # A tsheg ends a syllable, and the keyboard reads context by syllable.
        spaces = {"\u0f0b": " ", "\u0f0c": " "} if script == "TIBETAN" else {}
        self.table = str.maketrans({**{c: None for c in drop}, **spaces, "\u2019": "'", "\u02bc": "'", "\u2018": glottal, "\u2035": glottal})

    def __call__(self, text):
        text = text.translate(self.table)
        if self.fix is not None:
            text = self.fix(text)
        if self.form is None:
            text = unicodedata.normalize("NFKC", text)
        return unicodedata.normalize("NFC", text).lower().replace("i\u0307", "i")


def token_splitter(script, extra, zwnj):
    """A regex matching whatever ends a run of adjacent words."""
    wanted = {script}
    if script == "LATIN":
        wanted.add("MODIFIER")
    chars = set(extra)
    for code in range(0x20000):
        char = chr(code)
        category = unicodedata.category(char)
        if category[0] == "L" or category[0] == "M":
            name = script_of(char)
            if name in wanted or name == "COMBINING":
                chars.add(code)
    chars.add(ord("'"))
    if zwnj:
        chars.add(0x200C)
    ranges = []
    for code in sorted(chars):
        if ranges and code == ranges[-1][1] + 1:
            ranges[-1][1] = code
        else:
            ranges.append([code, code])
    body = "".join(f"\\U{a:08X}" if a == b else f"\\U{a:08X}-\\U{b:08X}" for a, b in ranges)
    return re.compile(f"[^{body} \\t]+")


class Segmenter:
    """wm-engine's word segmenter, one line in and one line out."""

    def __init__(self, binary):
        self.process = subprocess.Popen([binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def __call__(self, chunk):
        self.process.stdin.write(chunk + "\n")
        self.process.stdin.flush()
        return self.process.stdout.readline().split()


class Counts:
    def __init__(self):
        self.ids = {}
        self.words = []
        self.tokens = 0
        self.unigrams = {}
        self.bigrams = {}
        self.trigrams = {}
        self.seen = set()
        self.short = {}

    def group(self, weight):
        self.uni = self.unigrams.setdefault(weight, array("i"))
        self.bi = self.bigrams.setdefault(weight, array("q"))
        self.tri = self.trigrams.setdefault(weight, array("q"))

    def add(self, run):
        if len(run) >= 5:
            key = hash(" ".join(run))
            if key in self.seen:
                return
            self.seen.add(key)
        else:
            # A short line seen over and over is a site's menu ("edit source").
            key = hash(" ".join(run))
            seen = self.short.get(key, 0)
            if seen >= MAX_SHORT_REPEATS:
                return
            self.short[key] = seen + 1
        ids = self.ids
        out = []
        for word in run:
            index = ids.get(word)
            if index is None:
                if len(word) > MAX_WORD or len(self.words) >= MAX_IDS:
                    self._flush(out)
                    out = []
                    continue
                index = ids[word] = len(self.words)
                self.words.append(word)
            out.append(index)
        self._flush(out)

    def _flush(self, ids):
        if not ids:
            return
        self.tokens += len(ids)
        self.uni.extend(ids)
        if len(ids) >= 2:
            self.bi.extend((a << RADIX_BITS) | b for a, b in zip(ids, ids[1:]))
        if len(ids) >= 3:
            self.tri.extend((a << (2 * RADIX_BITS)) | (b << RADIX_BITS) | c for a, b, c in zip(ids, ids[1:], ids[2:]))

    def unigram_counts(self):
        counts = np.zeros(len(self.words), dtype=np.int64)
        for weight, ids in self.unigrams.items():
            if ids:
                counts += weight * np.bincount(np.frombuffer(ids, dtype=np.int32), minlength=len(self.words))
        return counts


def collapse(groups):
    keys = []
    counts = []
    for weight, values in groups.items():
        if not values:
            continue
        sorted_keys = np.sort(np.frombuffer(values, dtype=np.int64))
        unique, tally = np.unique(sorted_keys, return_counts=True)
        keys.append(unique)
        counts.append(tally.astype(np.int64) * weight)
    if not keys:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    keys = np.concatenate(keys)
    counts = np.concatenate(counts)
    unique, inverse = np.unique(keys, return_inverse=True)
    return unique, np.bincount(inverse, weights=counts, minlength=unique.size).astype(np.int64)


def write_gz(path, lines):
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as packed:
        for line in lines:
            packed.write(line.encode("utf-8"))


def write_ngrams(path, words, keep, keys, counts, arity, floor, cap):
    mask = np.ones(keys.size, dtype=bool)
    parts = []
    for slot in range(arity):
        part = (keys >> (RADIX_BITS * (arity - 1 - slot))) & MAX_IDS
        parts.append(part)
        mask &= keep[part]
    mask &= counts >= floor
    order = np.flatnonzero(mask)
    order = order[np.lexsort((keys[order], -counts[order]))][:cap]
    write_gz(
        path,
        (" ".join(words[int(parts[s][i])] for s in range(arity)) + f" {int(counts[i])}\n" for i in order),
    )
    return int(order.size)


def lines_of(path):
    if not path.exists():
        return 0
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as lines:
        return sum(1 for _ in lines)


def reference_tables(script, folder):
    tables = []
    for code in REFERENCES.get(script, []):
        path = DATA_DIR / code / f"{code}_full.txt.gz"
        if code == folder or not path.exists():
            continue
        table = {}
        total = 0
        for word, count in read_list(path):
            table[word.lower()] = count
            total += count
            if len(table) >= 50_000:
                break
        tables.append({word: count / total for word, count in table.items()})
    return tables


def build(folder, sources, segmenter_path, work, script_hint=None, min_tokens=MIN_TOKENS):
    out_dir = DATA_DIR / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = work / f"tmp_{folder}"
    tmp.mkdir(parents=True, exist_ok=True)

    old_path = out_dir / f"{folder}_full.txt.gz"
    old = list(read_list(old_path)) if old_path.exists() else []
    script = script_hint or dominant_script(word for word, _ in old[:5000])
    if script is None:
        return {"folder": folder, "status": "no script"}
    zwnj = any("\u200c" in word for word, _ in old[:50000])
    okina = any("\u02bb" in word for word, _ in old[:50000])
    normalize = Normalizer(script, zwnj, folder, okina)

    alphabet = {}
    for word, _ in old[:5000]:
        for char in normalize(word):
            if unicodedata.category(char)[0] in "LM":
                alphabet[ord(char)] = alphabet.get(ord(char), 0) + 1
    letters = sum(alphabet.values()) or 1
    splitter = token_splitter(script, [c for c, n in alphabet.items() if n / letters >= 0.001], zwnj)

    segment = Segmenter(segmenter_path) if script in SEGMENTED else None
    budget = SEGMENTED_BUDGET if segment else TOKEN_BUDGET
    tells = TELLS.get(script) if folder not in TELL_EXEMPT else None

    counts = Counts()
    used = {}
    dropped_docs = 0
    for spec in sources:
        kind, _, name = spec.partition(":")
        weight = 3 if kind == "t" else 1
        if kind != "t" and counts.tokens >= budget:
            continue
        counts.group(weight)
        before = counts.tokens
        try:
            for doc in READERS[kind](name, tmp):
                if len(MOJIBAKE.findall(doc)) >= 3:
                    dropped_docs += 1
                    continue
                doc = normalize(doc)
                if script == "MYANMAR" and folder == "my" and ZAWGYI.search(doc):
                    dropped_docs += 1
                    continue
                runs = []
                n_tokens = n_tells = 0
                for line in doc.split("\n"):
                    for chunk in splitter.split(line):
                        if segment:
                            run = []
                            for piece in chunk.split():
                                run.extend(segment(piece))
                        else:
                            run = [w for w in (t.strip("'") for t in chunk.split()) if w]
                        if run:
                            runs.append(run)
                            n_tokens += len(run)
                            if tells:
                                n_tells += sum(1 for w in run if w in tells)
                if tells and n_tells >= 0.03 * n_tokens and n_tokens >= 8:
                    dropped_docs += 1
                    continue
                for run in runs:
                    counts.add(run)
                if kind != "t" and counts.tokens >= budget:
                    break
        except (OSError, EOFError, ValueError) as error:
            log(f"{folder}: {spec} stopped early: {error}")
        for leftover in tmp.iterdir():
            leftover.unlink()
        if counts.tokens > before:
            used[spec] = counts.tokens - before
        log(f"{folder}: {spec} -> {counts.tokens - before} tokens")
    if segment:
        segment.process.stdin.close()
    counts.seen = counts.short = None

    total = counts.tokens
    report = {"folder": folder, "script": script, "tokens": total, "sources": used, "dropped_docs": dropped_docs}
    shutil.rmtree(tmp, ignore_errors=True)
    if total < min_tokens:
        report["status"] = "too little text"
        return report

    words = counts.words
    uni = counts.unigram_counts()
    old_keys = {}
    for word, count in old:
        key = normalize(word)
        old_keys[key] = old_keys.get(key, 0) + count
    refs = reference_tables(script, folder)
    word_floor = 2 if total < 300_000 else 3 if total < 3_000_000 else 2 + total // 5_000_000
    repeat = re.compile(r"(.)\1{3}")
    keep_list_as_is = len(old) >= KEEP_LIST_ABOVE

    keep = np.zeros(len(words), dtype=bool)
    foreign = set()
    weighted_total = int(uni.sum()) or 1
    for index, word in enumerate(words):
        count = int(uni[index])
        share = count / weighted_total
        if any(share < 0.3 * table.get(word, 0.0) for table in refs):
            # Old lists counted the same foreign text, so being in one is no
            # defence, but a list this leaves alone still holds the word.
            if not keep_list_as_is:
                foreign.add(word)
            continue
        if word in old_keys:
            keep[index] = True
            continue
        if keep_list_as_is or count < word_floor or repeat.search(word):
            continue
        if unicodedata.category(word[0])[0] != "L" or script_of(word[0]) not in (script, "MODIFIER"):
            continue
        if len(word) == 1 and share < 0.0005:
            continue
        keep[index] = True

    n_floor = 5 if total >= 3_000_000 else 3 if total >= 300_000 else 2
    old_bi = out_dir / f"{folder}_bigrams.txt.gz"
    old_tri = out_dir / f"{folder}_trigrams.txt.gz"
    old_bi_lines = lines_of(old_bi)

    keys, tallies = collapse(counts.bigrams)
    counts.bigrams = None
    new_bi = work / f"{folder}.bi.gz"
    n_bi = write_ngrams(new_bi, words, keep, keys, tallies, 2, n_floor, MAX_BIGRAMS)
    keys, tallies = collapse(counts.trigrams)
    counts.trigrams = None
    new_tri = work / f"{folder}.tri.gz"
    n_tri = write_ngrams(new_tri, words, keep, keys, tallies, 3, n_floor, MAX_TRIGRAMS)
    del keys, tallies

    report.update(bigrams=n_bi, trigrams=n_tri, old_bigrams=old_bi_lines, old_words=len(old))
    if n_bi >= max(1000, int(1.5 * old_bi_lines)):
        suffix = "_v2" if old_bi.exists() or old_tri.exists() else ""
        final_bi = out_dir / f"{folder}_bigrams{suffix}.txt.gz"
        final_tri = out_dir / f"{folder}_trigrams{suffix}.txt.gz"
        new_bi.replace(final_bi)
        new_tri.replace(final_tri)
        report.update(
            bigram_stem=final_bi.name[:-7], trigram_stem=final_tri.name[:-7],
            ngram_bytes=final_bi.stat().st_size + final_tri.stat().st_size,
        )
    else:
        new_bi.unlink()
        new_tri.unlink()
        report["ngrams_skipped"] = True

    # The list. Corpus and old counts are on different scales, so the old counts
    # are rescaled to this corpus's size before they are added.
    if not keep_list_as_is:
        scale = total / max(1, sum(old_keys.values()))
        surface = {}
        for word, _ in old:
            surface.setdefault(normalize(word), word)
        merged = {}
        for index, word in enumerate(words):
            if keep[index]:
                merged[word] = int(uni[index])
        for key, count in old_keys.items():
            if key not in foreign:
                merged[key] = merged.get(key, 0) + int(round(count * scale))
        ranked = sorted(merged.items(), key=lambda item: (-max(item[1], 2), item[0]))[:MAX_LIST]
        if len(ranked) >= 1000 and (total >= 1_000_000 or len(ranked) >= 1.2 * len(old)):
            final = out_dir / f"{folder}_full_v2.txt.gz" if old else old_path
            write_gz(final, (f"{surface.get(w, w)} {max(c, 2)}\n" for w, c in ranked))
            report.update(list_stem=final.name[:-7], list_words=len(ranked), list_bytes=final.stat().st_size)
    top = np.argsort(-uni * keep)[:40]
    report["top"] = [words[int(i)] for i in top if keep[int(i)]]
    report["status"] = "built"
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="comma-separated folders; default every folder in the config")
    parser.add_argument("--work", required=True, help="scratch directory; finished languages leave a report here")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--segmenter")
    parser.add_argument("--one", help=argparse.SUPPRESS)
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text())
    work = Path(args.work)
    (work / "reports").mkdir(parents=True, exist_ok=True)

    if args.one:
        entry = config[args.one]
        report = build(args.one, entry["sources"], args.segmenter, work, entry.get("script"), entry.get("min_tokens", MIN_TOKENS))
        (work / "reports" / f"{args.one}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
        log(f"{args.one}: {report['status']} {report.get('tokens')} tokens, {report.get('bigrams')} bigrams")
        return

    wanted = args.only.split(",") if args.only else list(config)
    pending = [f for f in wanted if not (work / "reports" / f"{f}.json").exists()]
    running = []
    while pending or running:
        running = [p for p in running if p.poll() is None]
        while pending and len(running) < args.jobs:
            folder = pending.pop(0)
            command = [sys.executable, "-I", str(Path(__file__).resolve()), "--one", folder, "--work", str(work)]
            if args.segmenter:
                command += ["--segmenter", args.segmenter]
            running.append(subprocess.Popen(command))
        time.sleep(2)


if __name__ == "__main__":
    main()

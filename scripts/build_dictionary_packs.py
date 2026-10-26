#!/usr/bin/env python3
"""Build WM Keyboard's offline English dictionaries (`dictionary/en/*.wmdict.gz`).

The Dictionary tool asks a chain of sources. The vocabulary packs only know
their study lists' few thousand words and every other source is online, so a
phone with no network (or the no-internet build) could not define "house"
(#665). These packs are the offline answer: one line per headword, sorted, so
the app can binary-search the installed file on disk instead of parsing it.

Two packs, both single words only (no "ice cream", no "look after"):

  * `oewn`          Open English WordNet 2024 (CC BY 4.0). Every single-word
                    lemma, every sense, one example, a few synonyms and
                    antonyms, IPA where OEWN has it, irregular forms as
                    redirects.
  * `wiktionary`    English Wiktionary through kaikki.org's extract
                    (CC BY-SA 4.0 and GFDL). Common words only (the repo's
                    frequency list decides, plus every word OEWN has), no
                    proper nouns, a capped number of senses, one short
                    example, IPA, and inflections as redirects.

Sources live in `dictionary/cache/` (gitignored):

  english-wordnet-2024.xml.gz       https://github.com/globalwordnet/english-wordnet/releases
  kaikki-English.common.jsonl.gz    kaikki.org's English extract (520 MB gzipped),
                                    cut on the way in to the words the pack can
                                    keep and the fields it reads (--prefilter):

    curl -sL https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz \
      | python3 scripts/build_dictionary_packs.py --prefilter

  The cut keeps the build reproducible without keeping 3 GB of JSON around:
  `--check` rebuilds from the cut file, whose SHA-256 the pack's header records.

File format, UTF-8 text:

  #wmdict<TAB>1                          magic and format version
  #<field><TAB><value>                   id, name, lang, license, source, ...
  <key><TAB><word><TAB><ipa><TAB><sense><TAB><sense>...
  <key><TAB>@<lemma>|<lemma>             an inflection pointing at its lemmas

<key> is the headword in lower case; lines are sorted by the key's UTF-8
bytes, then by the headword. A sense is four fields joined by U+001F:
part of speech, definition, example, synonyms (`|`-separated); a fifth,
antonyms, is present only when there are some. No field holds a tab, a
newline or U+001F.

Usage:
  python3 scripts/build_dictionary_packs.py                 # both packs
  python3 scripts/build_dictionary_packs.py --packs oewn    # one pack
  python3 scripts/build_dictionary_packs.py --check         # rebuild to a
                                      # temp dir and fail if bytes differ

The build is deterministic: sorted lines, fixed fields, gzip with a zero
mtime and no file name. The header records the source file's SHA-256 rather
than a date, so the same source always makes the same bytes.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import io
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "dictionary" / "en"
CACHE = ROOT / "dictionary" / "cache"
OEWN_SOURCE = CACHE / "english-wordnet-2024.xml.gz"
KAIKKI_SOURCE = CACHE / "kaikki-English.common.jsonl.gz"
FREQUENCY = ROOT / "data" / "en" / "en_full.txt.gz"

FORMAT_VERSION = 1
SEP = "\x1f"

# A single word: starts with a letter, then letters or apostrophes
# ("o'clock"). No spaces, hyphens, full stops or digits: compounds like
# "self-esteem" would add a sixth to the pack for words the user can look up
# by their parts.
WORD = re.compile(r"^[^\W\d_](?:[^\W\d_]|['’])*$")

MAX_SYNONYMS = 4
MAX_ANTONYMS = 3

# The Wiktionary pack's cut. A word is kept when the frequency list counts it
# at least KAIKKI_MIN_COUNT times or OEWN has it too; KAIKKI_MAX_SENSES senses
# per part of speech and KAIKKI_MAX_WORD_SENSES in all, examples and
# definitions trimmed to the lengths below. That holds the pack near 4.5 MB.
# Proper nouns (Wiktionary's "name": surnames, villages) are left out; they
# were a tenth of the pack and crowded out the common noun ("House", a
# village in New Mexico, before "house").
KAIKKI_MIN_COUNT = 300
KAIKKI_MAX_SENSES = 3
KAIKKI_MAX_WORD_SENSES = 6
KAIKKI_MAX_DEFINITION = 240
KAIKKI_MAX_EXAMPLE = 120

POS_OEWN = {"n": "noun", "v": "verb", "a": "adjective", "s": "adjective", "r": "adverb"}
POS_ORDER = ["noun", "verb", "adjective", "adverb"]


def clean(text: str | None) -> str:
    """One line, no separators: whitespace runs to a space, U+001F and '|' out."""
    if not text:
        return ""
    text = text.replace(SEP, " ").replace("|", "/")
    return re.sub(r"\s+", " ", text).strip()


def trim(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "…"


def sense_field(pos: str, definition: str, example: str, synonyms: list[str], antonyms: list[str]) -> str:
    fields = [pos, clean(definition), clean(example), "|".join(clean(s) for s in synonyms if clean(s))]
    ants = "|".join(clean(a) for a in antonyms if clean(a))
    if ants:
        fields.append(ants)
    return SEP.join(fields)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_pack(path: Path, header: dict[str, str], entries: dict[str, list], redirects: dict[str, set[str]]) -> int:
    """Writes the sorted pack; returns the headword count. [entries] maps headword → (ipa, senses)."""
    lines: list[tuple[bytes, str, str]] = []
    keys_with_entries = set()
    for word, (ipa, senses) in entries.items():
        if not senses:
            continue
        key = word.lower()
        keys_with_entries.add(key)
        lines.append((key.encode("utf-8"), word, "\t".join([key, word, clean(ipa), *senses])))
    for key, targets in redirects.items():
        # A form that is a headword of its own is looked up as itself; the
        # app then tries the rules for the lemma only when nothing matched.
        if key in keys_with_entries:
            continue
        targets = sorted(t for t in targets if t.lower() != key and t.lower() in keys_with_entries)
        if targets:
            lines.append((key.encode("utf-8"), "@", key + "\t@" + "|".join(targets)))
    lines.sort(key=lambda line: (line[0], line[1]))
    text = io.StringIO()
    text.write(f"#wmdict\t{FORMAT_VERSION}\n")
    for field, value in header.items():
        text.write(f"#{field}\t{clean(value)}\n")
    for _, _, line in lines:
        text.write(line)
        text.write("\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
        gz.write(text.getvalue().encode("utf-8"))
    return len(keys_with_entries)


# ---------------------------------------------------------------- OEWN


def read_oewn(source: Path):
    """Lexical entries (lemma, pos, sense synset ids, IPA, forms) and synsets (definition, examples, members)."""
    entries = []
    synsets = {}
    sense_antonyms = collections.defaultdict(list)  # sense id -> antonym sense ids
    sense_lemma = {}
    with gzip.open(source, "rb") as f:
        for _, elem in ET.iterparse(f, events=("end",)):
            tag = elem.tag
            if tag == "LexicalEntry":
                lemma = elem.find("Lemma")
                form = lemma.get("writtenForm")
                pos = lemma.get("partOfSpeech")
                ipa = ""
                for p in lemma.findall("Pronunciation"):
                    if p.get("variety") in (None, "US") and not ipa:
                        ipa = p.text or ""
                if not ipa:
                    first = lemma.find("Pronunciation")
                    ipa = first.text if first is not None and first.text else ""
                senses = []
                for sense in elem.findall("Sense"):
                    sid = sense.get("id")
                    senses.append((sid, sense.get("synset")))
                    sense_lemma[sid] = form
                    for rel in sense.findall("SenseRelation"):
                        if rel.get("relType") == "antonym":
                            sense_antonyms[sid].append(rel.get("target"))
                forms = [x.get("writtenForm") for x in elem.findall("Form")]
                entries.append((elem.get("id"), form, pos, senses, ipa, forms))
                elem.clear()
            elif tag == "Synset":
                definition = elem.findtext("Definition") or ""
                examples = [e.text or "" for e in elem.findall("Example")]
                members = (elem.get("members") or "").split()
                synsets[elem.get("id")] = (definition, examples, members)
                elem.clear()
    return entries, synsets, sense_antonyms, sense_lemma


def build_oewn(source: Path, out: Path) -> int:
    entries, synsets, sense_antonyms, sense_lemma = read_oewn(source)
    lemma_by_entry = {entry_id: form for entry_id, form, *_ in entries}
    by_word: dict[str, dict] = collections.OrderedDict()
    redirects: dict[str, set[str]] = collections.defaultdict(set)
    for _, form, pos, senses, ipa, forms in entries:
        if not WORD.match(form):
            continue
        record = by_word.setdefault(form, {"ipa": ipa, "pos": collections.OrderedDict()})
        if not record["ipa"]:
            record["ipa"] = ipa
        pos_name = POS_OEWN[pos]
        bucket = record["pos"].setdefault(pos_name, [])
        for sid, synset_id in senses:
            definition, examples, members = synsets.get(synset_id, ("", [], []))
            if not definition:
                continue
            synonyms = []
            for m in members:
                w = lemma_by_entry.get(m, "")
                if w and w != form and w not in synonyms:
                    synonyms.append(w)
            antonyms = [sense_lemma[a] for a in sense_antonyms.get(sid, []) if a in sense_lemma]
            bucket.append(sense_field(
                pos_name, definition, examples[0] if examples else "",
                synonyms[:MAX_SYNONYMS], antonyms[:MAX_ANTONYMS],
            ))
        for f in forms:
            if f and WORD.match(f):
                redirects[f.lower()].add(form)
    packed = {}
    for word, record in by_word.items():
        groups = [(pos, senses) for pos, senses in record["pos"].items() if senses]
        # The part of speech with the most senses first ("run" is a verb
        # before it is a noun), ties in the usual dictionary order.
        groups.sort(key=lambda g: (-len(g[1]), POS_ORDER.index(g[0])))
        packed[word] = (record["ipa"], [s for _, senses in groups for s in senses])
    header = {
        "id": "oewn",
        "name": "Open English WordNet",
        "lang": "en",
        "version": "2024",
        "license": "CC-BY-4.0",
        "attribution": "Open English WordNet 2024, https://en-word.net, CC BY 4.0",
        "source": "english-wordnet-2024.xml.gz sha256:" + sha256(source)[:16],
    }
    return write_pack(out, header, packed, redirects)


# ---------------------------------------------------------------- Wiktionary


KAIKKI_POS = {
    "noun": "noun", "verb": "verb", "adj": "adjective", "adv": "adverb",
    "pron": "pronoun", "prep": "preposition", "conj": "conjunction", "intj": "interjection",
    "det": "determiner", "article": "article", "num": "numeral", "particle": "particle",
    "contraction": "contraction", "prefix": "prefix", "suffix": "suffix",
    "abbrev": "abbreviation", "phrase": "phrase", "prep_phrase": "phrase", "postp": "postposition",
}

# Senses that say nothing to someone looking a word up.
SKIP_SENSE_TAGS = {"obsolete", "archaic", "rare", "dated", "nonstandard", "misspelling", "uncommon"}
REDIRECT_TAGS = {"form-of", "alt-of", "misspelling"}


def read_frequency(path: Path, minimum: int) -> set[str]:
    words = set()
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            word, _, count = line.rstrip("\n").rpartition(" ")
            if count.isdigit() and int(count) >= minimum:
                words.add(word.lower())
    return words


def oewn_words(path: Path) -> set[str]:
    words = set()
    with gzip.open(path, "rb") as f:
        for _, elem in ET.iterparse(f, events=("end",)):
            if elem.tag == "Lemma":
                words.add((elem.get("writtenForm") or "").lower())
            elif elem.tag in ("LexicalEntry", "Synset"):
                elem.clear()
    return words


def kaikki_ipa(record: dict) -> str:
    first = ""
    for sound in record.get("sounds", []):
        ipa = sound.get("ipa")
        if not ipa:
            continue
        tags = set(sound.get("tags", []))
        if "US" in tags or "General-American" in tags:
            return ipa
        if not first:
            first = ipa
    return first


def prefilter(stdin, out: Path) -> int:
    """Reads kaikki's gzipped JSONL from [stdin] and keeps what build_kaikki can use."""
    common = read_frequency(FREQUENCY, KAIKKI_MIN_COUNT) | oewn_words(OEWN_SOURCE)
    kept = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(out.name + ".part")
    with gzip.open(stdin, "rt", encoding="utf-8") as f, \
            part.open("wb") as raw, \
            gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as gz:
        for line in f:
            record = json.loads(line)
            word = record.get("word", "")
            if record.get("lang_code") != "en" or not WORD.match(word) or word.lower() not in common:
                continue
            if record.get("pos", "") not in KAIKKI_POS:
                continue
            slim = {
                "word": word,
                "lang_code": "en",
                "pos": record["pos"],
                "sounds": [{"ipa": x["ipa"], "tags": x.get("tags", [])} for x in record.get("sounds", []) if x.get("ipa")],
                "senses": [{
                    "glosses": sense.get("glosses", []),
                    "tags": sense.get("tags", []),
                    "examples": [{"text": e.get("text", ""), "type": e.get("type", "example")} for e in sense.get("examples", [])],
                    "synonyms": [{"word": x.get("word", ""), "source": x.get("source", "")} for x in sense.get("synonyms", [])],
                    "antonyms": [{"word": x.get("word", ""), "source": x.get("source", "")} for x in sense.get("antonyms", [])],
                    "form_of": [{"word": x.get("word", "")} for x in sense.get("form_of", [])],
                    "alt_of": [{"word": x.get("word", "")} for x in sense.get("alt_of", [])],
                } for sense in record.get("senses", [])],
            }
            gz.write((json.dumps(slim, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
            kept += 1
    part.replace(out)
    return kept


def build_kaikki(source: Path, out: Path) -> int:
    common = read_frequency(FREQUENCY, KAIKKI_MIN_COUNT) | oewn_words(OEWN_SOURCE)
    by_word: dict[str, dict] = {}
    forms_of: dict[str, list[tuple[str, str]]] = {}
    redirects: dict[str, set[str]] = collections.defaultdict(set)
    with gzip.open(source, "rt", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            word = record.get("word", "")
            if record.get("lang_code") != "en" or not WORD.match(word) or word.lower() not in common:
                continue
            pos = KAIKKI_POS.get(record.get("pos", ""))
            if pos is None:
                continue
            senses = []
            form_senses = []
            for sense in record.get("senses", []):
                tags = set(sense.get("tags", []))
                targets = [x.get("word", "") for x in sense.get("form_of", []) + sense.get("alt_of", [])]
                if tags & REDIRECT_TAGS and targets:
                    for t in targets:
                        if WORD.match(t):
                            redirects[word.lower()].add(t)
                    # Kept as a sense too, in case the word has senses of its
                    # own ("mice" is a verb as well): it then says what it is
                    # a form of. A word with no others stays a redirect.
                    glosses = sense.get("glosses") or []
                    if glosses:
                        form_senses.append((pos, trim(clean(glosses[-1]), KAIKKI_MAX_DEFINITION)))
                    continue
                if tags & SKIP_SENSE_TAGS:
                    continue
                glosses = sense.get("glosses") or []
                if not glosses:
                    continue
                # A subsense repeats its parent's gloss first; the last one is its own.
                definition = trim(clean(glosses[-1]), KAIKKI_MAX_DEFINITION)
                example = ""
                for ex in sense.get("examples", []):
                    text = clean(ex.get("text"))
                    if text and ex.get("type", "example") == "example" and len(text) <= KAIKKI_MAX_EXAMPLE:
                        example = text
                        break
                synonyms = [s.get("word", "") for s in sense.get("synonyms", []) if not s.get("source")]
                antonyms = [a.get("word", "") for a in sense.get("antonyms", []) if not a.get("source")]
                senses.append((definition, example, synonyms[:MAX_SYNONYMS], antonyms[:MAX_ANTONYMS]))
            if form_senses:
                forms_of.setdefault(word, []).extend(form_senses)
            if not senses:
                continue
            record_out = by_word.setdefault(word, {"ipa": "", "pos": collections.OrderedDict()})
            if not record_out["ipa"]:
                record_out["ipa"] = kaikki_ipa(record)
            bucket = record_out["pos"].setdefault(pos, [])
            seen = {s[0] for s in bucket}
            for definition, example, synonyms, antonyms in senses:
                if len(bucket) >= KAIKKI_MAX_SENSES or definition in seen:
                    continue
                seen.add(definition)
                bucket.append((definition, example, synonyms, antonyms))
    for word, forms in forms_of.items():
        record = by_word.get(word)
        if record is None:
            continue
        for pos, gloss in reversed(forms):
            bucket = record["pos"].setdefault(pos, [])
            if all(gloss != d for d, *_ in bucket):
                bucket.insert(0, (gloss, "", [], []))
                del bucket[KAIKKI_MAX_SENSES:]
            # "plural of mouse" before the rare verb "mice".
            record["pos"].move_to_end(pos, last=False)
    packed = {}
    for word, record in by_word.items():
        # Wiktionary's own order of parts of speech is its etymology order,
        # which is also roughly how common each is: kept as it came.
        fields = [
            sense_field(pos, d, e, s, a)
            for pos, senses in record["pos"].items()
            for d, e, s, a in senses
        ]
        packed[word] = (record["ipa"], fields[:KAIKKI_MAX_WORD_SENSES])
    header = {
        "id": "wiktionary",
        "name": "Wiktionary (offline)",
        "lang": "en",
        "license": "CC-BY-SA-4.0 OR GFDL-1.3",
        "attribution": "English Wiktionary via kaikki.org, CC BY-SA 4.0 and GFDL",
        "source": "kaikki-English.jsonl.gz sha256:" + sha256(source)[:16],
    }
    return write_pack(out, header, packed, redirects)


# ---------------------------------------------------------------- Bengali

KAIKKI_BENGALI_SOURCE = CACHE / "kaikki-Bengali.jsonl"
BENGALI = re.compile(r"^[\u0980-\u09FF\u200C\u200D]+$")


def build_kaikki_bengali(source: Path, out: Path) -> int:
    """
    Bengali words with English glosses, from English Wiktionary's Bengali
    entries via kaikki.org (the plain, ungzipped JSONL it publishes per
    language): what the Dictionary tool shows for a Bengali word typed or
    selected, with no network. The romanization stands where the IPA goes.
    Every entry is kept (the extract is small), and each inflected form the
    entry lists redirects to it.
    """
    by_word: dict[str, dict] = {}
    redirects: dict[str, set[str]] = collections.defaultdict(set)
    with source.open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            word = record.get("word", "")
            if record.get("lang_code") != "bn" or not BENGALI.match(word):
                continue
            pos = KAIKKI_POS.get(record.get("pos", ""))
            if pos is None:
                continue
            roman = ""
            for form in record.get("forms", []):
                tags = set(form.get("tags", []))
                text = form.get("form", "")
                if "romanization" in tags and not roman:
                    roman = clean(text)
                elif BENGALI.match(text) and text != word and form.get("source") != "inflection-template":
                    redirects[text].add(word)
            senses = []
            for sense in record.get("senses", []):
                tags = set(sense.get("tags", []))
                targets = [x.get("word", "") for x in sense.get("form_of", []) + sense.get("alt_of", [])]
                if tags & REDIRECT_TAGS and targets:
                    for t in targets:
                        if BENGALI.match(t):
                            redirects[word].add(t)
                    continue
                if tags & SKIP_SENSE_TAGS:
                    continue
                glosses = sense.get("glosses") or []
                if not glosses:
                    continue
                definition = trim(clean(glosses[-1]), KAIKKI_MAX_DEFINITION)
                example = ""
                for ex in sense.get("examples", []):
                    text = clean(ex.get("text"))
                    english = clean(ex.get("english") or ex.get("translation"))
                    if text and len(text) <= KAIKKI_MAX_EXAMPLE:
                        example = trim(text + (" — " + english if english else ""), KAIKKI_MAX_EXAMPLE * 2)
                        break
                synonyms = [s.get("word", "") for s in sense.get("synonyms", []) if not s.get("source")]
                senses.append((definition, example, synonyms[:MAX_SYNONYMS], []))
            if not senses:
                continue
            record_out = by_word.setdefault(word, {"ipa": roman, "pos": collections.OrderedDict()})
            if not record_out["ipa"]:
                record_out["ipa"] = roman
            bucket = record_out["pos"].setdefault(pos, [])
            seen = {s[0] for s in bucket}
            for definition, example, synonyms, antonyms in senses:
                if len(bucket) >= KAIKKI_MAX_SENSES or definition in seen:
                    continue
                seen.add(definition)
                bucket.append((definition, example, synonyms, antonyms))
    packed = {}
    for word, record in by_word.items():
        fields = [
            sense_field(pos, d, e, s, a)
            for pos, senses in record["pos"].items()
            for d, e, s, a in senses
        ]
        packed[word] = (record["ipa"], fields[:KAIKKI_MAX_WORD_SENSES])
    header = {
        "id": "bn_wiktionary",
        "name": "Bengali–English Wiktionary (offline)",
        "lang": "bn",
        "license": "CC-BY-SA-4.0 OR GFDL-1.3",
        "attribution": "English Wiktionary's Bengali entries via kaikki.org, CC BY-SA 4.0 and GFDL",
        "source": "kaikki-Bengali.jsonl sha256:" + sha256(source)[:16],
    }
    return write_pack(out, header, packed, redirects)


PACKS = {
    "oewn": (OEWN_SOURCE, build_oewn, "en"),
    "wiktionary": (KAIKKI_SOURCE, build_kaikki, "en"),
    "bn_wiktionary": (KAIKKI_BENGALI_SOURCE, build_kaikki_bengali, "bn"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--packs", default=",".join(PACKS), help="comma-separated pack ids")
    parser.add_argument("--check", action="store_true", help="rebuild and compare with the checked-in files")
    parser.add_argument("--prefilter", action="store_true", help="cut kaikki's English JSONL (gzipped, on stdin) into the cache")
    args = parser.parse_args()
    if args.prefilter:
        kept = prefilter(sys.stdin.buffer, KAIKKI_SOURCE)
        print(f"kept {kept} records -> {KAIKKI_SOURCE.relative_to(ROOT)}")
        return 0
    ids = [p for p in args.packs.split(",") if p]
    unknown = [p for p in ids if p not in PACKS]
    if unknown:
        parser.error("unknown pack: " + ", ".join(unknown))
    failed = False
    with tempfile.TemporaryDirectory() as tmp:
        for pack_id in ids:
            source, build, lang = PACKS[pack_id]
            if not source.is_file():
                print(f"{pack_id}: missing {source.relative_to(ROOT)}; see the docstring for where to get it", file=sys.stderr)
                failed = True
                continue
            final = ROOT / "dictionary" / lang / f"{pack_id}.wmdict.gz"
            target = Path(tmp) / final.name if args.check else final
            count = build(source, target)
            size = target.stat().st_size
            if args.check:
                same = final.is_file() and final.read_bytes() == target.read_bytes()
                print(f"{pack_id}: {count} words, {size} bytes, {'identical' if same else 'DIFFERS'}")
                failed |= not same
            else:
                print(f"{pack_id}: {count} words, {size} bytes -> {final.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

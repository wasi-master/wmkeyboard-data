#!/usr/bin/env python3
"""Build WM Keyboard vocabulary packs (`vocab/<lang>/<id>.wmvocab.json.gz`).

Each pack is one GRE word list (Word Smart 1, Barron's 333, ...) turned into a
self-contained dictionary: part of speech, IPA for both accents, senses with
examples and quotations, synonyms, antonyms, word family, etymology, and the
"trigger" words — plainer synonyms that make the keyboard offer the harder
word while you type ("hate" -> abhor).

Sources, in order of preference:
  * Wiktionary through kaikki.org's per-word JSONL (CC BY-SA 3.0);
  * WordNet 3.0 through NLTK, for words Wiktionary lacks or defines thinly;
  * the CMU Pronouncing Dictionary for IPA when Wiktionary has none;
  * the repo's own English frequency list (`data/en/en_full.txt.gz`), whose
    Zipf-scale frequencies decide what counts as a plainer word;
  * `vocab/sources/word_details.json` for mnemonics and stress respellings;
  * `vocab/translations/<code>.json` for hand-written glosses (Bengali).

Translations Wiktionary lists for other languages are written beside the pack
as per-language sidecars (`<id>.tr.<code>.json.gz`) so the app downloads only
the languages a user reads.

Usage:
  python3 scripts/build_vocab_packs.py                       # every list
  python3 scripts/build_vocab_packs.py --lists ws1,ws2,b333  # some lists
  python3 scripts/build_vocab_packs.py --offline             # cache only
  python3 scripts/build_vocab_packs.py --check               # rebuild to a
                                        # temp dir and fail if bytes differ

Every fetch is cached under `vocab/cache/` (gitignored), so a rerun costs no
network. The build is deterministic: sorted words, fixed key order, gzip with
a zero mtime — only `pack.built` (the build date) changes between runs, and
`--check` ignores it.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as _dt
import gzip
import io
import json
import math
import re
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VOCAB = REPO / "vocab"
SOURCES = VOCAB / "sources"
LISTS_FILE = SOURCES / "lists.json"
DETAILS_FILE = SOURCES / "word_details.json"
TRANSLATIONS = VOCAB / "translations"
CACHE = VOCAB / "cache"
KAIKKI_CACHE = CACHE / "kaikki"
ZIPF_CACHE = CACHE / "zipf.json"
REPORT_FILE = VOCAB / "build-report.txt"
FREQUENCY_LIST = REPO / "data" / "en" / "en_full.txt.gz"

FORMAT = "wmkeyboard-vocab"
VERSION = 1
LANG = "en"

KAIKKI_URL = "https://kaikki.org/dictionary/English/meaning/{a}/{ab}/{w}.jsonl"
USER_AGENT = "wmkeyboard-data vocab builder (+https://github.com/wasi-master/wmkeyboard-data)"
FETCH_SLEEP_S = 0.12
FETCH_RETRIES = 3
FETCH_TIMEOUT_S = 30

# A list entry: letters, with inner apostrophes, hyphens or spaces.
WORD_RE = re.compile(r"^[a-z][a-z' \-]*[a-z]$")
TOKEN_RE = re.compile(r"^[a-z]+$")

POS_MAP = {
    "adj": "adjective",
    "adv": "adverb",
    "intj": "interjection",
    "prep": "preposition",
    "conj": "conjunction",
    "det": "determiner",
    "pron": "pronoun",
    "num": "numeral",
    "prep_phrase": "phrase",
    "adv_phrase": "phrase",
}
POS_DROP = {"name", "prefix", "suffix", "character", "symbol", "proverb", "infix", "affix"}
WORDNET_POS = {"n": "noun", "v": "verb", "a": "adjective", "s": "adjective", "r": "adverb"}

SENSE_DROP_TAGS = {"obsolete", "archaic", "rare", "dated", "historical", "nonstandard", "misspelling"}
SENSE_DROP_GLOSS = re.compile(
    r"^(?:Alternative|Obsolete|Archaic|Dated|Rare|Nonstandard|Eye[- ]dialect)\s+(?:form|spelling)\s+of\b"
    r"|^(?:Misspelling|Synonym|Abbreviation|Initialism|Acronym|Clipping|Ellipsis)\s+of\b",
    re.IGNORECASE,
)
TAG_WHITELIST = {
    "transitive", "intransitive", "ambitransitive", "reflexive", "formal", "informal",
    "figurative", "literary", "slang", "colloquial", "derogatory", "humorous",
    "countable", "uncountable",
}
INFLECTION_TAGS = {
    "third-person", "past", "participle", "present", "plural",
    "comparative", "superlative",
}
FORM_SKIP_TAGS = {"table-tags", "inflection-template", "class", "canonical", "romanization"}
ORIGIN_TEMPLATES = {"inh", "der", "bor", "lbor", "obor", "ubor", "uder", "inh+", "der+", "bor+"}
ROOT_LANGS = {
    "ine-pro": "Proto-Indo-European",
    "gem-pro": "Proto-Germanic",
    "gmw-pro": "Proto-West Germanic",
    "itc-pro": "Proto-Italic",
    "sem-pro": "Proto-Semitic",
    "iir-pro": "Proto-Indo-Iranian",
    "cel-pro": "Proto-Celtic",
    "sla-pro": "Proto-Slavic",
    "grk-pro": "Proto-Hellenic",
    "ine-bsl-pro": "Proto-Balto-Slavic",
}

# Consonant clusters English allows at the start of a syllable (IPA), used to
# place stress marks when converting CMU pronunciations.
IPA_ONSETS = {
    "pɹ", "pl", "pj", "bɹ", "bl", "bj", "tɹ", "tw", "tj", "dɹ", "dw", "dj",
    "kɹ", "kl", "kw", "kj", "ɡɹ", "ɡl", "ɡw", "fɹ", "fl", "fj", "vj", "θɹ",
    "θw", "ʃɹ", "hj", "mj", "nj", "sl", "sw", "sm", "sn", "sp", "st", "sk",
    "sf", "spɹ", "spl", "stɹ", "skɹ", "skw", "skl", "spj", "stj", "skj",
}

MAX_SENSES_PER_POS = 3
MAX_DEFINITION = 240
MAX_EXAMPLE = 160
MAX_QUOTATIONS = 2
MAX_QUOTATION = 220
MAX_REF = 80
MAX_ETYMOLOGY = 240
MIN_ETYMOLOGY_CUT = 120
MAX_RELATED = 12
MAX_FAMILY = 8
MAX_HYPER = 6
MAX_FORMS = 8
MAX_ORIGIN = 6

TRIGGER_MIN_ZIPF = 3.5
TRIGGER_MIN_GAP = 1.0
TRIGGER_MAX_ZIPF = 6.0
TRIGGER_MIN_LEN = 3
TRIGGER_FANOUT = 5

TRANSLATION_MIN_COVERAGE = 0.10
TRANSLATIONS_PER_LANGUAGE = 3

ATTRIBUTION = [
    {
        "name": "Wiktionary (via kaikki.org)",
        "license": "CC-BY-SA-3.0",
        "url": "https://kaikki.org/dictionary/English/",
    },
    {
        "name": "WordNet 3.0",
        "license": "WordNet License",
        "url": "https://wordnet.princeton.edu/license-and-commercial-use",
    },
    {
        "name": "CMU Pronouncing Dictionary",
        "license": "BSD-2-Clause",
        "url": "http://www.speech.cs.cmu.edu/cgi-bin/cmudict",
    },
    {
        "name": "FrequencyWords (OpenSubtitles 2018)",
        "license": "CC-BY-SA-4.0",
        "url": "https://github.com/hermitdave/FrequencyWords",
    },
]

# ---------------------------------------------------------------------------
# Normalisation helpers (pure; unit-tested)
# ---------------------------------------------------------------------------


def normalize_word(value: str) -> str | None:
    """A list entry as a lowercase lemma, or None when it is not a word."""
    text = unicodedata.normalize("NFKC", str(value)).strip().lower()
    text = text.replace("’", "'").replace("‘", "'").replace("\\'", "'")
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" .,;:!?\"()[]")
    if not WORD_RE.match(text):
        return None
    return text


def normalize_pos(pos: str | None) -> str | None:
    if not pos:
        return None
    pos = pos.strip().lower()
    if pos in POS_DROP:
        return None
    return POS_MAP.get(pos, pos)


def truncate(text: str, limit: int) -> str:
    """Cut at a word boundary under [limit], with an ellipsis when cut."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    space = cut.rfind(" ")
    if space > limit // 2:
        cut = cut[:space]
    return cut.rstrip(" ,;:") + "…"


def sentence_cut(text: str, min_len: int, max_len: int) -> str:
    """Cut at the first sentence end past [min_len]; hard-truncate past [max_len]."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    for m in re.finditer(r"[.!?](?=\s|$)", text):
        if m.end() >= min_len:
            if m.end() <= max_len:
                return text[: m.end()]
            break
    return truncate(text, max_len)


def clean_etymology(text: str) -> str:
    text = re.sub(r"^\s*First attested (?:in|around|from)\s+(?:the\s+)?[^,]*,\s*", "", text)
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
    return sentence_cut(text, MIN_ETYMOLOGY_CUT, MAX_ETYMOLOGY)


def attested_year(etymology_text: str, senses: list[dict]) -> str | None:
    m = re.search(r"[Ff]irst attested (?:in|around|from)\s+(?:the\s+)?(\d{4})", etymology_text or "")
    if m:
        return m.group(1)
    for sense in senses:
        for att in sense.get("attestations", []) or []:
            date = att.get("date", "") or ""
            m = re.search(r"\((\d{4})\s+to\s+(\d{4})\)", date)
            if m:
                return f"c. {m.group(1)}–{m.group(2)}"
            m = re.search(r"(\d{4})", date)
            if m:
                return m.group(1)
    return None


def clean_ref(ref: str) -> str:
    """"1975 March 21, Judy Klemesrud, “Vegetarianism…”, in The New York Times, →ISSN" -> short."""
    ref = re.sub(r"\[…\]|\[…\]|\(\.\.\.\)", "", ref)
    ref = re.sub(r"→\w+,?", "", ref)
    ref = re.sub(r"\s+", " ", ref).strip(" ,:;")
    # Keep "year, author, title" — the first three comma-separated parts,
    # letting a quoted title keep its inner commas.
    parts: list[str] = []
    depth = 0
    current = ""
    for ch in ref:
        if ch in "“\"":
            depth = 1 if ch == "“" else depth
        if ch == "”":
            depth = 0
        if ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
            if len(parts) == 3:
                break
        else:
            current += ch
    else:
        if current.strip():
            parts.append(current.strip())
    short = ", ".join(p for p in parts[:3] if p)
    short = re.sub(r"\s*\(date written\)", "", short)
    return truncate(short, MAX_REF)


def clean_respelling(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip().strip("/").strip("()").strip()
    return text or None


def arpabet_to_ipa(phones: list[str]) -> str:
    """CMU ARPAbet with stress digits -> a slashed IPA string (General American)."""
    vowels = {
        "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ",
        "AY": "aɪ", "EH": "ɛ", "ER": "ɝ", "EY": "eɪ", "IH": "ɪ",
        "IY": "i", "OW": "oʊ", "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
    }
    consonants = {
        "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f", "G": "ɡ",
        "HH": "h", "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
        "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ", "T": "t", "TH": "θ",
        "V": "v", "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ",
    }
    # A syllable starts at the longest consonant cluster English allows as an
    # onset before each vowel (maximal onset); whatever is left of the cluster
    # closes the previous syllable. Stress marks go in front of the onset.
    out: list[str] = []
    pending: list[str] = []  # consonants waiting for their vowel
    for phone in phones:
        base = phone.rstrip("012")
        stress = phone[len(base):]
        if base in vowels:
            mark = "ˈ" if stress == "1" else "ˌ" if stress == "2" else ""
            vowel = vowels[base]
            if base == "AH" and stress == "0":
                vowel = "ə"
            if base == "ER" and stress == "0":
                vowel = "ɚ"
            split = 0
            for i in range(len(pending)):
                if len(pending) - i <= 1 or "".join(pending[i:]) in IPA_ONSETS:
                    split = i
                    break
            out.append("".join(pending[:split]) + mark + "".join(pending[split:]) + vowel)
            pending = []
        else:
            pending.append(consonants.get(base, base.lower()))
    out.append("".join(pending))
    return "/" + "".join(out) + "/"


def inflect(word: str) -> list[str]:
    """Rule-based English inflections for a trigger word without a Wiktionary entry."""
    forms: list[str] = []
    if re.search(r"(s|x|z|ch|sh)$", word):
        forms.append(word + "es")
    elif re.search(r"[^aeiou]y$", word):
        forms.append(word[:-1] + "ies")
    else:
        forms.append(word + "s")
    if word.endswith("e"):
        forms.append(word + "d")
    elif re.search(r"[^aeiou]y$", word):
        forms.append(word[:-1] + "ied")
    else:
        forms.append(word + "ed")
    if word.endswith("e") and not word.endswith(("ee", "ye", "oe")):
        forms.append(word[:-1] + "ing")
    else:
        forms.append(word + "ing")
    seen: list[str] = []
    for form in forms:
        if form != word and form not in seen:
            seen.append(form)
    return seen


def is_trigger(candidate: str, word: str, zipf_c: float, zipf_w: float, list_union: set[str],
               stopwords: set[str], word_forms: set[str]) -> bool:
    if not TOKEN_RE.match(candidate) or len(candidate) < TRIGGER_MIN_LEN:
        return False
    if candidate == word or candidate in word_forms or candidate in list_union or candidate in stopwords:
        return False
    if zipf_c < max(TRIGGER_MIN_ZIPF, zipf_w + TRIGGER_MIN_GAP):
        return False
    return zipf_c <= TRIGGER_MAX_ZIPF


def dedupe(items, key=lambda x: x):
    seen = set()
    out = []
    for item in items:
        k = key(item)
        if k in seen or not k:
            continue
        seen.add(k)
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# Kaikki record parsing (pure; unit-tested with a fixture)
# ---------------------------------------------------------------------------


def kaikki_forms(entries: list[dict], headword: str) -> list[str]:
    forms: list[str] = []
    for entry in entries:
        for form in entry.get("forms", []) or []:
            tags = set(form.get("tags", []) or [])
            if tags & FORM_SKIP_TAGS or not tags & INFLECTION_TAGS:
                continue
            text = form.get("form", "")
            if text and text != headword and TOKEN_RE.match(text.replace(" ", "")):
                forms.append(text)
    return dedupe(forms)


def kaikki_sounds(entries: list[dict]) -> tuple[dict, dict, str | None, str | None]:
    """(ipa by accent, audio by accent, enpr respelling, rhyme)."""
    ipa: dict[str, str] = {}
    audio: dict[str, str] = {}
    enpr = None
    rhyme = None
    for entry in entries:
        for sound in entry.get("sounds", []) or []:
            tags = set(sound.get("tags", []) or [])
            accent = None
            if tags & {"General-American", "US", "GA", "General-Australian"} and not tags & {"General-Australian"}:
                accent = "us"
            elif tags & {"Received-Pronunciation", "UK", "RP", "British"}:
                accent = "uk"
            if "ipa" in sound:
                key = accent or ("us" if "us" not in ipa else None)
                if key and key not in ipa and sound["ipa"].startswith(("/", "[")):
                    ipa[key] = sound["ipa"]
            url = sound.get("mp3_url") or sound.get("ogg_url")
            if url:
                name = (sound.get("audio") or url).lower()
                key = accent
                if key is None:
                    if "en-us" in name or "-us-" in name:
                        key = "us"
                    elif "en-uk" in name or "-uk-" in name or "en-gb" in name:
                        key = "uk"
                    elif "en-au" in name or "en-ca" in name or "en-nz" in name:
                        key = None
                    elif "us" not in audio:
                        key = "us"
                if key and key not in audio:
                    audio[key] = url
            if enpr is None and sound.get("enpr"):
                enpr = sound["enpr"]
            if rhyme is None and sound.get("rhymes"):
                rhyme = sound["rhymes"]
    return ipa, audio, enpr, rhyme


def sense_dropped(sense: dict) -> bool:
    tags = set(sense.get("tags", []) or [])
    if tags & SENSE_DROP_TAGS:
        return True
    glosses = sense.get("glosses") or []
    if not glosses:
        return True
    return bool(SENSE_DROP_GLOSS.match(glosses[0]))


def parse_sense(sense: dict, pos: str) -> dict:
    glosses = [g.strip() for g in (sense.get("glosses") or []) if g and g.strip()]
    definition = truncate(": ".join(glosses), MAX_DEFINITION)
    example = None
    quotations: list[tuple[int, dict]] = []
    for ex in sense.get("examples", []) or []:
        text = re.sub(r"\s+", " ", (ex.get("text") or "")).strip()
        if not text:
            continue
        kind = ex.get("type")
        ref = (ex.get("ref") or "").strip()
        if kind == "quotation" or (ref and kind is None):
            m = re.match(r"\D*?(\d{4})", ref)
            year = int(m.group(1)) if m else 0
            quotations.append((year, {"text": truncate(text, MAX_QUOTATION), "ref": clean_ref(ref)}))
        elif example is None and len(text) <= MAX_EXAMPLE:
            example = text
    quotations.sort(key=lambda q: -q[0])
    out = {"pos": pos, "definition": definition}
    if example:
        out["example"] = example
    quotes = [q for _, q in quotations[:MAX_QUOTATIONS] if q["ref"]]
    if quotes:
        out["quotations"] = quotes
    syn = dedupe([s.get("word", "").strip() for s in sense.get("synonyms", []) or []])
    ant = dedupe([s.get("word", "").strip() for s in sense.get("antonyms", []) or []])
    if syn:
        out["synonyms"] = syn
    if ant:
        out["antonyms"] = ant
    tags = sorted(t for t in (sense.get("tags") or []) if t in TAG_WHITELIST)
    if tags:
        out["tags"] = tags
    topics = dedupe([t for t in (sense.get("topics") or []) if isinstance(t, str)])
    if topics:
        out["topics"] = topics[:4]
    return out


def kaikki_senses(entries: list[dict]) -> tuple[list[str], list[dict]]:
    """(part-of-speech list, senses capped per POS) in Wiktionary order."""
    pos_list: list[str] = []
    senses: list[dict] = []
    per_pos: dict[str, int] = {}
    for entry in entries:
        pos = normalize_pos(entry.get("pos"))
        if pos is None:
            continue
        if pos not in pos_list:
            pos_list.append(pos)
        for sense in entry.get("senses", []) or []:
            if per_pos.get(pos, 0) >= MAX_SENSES_PER_POS or sense_dropped(sense):
                continue
            parsed = parse_sense(sense, pos)
            if not parsed["definition"]:
                continue
            senses.append(parsed)
            per_pos[pos] = per_pos.get(pos, 0) + 1
    return pos_list, senses


def kaikki_relations(entries: list[dict], key: str) -> list[str]:
    words: list[str] = []
    for entry in entries:
        for rel in entry.get(key, []) or []:
            w = (rel.get("word") or "").strip()
            if w:
                words.append(w)
        for sense in entry.get("senses", []) or []:
            for rel in sense.get(key, []) or []:
                w = (rel.get("word") or "").strip()
                if w:
                    words.append(w)
    return dedupe(words)


def kaikki_origin(entries: list[dict]) -> tuple[list[dict], str | None]:
    origin: list[dict] = []
    root = None
    for entry in entries:
        for tpl in entry.get("etymology_templates", []) or []:
            name = tpl.get("name", "")
            args = tpl.get("args", {}) or {}
            if name == "root" and root is None:
                code = args.get("2", "")
                root_word = args.get("3", "")
                if root_word:
                    root = f"{ROOT_LANGS.get(code, code)} {root_word}".strip()
            elif name in ORIGIN_TEMPLATES:
                word = (args.get("3") or "").strip()
                expansion = re.sub(r"\s+", " ", tpl.get("expansion", "") or "").strip()
                expansion = re.sub(r"^(?:Inherited|Borrowed|Derived) from\s+", "", expansion)
                if not word or not expansion:
                    continue
                lang = expansion
                if expansion.endswith(word):
                    lang = expansion[: -len(word)].strip()
                elif word in expansion:
                    lang = expansion.split(word)[0].strip()
                lang = re.sub(r"\s*\(.*$", "", lang).strip()
                if lang and word:
                    origin.append({"lang": lang, "word": word})
        if origin or root:
            break
    return dedupe(origin, key=lambda o: (o["lang"], o["word"]))[:MAX_ORIGIN], root


def kaikki_translations(entries: list[dict]) -> dict[str, dict]:
    """code -> {"w": [words], "r": [romanizations]} from the first sense outwards."""
    out: dict[str, dict] = {}
    for entry in entries:
        for tr in entry.get("translations", []) or []:
            code = tr.get("code") or tr.get("lang_code")
            word = (tr.get("word") or "").strip()
            if not code or not word:
                continue
            slot = out.setdefault(code, {"w": [], "r": []})
            if word in slot["w"] or len(slot["w"]) >= TRANSLATIONS_PER_LANGUAGE:
                continue
            slot["w"].append(word)
            slot["r"].append((tr.get("roman") or "").strip())
    for slot in out.values():
        if not any(slot["r"]):
            slot.pop("r")
    return out


# ---------------------------------------------------------------------------
# Fetching with an on-disk cache
# ---------------------------------------------------------------------------


class Kaikki:
    """Per-word Wiktionary entries from kaikki.org, cached on disk."""

    def __init__(self, offline: bool, workers: int):
        self.offline = offline
        self.workers = max(1, workers)
        self.misses: set[str] = set()
        self.fetched = 0
        self.lock = threading.Lock()
        KAIKKI_CACHE.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def cache_name(word: str) -> str:
        return re.sub(r"[^a-z0-9'\-]", "_", word)

    def paths(self, word: str) -> tuple[Path, Path]:
        stem = self.cache_name(word)
        return KAIKKI_CACHE / f"{stem}.jsonl", KAIKKI_CACHE / f"{stem}.404"

    @staticmethod
    def url(word: str) -> str:
        return KAIKKI_URL.format(
            a=urllib.parse.quote(word[0]),
            ab=urllib.parse.quote(word[:2]),
            w=urllib.parse.quote(word),
        )

    def get(self, word: str) -> list[dict] | None:
        hit, miss = self.paths(word)
        if hit.exists():
            return self._parse(hit.read_text(encoding="utf-8"))
        if miss.exists():
            return None
        if self.offline:
            with self.lock:
                self.misses.add(word)
            return None
        text = self._download(word)
        if text is None:
            miss.write_text("")
            return None
        hit.write_text(text, encoding="utf-8")
        return self._parse(text)

    def prefetch(self, words: list[str]) -> None:
        todo = [w for w in words if not any(p.exists() for p in self.paths(w))]
        if not todo or self.offline:
            return
        print(f"  fetching {len(todo)} entries from kaikki.org with {self.workers} workers", flush=True)
        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as pool:
            for _ in pool.map(self.get, todo):
                done += 1
                if done % 200 == 0:
                    print(f"    {done}/{len(todo)}", flush=True)

    def _download(self, word: str) -> str | None:
        request = urllib.request.Request(self.url(word), headers={"User-Agent": USER_AGENT})
        for attempt in range(FETCH_RETRIES):
            try:
                with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_S) as response:
                    data = response.read().decode("utf-8")
                with self.lock:
                    self.fetched += 1
                time.sleep(FETCH_SLEEP_S)
                return data
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    time.sleep(FETCH_SLEEP_S)
                    return None
                time.sleep(2.0 * (attempt + 1))
            except (urllib.error.URLError, TimeoutError, OSError):
                time.sleep(2.0 * (attempt + 1))
        print(f"  ! giving up on {word}", file=sys.stderr)
        with self.lock:
            self.misses.add(word)
        return None

    @staticmethod
    def _parse(text: str) -> list[dict] | None:
        entries = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("lang_code", "en") == "en":
                entries.append(entry)
        return entries or None


class Zipf:
    """Zipf-scale word frequencies from the repo's own English list.

    `data/en/en_full.txt.gz` is the OpenSubtitles frequency list the keyboard
    downloads for prediction; Zipf is log10 of occurrences per billion words,
    the scale `wordfreq` popularised, so the thresholds read the same way.
    Words under [MIN_COUNT] are dropped from the table and score 0.0, which
    can never qualify as a trigger.
    """

    MIN_COUNT = 3

    def __init__(self):
        self.table: dict[str, float] = {}
        if ZIPF_CACHE.exists():
            self.table = json.loads(ZIPF_CACHE.read_text(encoding="utf-8"))
        self._counts: dict[str, int] | None = None
        self._total = 0.0

    def _load_counts(self) -> None:
        counts: dict[str, int] = {}
        total = 0
        with gzip.open(FREQUENCY_LIST, "rt", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                parts = line.rstrip("\n").rsplit(" ", 1)
                if len(parts) != 2:
                    continue
                try:
                    count = int(parts[1])
                except ValueError:
                    continue
                total += count
                if count >= self.MIN_COUNT:
                    counts[parts[0]] = count
        self._counts = counts
        self._total = float(total) or 1.0

    def get(self, word: str) -> float:
        value = self.table.get(word)
        if value is None:
            if self._counts is None:
                self._load_counts()
            count = self._counts.get(word, 0) if self._counts else 0
            value = round(math.log10(count / self._total * 1e9), 2) if count > 0 else 0.0
            self.table[word] = value
        return value

    def save(self) -> None:
        CACHE.mkdir(parents=True, exist_ok=True)
        ZIPF_CACHE.write_text(
            json.dumps(dict(sorted(self.table.items())), ensure_ascii=False, indent=0),
            encoding="utf-8",
        )


class WordNet:
    def __init__(self):
        from nltk.corpus import cmudict, stopwords, wordnet  # noqa: WPS433

        self.wn = wordnet
        self.cmu = cmudict.dict()
        self.stopwords = set(stopwords.words("english"))

    def senses(self, word: str) -> tuple[list[str], list[dict]]:
        pos_list: list[str] = []
        senses: list[dict] = []
        per_pos: dict[str, int] = {}
        for synset in self.wn.synsets(word.replace(" ", "_")):
            pos = WORDNET_POS.get(synset.pos())
            if pos is None:
                continue
            if per_pos.get(pos, 0) >= MAX_SENSES_PER_POS:
                continue
            if pos not in pos_list:
                pos_list.append(pos)
            lemmas = [l.name().replace("_", " ") for l in synset.lemmas()]
            sense = {"pos": pos, "definition": truncate(synset.definition(), MAX_DEFINITION)}
            examples = [e for e in synset.examples() if len(e) <= MAX_EXAMPLE]
            if examples:
                sense["example"] = examples[0]
            syn = [l for l in lemmas if l != word]
            if syn:
                sense["synonyms"] = syn
            ant = dedupe([a.name().replace("_", " ") for l in synset.lemmas() for a in l.antonyms()])
            if ant:
                sense["antonyms"] = ant
            senses.append(sense)
            per_pos[pos] = per_pos.get(pos, 0) + 1
        return pos_list, senses

    def synonyms(self, word: str) -> list[str]:
        out: list[str] = []
        for synset in self.wn.synsets(word.replace(" ", "_")):
            for lemma in synset.lemmas():
                name = lemma.name().replace("_", " ")
                if name != word:
                    out.append(name)
        return dedupe(out)

    def antonyms(self, word: str) -> list[str]:
        out: list[str] = []
        for synset in self.wn.synsets(word.replace(" ", "_")):
            for lemma in synset.lemmas():
                for ant in lemma.antonyms():
                    out.append(ant.name().replace("_", " "))
        return dedupe(out)

    def ipa(self, word: str) -> str | None:
        phones = self.cmu.get(word)
        if not phones:
            return None
        return arpabet_to_ipa(phones[0])


# ---------------------------------------------------------------------------
# Record assembly
# ---------------------------------------------------------------------------


def load_lists() -> list[dict]:
    specs = json.loads(LISTS_FILE.read_text(encoding="utf-8"))
    for spec in specs:
        raw = json.loads((SOURCES / "lists" / spec["file"]).read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = raw.get("words", [])
        words = []
        for value in raw:
            word = normalize_word(value)
            if word and word not in words:
                words.append(word)
        spec["words"] = words
    return specs


def load_details() -> dict:
    if not DETAILS_FILE.exists():
        return {}
    return json.loads(DETAILS_FILE.read_text(encoding="utf-8"))


def load_hand_translations() -> dict[str, dict[str, list[str]]]:
    """code -> word -> glosses, from vocab/translations/<code>.json."""
    out: dict[str, dict[str, list[str]]] = {}
    if not TRANSLATIONS.exists():
        return out
    for path in sorted(TRANSLATIONS.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
        table: dict[str, list[str]] = {}
        for word, glosses in data.items():
            key = normalize_word(word) or word.strip().lower()
            if isinstance(glosses, str):
                glosses = [glosses]
            glosses = [g.strip() for g in glosses if isinstance(g, str) and g.strip()]
            if glosses:
                table[key] = glosses[:TRANSLATIONS_PER_LANGUAGE]
        if table:
            out[path.stem] = table
    return out


class Builder:
    def __init__(self, kaikki: Kaikki, zipf: Zipf, wordnet: WordNet, details: dict,
                 sources_of: dict[str, list[str]], list_union: set[str]):
        self.kaikki = kaikki
        self.zipf = zipf
        self.wordnet = wordnet
        self.details = details
        self.sources_of = sources_of
        self.list_union = list_union
        self.stats: dict[str, int] = {}
        self.fanout: dict[str, list[tuple[str, float]]] = {}

    def bump(self, key: str) -> None:
        self.stats[key] = self.stats.get(key, 0) + 1

    def record(self, word: str) -> tuple[dict, dict[str, dict]]:
        entries = self.kaikki.get(word)
        if entries:
            self.bump("kaikki")
        else:
            self.bump("kaikki_missing")
        pos_list, senses = kaikki_senses(entries or [])
        if not senses:
            wn_pos, wn_senses = self.wordnet.senses(word)
            if wn_senses:
                self.bump("wordnet_only")
            pos_list = pos_list or wn_pos
            senses = wn_senses
        details = self.details.get(word, {}) or {}
        if not senses:
            meaning = (details.get("meaning") or "").strip()
            if meaning:
                self.bump("details_only")
                senses = [{"pos": pos_list[0] if pos_list else "", "definition": truncate(meaning, MAX_DEFINITION)}]
            else:
                self.bump("no_definition")

        ipa, audio, enpr, rhyme = kaikki_sounds(entries or [])
        if not ipa:
            cmu = self.wordnet.ipa(word)
            if cmu:
                ipa["us"] = cmu
                self.bump("ipa_cmu")
            else:
                self.bump("no_ipa")
        respelling = clean_respelling(details.get("pronunciation")) or (enpr.strip() if enpr else None)

        top_syn: list[str] = []
        top_ant: list[str] = []
        for entry in entries or []:
            top_syn += [s.get("word", "").strip() for s in entry.get("synonyms", []) or []]
            top_ant += [s.get("word", "").strip() for s in entry.get("antonyms", []) or []]
        sense_syn = [s for sense in senses for s in sense.get("synonyms", [])]
        sense_ant = [a for sense in senses for a in sense.get("antonyms", [])]
        synonyms = dedupe(top_syn + sense_syn, key=str.lower)
        antonyms = dedupe(top_ant + sense_ant, key=str.lower)
        wn_syn = self.wordnet.synonyms(word)
        if len(synonyms) < 3:
            synonyms = dedupe(synonyms + wn_syn, key=str.lower)
        if len(antonyms) < 2:
            antonyms = dedupe(antonyms + self.wordnet.antonyms(word), key=str.lower)
        synonyms = [s for s in synonyms if s.lower() != word and re.match(r"^[A-Za-z][A-Za-z' \-]*$", s)]
        antonyms = [a for a in antonyms if a.lower() != word and re.match(r"^[A-Za-z][A-Za-z' \-]*$", a)]
        synonyms.sort(key=lambda s: (-self.zipf.get(s.lower()), s.lower()))
        antonyms.sort(key=lambda s: (-self.zipf.get(s.lower()), s.lower()))
        synonyms = synonyms[:MAX_RELATED]
        antonyms = antonyms[:MAX_RELATED]

        forms = kaikki_forms(entries or [], word)
        etymology_text = ""
        for entry in entries or []:
            if entry.get("etymology_text"):
                etymology_text = entry["etymology_text"]
                break
        origin, root = kaikki_origin(entries or [])
        attested = attested_year(etymology_text, [s for e in (entries or []) for s in e.get("senses", []) or []])

        derived = [w for w in kaikki_relations(entries or [], "derived") if w.lower() != word][:MAX_FAMILY]
        related = [w for w in kaikki_relations(entries or [], "related") if w.lower() != word and w not in derived][:MAX_FAMILY]
        hypernyms = kaikki_relations(entries or [], "hypernyms")[:MAX_HYPER]
        hyponyms = kaikki_relations(entries or [], "hyponyms")[:MAX_HYPER]
        hyphenation = None
        wikipedia = None
        for entry in entries or []:
            for h in entry.get("hyphenations", []) or []:
                parts = h.get("parts") if isinstance(h, dict) else None
                if parts and len(parts) > 1:
                    hyphenation = parts
                    break
            wiki = entry.get("wikipedia")
            if wiki and wikipedia is None:
                wikipedia = wiki[0] if isinstance(wiki, list) else str(wiki)
            if hyphenation:
                break

        candidates = dedupe([s.lower() for s in synonyms] + [s.lower() for s in wn_syn])
        triggers = self.triggers(word, candidates, forms)

        record: dict = {"word": word}
        if pos_list:
            record["pos"] = pos_list
        if ipa:
            record["ipa"] = {k: ipa[k] for k in ("us", "uk") if k in ipa}
        if respelling:
            record["respelling"] = respelling
        if audio:
            record["audio"] = {k: audio[k] for k in ("us", "uk") if k in audio}
        if senses:
            record["senses"] = senses
        if synonyms:
            record["synonyms"] = synonyms
        if antonyms:
            record["antonyms"] = antonyms
        if derived or related:
            family = {}
            if derived:
                family["derived"] = derived
            if related:
                family["related"] = related
            record["family"] = family
        if hypernyms:
            record["hypernyms"] = hypernyms
        if hyponyms:
            record["hyponyms"] = hyponyms
        if forms:
            record["forms"] = forms[:MAX_FORMS]
        if hyphenation:
            record["hyphenation"] = hyphenation
        if rhyme:
            record["rhymes"] = rhyme
        etymology = clean_etymology(etymology_text) if etymology_text else ""
        if etymology:
            record["etymology"] = etymology
        if origin:
            record["origin"] = origin
        if root:
            record["root"] = root
        if attested:
            record["attested"] = attested
        if wikipedia:
            record["wikipedia"] = wikipedia
        mnemonic = (details.get("mnemonic") or "").strip()
        if mnemonic:
            record["mnemonic"] = mnemonic
        record["sources"] = self.sources_of.get(word, [])
        if triggers:
            record["triggers"] = triggers
        else:
            self.bump("no_triggers")
        return record, kaikki_translations(entries or [])

    def trigger_candidates(self, word: str) -> list[str]:
        """The synonyms that pass every trigger test except the forms lookup — what to prefetch."""
        entries = self.kaikki.get(word)
        synonyms: list[str] = []
        for entry in entries or []:
            synonyms += [x.get("word", "").strip() for x in entry.get("synonyms", []) or []]
            for sense in entry.get("senses", []) or []:
                synonyms += [x.get("word", "").strip() for x in sense.get("synonyms", []) or []]
        synonyms += self.wordnet.synonyms(word)
        zipf_w = self.zipf.get(word)
        forms = set(kaikki_forms(entries or [], word))
        out = []
        for candidate in dedupe([x.lower() for x in synonyms if x]):
            if is_trigger(candidate, word, self.zipf.get(candidate), zipf_w, self.list_union, self.wordnet.stopwords, forms):
                out.append(candidate)
        return out

    def triggers(self, word: str, candidates: list[str], word_forms: list[str]) -> list[dict]:
        zipf_w = self.zipf.get(word)
        forms_set = set(word_forms)
        out: list[dict] = []
        for candidate in candidates:
            if not is_trigger(candidate, word, self.zipf.get(candidate), zipf_w, self.list_union,
                              self.wordnet.stopwords, forms_set):
                continue
            entries = self.kaikki.get(candidate)
            forms = kaikki_forms(entries, candidate) if entries else inflect(candidate)
            forms = [f for f in forms if f not in self.list_union and f != word and TOKEN_RE.match(f)]
            gap = round(self.zipf.get(candidate) - zipf_w, 2)
            out.append({"w": candidate, "forms": forms[:6], "gap": gap})
            self.fanout.setdefault(candidate, []).append((word, gap))
        out.sort(key=lambda t: (-t["gap"], t["w"]))
        return out


def apply_fanout_cap(words: list[dict], report: list[str]) -> None:
    """Keep at most TRIGGER_FANOUT vocabulary words per trigger token, largest gap first."""
    by_trigger: dict[str, list[tuple[float, str]]] = {}
    for record in words:
        for trigger in record.get("triggers", []):
            by_trigger.setdefault(trigger["w"], []).append((trigger["gap"], record["word"]))
    keep: dict[str, set[str]] = {}
    for token, owners in sorted(by_trigger.items()):
        owners.sort(key=lambda o: (-o[0], o[1]))
        keep[token] = {w for _, w in owners[:TRIGGER_FANOUT]}
        if len(owners) > TRIGGER_FANOUT:
            dropped = [w for _, w in owners[TRIGGER_FANOUT:]]
            report.append(f"    {token}: kept {sorted(keep[token])}, dropped {dropped}")
    for record in words:
        triggers = [t for t in record.get("triggers", []) if record["word"] in keep.get(t["w"], set())]
        if triggers:
            record["triggers"] = triggers
        else:
            record.pop("triggers", None)


def encode_json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def gzip_bytes(data: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as handle:
        handle.write(data)
    return buffer.getvalue()


def build_pack(spec: dict, all_specs: list[dict], builder: Builder, hand_tr: dict,
               built: str, report: list[str]) -> tuple[dict, dict[str, dict]]:
    words: list[dict] = []
    translations: dict[str, dict] = {}  # code -> word -> {"w", "r"?}
    builder.stats.clear()
    builder.fanout.clear()
    for word in sorted(spec["words"]):
        record, tr = builder.record(word)
        words.append(record)
        for code, slot in tr.items():
            translations.setdefault(code, {})[word] = slot
    fanout_lines: list[str] = []
    apply_fanout_cap(words, fanout_lines)
    for code, table in hand_tr.items():
        target = translations.setdefault(code, {})
        for word in spec["words"]:
            glosses = table.get(word)
            if glosses:
                target[word] = {"w": glosses}
    pack = {
        "format": FORMAT,
        "version": VERSION,
        "appVersion": 0,
        "appVersionName": "wmkeyboard-data",
        "pack": {
            "id": spec["id"],
            "name": spec["name"],
            "langId": LANG,
            "description": spec.get("description", ""),
            "userCreated": False,
            "sourceId": spec["id"],
            "built": built,
            "sources": [{"id": s["id"], "name": s["name"], "short": s["short"]} for s in all_specs],
            "attribution": ATTRIBUTION + [
                {"name": f"{spec['name']} word list", "license": "list of words only", "url": ""},
            ],
        },
        "words": words,
    }
    total = len(words)
    stats = builder.stats
    report.append(f"== {spec['id']} ({spec['name']}): {total} words")
    for key in sorted(stats):
        report.append(f"    {key}: {stats[key]}")
    covered = {code: len(table) for code, table in translations.items()}
    kept = {code: n for code, n in covered.items() if n >= TRANSLATION_MIN_COVERAGE * total or code in hand_tr}
    report.append(f"    translation languages: {len(kept)} kept of {len(covered)} seen "
                  f"(>= {int(TRANSLATION_MIN_COVERAGE * 100)}% coverage)")
    if fanout_lines:
        report.append(f"    trigger fan-out capped at {TRIGGER_FANOUT}:")
        report.extend(fanout_lines)
    translations = {code: table for code, table in translations.items() if code in kept}
    return pack, translations


def write_outputs(out_dir: Path, pack: dict, translations: dict[str, dict]) -> dict[str, bytes]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, bytes] = {}
    pack_id = pack["pack"]["id"]
    files[f"{pack_id}.wmvocab.json.gz"] = gzip_bytes(encode_json(pack))
    for code in sorted(translations):
        table = {w: translations[code][w] for w in sorted(translations[code])}
        files[f"{pack_id}.tr.{code}.json.gz"] = gzip_bytes(encode_json(table))
    for name, data in files.items():
        (out_dir / name).write_bytes(data)
    # Sidecars for languages that fell under the coverage floor this run are
    # stale; remove them so the catalog never advertises a file that is gone.
    for stale in out_dir.glob(f"{pack_id}.tr.*.json.gz"):
        if stale.name not in files:
            stale.unlink()
    return files


def strip_built(data: bytes) -> bytes:
    text = gzip.decompress(data).decode("utf-8")
    return re.sub(r'"built":"[^"]*"', '"built":""', text).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lists", default="", help="comma-separated list ids (default: all)")
    parser.add_argument("--out", default=str(VOCAB / LANG), help="output directory")
    parser.add_argument("--offline", action="store_true", help="never touch the network")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--check", action="store_true", help="rebuild and compare with the checked-in files")
    parser.add_argument("--no-report", action="store_true", help="do not rewrite vocab/build-report.txt")
    args = parser.parse_args(argv)

    specs = load_lists()
    wanted = [s.strip() for s in args.lists.split(",") if s.strip()] or [s["id"] for s in specs]
    unknown = [w for w in wanted if w not in {s["id"] for s in specs}]
    if unknown:
        parser.error(f"unknown list id(s): {', '.join(unknown)}")
    selected = [s for s in specs if s["id"] in wanted]

    sources_of: dict[str, list[str]] = {}
    for spec in specs:
        for word in spec["words"]:
            sources_of.setdefault(word, []).append(spec["id"])
    list_union = set(sources_of)

    kaikki = Kaikki(offline=args.offline, workers=args.workers)
    zipf = Zipf()
    wordnet = WordNet()
    details = load_details()
    hand_tr = load_hand_translations()
    builder = Builder(kaikki, zipf, wordnet, details, sources_of, list_union)

    selected_words = sorted({w for s in selected for w in s["words"]})
    print(f"building {len(selected)} pack(s), {len(selected_words)} distinct words", flush=True)
    kaikki.prefetch(selected_words)
    # The trigger pass looks every candidate synonym up for its inflections;
    # fetched here in parallel rather than one at a time inside the record loop.
    candidates = sorted({c for w in selected_words for c in builder.trigger_candidates(w)})
    print(f"  {len(candidates)} trigger candidates", flush=True)
    kaikki.prefetch(candidates)

    built = _dt.date.today().isoformat()
    report: list[str] = [
        "# Vocabulary pack build report",
        f"built: {built}",
        f"lists: {', '.join(s['id'] for s in selected)}",
        "",
    ]
    out_dir = Path(args.out)
    outputs: dict[str, bytes] = {}
    for spec in selected:
        print(f"  {spec['id']}: {len(spec['words'])} words", flush=True)
        pack, translations = build_pack(spec, specs, builder, hand_tr, built, report)
        if args.check:
            pack_id = pack["pack"]["id"]
            outputs[f"{pack_id}.wmvocab.json.gz"] = gzip_bytes(encode_json(pack))
            for code in sorted(translations):
                table = {w: translations[code][w] for w in sorted(translations[code])}
                outputs[f"{pack_id}.tr.{code}.json.gz"] = gzip_bytes(encode_json(table))
        else:
            files = write_outputs(out_dir, pack, translations)
            for name, data in files.items():
                print(f"    wrote {name} ({len(data):,} bytes)", flush=True)
    zipf.save()
    if kaikki.misses:
        report.append("")
        report.append(f"offline/failed fetches ({len(kaikki.misses)}): {', '.join(sorted(kaikki.misses))}")
    if args.check:
        failed = []
        for name, data in outputs.items():
            existing = out_dir / name
            if not existing.exists() or strip_built(existing.read_bytes()) != strip_built(data):
                failed.append(name)
        if failed:
            print("CHECK FAILED — differs from checked-in files:\n  " + "\n  ".join(failed))
            return 1
        print(f"check passed: {len(outputs)} file(s) identical")
        return 0
    if not args.no_report:
        REPORT_FILE.write_text("\n".join(report) + "\n", encoding="utf-8")
        print(f"report: {REPORT_FILE.relative_to(REPO)}")
    print(f"done ({kaikki.fetched} new fetches)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

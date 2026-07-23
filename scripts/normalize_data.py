#!/usr/bin/env python3
"""
Normalize multilingual keyboard wordlists.
Features:
- Unicode NFKC normalization
- Mojibake repair
- Garbage filtering
- Script validation
- Frequency normalization
- Duplicate merging
- Keyboard-oriented cleanup
"""

import gzip
import json
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MIN_FREQUENCY = {
    "default": 2,
}
# ----------------------------------------------------------------------
# Language script hints
# ----------------------------------------------------------------------
LANGUAGE_SCRIPTS = {
    "af": "Latin",
    "am": "Ethiopic",
    "ar": "Arabic",
    "as": "Bengali",
    "az": "Latin",
    "be": "Cyrillic",
    "bg": "Cyrillic",
    "bn": "Bengali",
    "br": "Latin",
    "bs": "Latin",
    "ca": "Latin",
    "cs": "Latin",
    "da": "Latin",
    "de": "Latin",
    "el": "Greek",
    "en": "Latin",
    "eo": "Latin",
    "es": "Latin",
    "et": "Latin",
    "eu": "Latin",
    "fa": "Arabic",
    "fi": "Latin",
    "fr": "Latin",
    "gl": "Latin",
    "gu": "Gujarati",
    "ha": "Latin",
    "he": "Hebrew",
    "hi": "Devanagari",
    "hr": "Latin",
    "hu": "Latin",
    "hy": "Armenian",
    "id": "Latin",
    "ig": "Latin",
    "is": "Latin",
    "it": "Latin",
    "ja": None,
    "jbo": "Latin",
    "ka": "Georgian",
    "kk": "Cyrillic",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Hangul",
    "lo": "Lao",
    "lt": "Latin",
    "lv": "Latin",
    "mk": "Cyrillic",
    "ml": "Malayalam",
    "mn": "Cyrillic",
    "mr": "Devanagari",
    "ms": "Latin",
    "my": "Myanmar",
    "ne": "Devanagari",
    "nl": "Latin",
    "no": "Latin",
    "pa": "Gurmukhi",
    "pl": "Latin",
    "pt": "Latin",
    "pt_br": "Latin",
    "ro": "Latin",
    "ru": "Cyrillic",
    "si": "Sinhala",
    "sk": "Latin",
    "sl": "Latin",
    "sq": "Latin",
    "sr": "Cyrillic",
    "sv": "Latin",
    "sw": "Latin",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "or": "Oriya",
    "tl": "Latin",
    "tlh": "Latin",
    "tr": "Latin",
    "uk": "Cyrillic",
    "ur": "Arabic",
    "uz": "Latin",
    "vi": "Latin",
    "yo": "Latin",
    "zh_cn": None,
    "zh_tw": None,
    "zu": "Latin",
}
# ----------------------------------------------------------------------
# Regex
# ----------------------------------------------------------------------
URL_RE = re.compile(
    r"(https?://|www\.|ftp://)",
    re.I,
)
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}$")
HASH_RE = re.compile(r"^[a-fA-F0-9]{16,}$")
YEAR_RE = re.compile(r"^\d{4}[−–-]\d{2,4}$")
EPISODE_RE = re.compile(
    r"^\d+x\d+$",
    re.I,
)
CODE_RE = re.compile(r"^[A-Z]{1,3}\d+$|^\d+[A-Z]{1,3}$")
MOJIBAKE_RE = re.compile(r"(Ã.|Â.|â€.|â€™|â€œ|â€�|ï¿½)")


# ----------------------------------------------------------------------
# Unicode helpers
# ----------------------------------------------------------------------
def normalize_unicode(word):
    word = unicodedata.normalize("NFKC", word)
    word = unicodedata.normalize("NFC", word)
    return word


def contains_letter(text):
    return any(c.isalpha() for c in text)


def is_only_symbols(text):
    if not text:
        return True
    return not contains_letter(text) and all(
        unicodedata.category(c)[0] in ("P", "S") for c in text
    )


# ----------------------------------------------------------------------
# Mojibake
# ----------------------------------------------------------------------
def fix_mojibake(word):
    if not MOJIBAKE_RE.search(word):
        return word, False
    try:
        fixed = word.encode("latin1").decode("utf-8")
        if fixed != word:
            return fixed, True
    except Exception:
        pass
    return word, False


# ----------------------------------------------------------------------
# Garbage detection
# ----------------------------------------------------------------------
def is_garbage(word):
    if not word:
        return True
    if URL_RE.search(word):
        return True
    if EMAIL_RE.match(word):
        return True
    if HASH_RE.match(word):
        return True
    if YEAR_RE.match(word):
        return True
    if EPISODE_RE.match(word):
        return True
    if CODE_RE.match(word):
        return True
    if is_only_symbols(word):
        return True
    letters = sum(c.isalpha() for c in word)
    digits = sum(c.isdigit() for c in word)
    # Short random identifiers
    if 1 <= letters <= 2 and 2 <= digits <= 3 and len(word) <= 6:
        return True
    return False


# ----------------------------------------------------------------------
# Script checking
# ----------------------------------------------------------------------
def get_script(char: str) -> str:
    """
    Extracts the primary script name from a Unicode character's designation.
    (e.g., 'LATIN', 'CYRILLIC', 'ARABIC').
    """
    name = unicodedata.name(char, "")
    # The script is typically the first word in the unicode name
    return name.split(" ")[0] if name else ""


def valid_script(word: str, language: str) -> bool:
    expected = LANGUAGE_SCRIPTS.get(language)

    if not expected:
        # Warning: This allows mixed-script words to slip through in ja, zh_cn, zh_tw
        return True

    allowed_script = expected.upper()
    has_letters = False

    for char in word:
        if char.isalpha():
            has_letters = True
            name = unicodedata.name(char, "")

            # 1. Primary check: Does the character belong to the expected script?
            if allowed_script in name:
                continue

            # 2. Exception: Safelist cross-script linguistic modifier letters
            # This saves Uzbek, Ukrainian, Belarusian, and Breton words
            if name.startswith("MODIFIER LETTER"):
                continue

            # 3. Exception: Safelist Roman numerals for Latin languages
            if allowed_script == "LATIN" and name.startswith("ROMAN NUMERAL"):
                continue

            # If it is a letter but fails all checks, reject the word
            return False

    return has_letters


# ----------------------------------------------------------------------
# Parsing
# ----------------------------------------------------------------------
def parse_lines(lines):
    result = []
    had_float = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        word = None
        freq = 1.0
        parts = line.rsplit(" ", 1)
        if len(parts) == 2:
            word, value = parts
            try:
                freq = float(value)
                if "." in value:
                    had_float = True
            except ValueError:
                # FIX: Check if the line is a duplicated word (e.g., "the the")
                if word == value:
                    freq = 1.0  # Keep the single 'word', use default frequency
                else:
                    word = line
                    freq = 1.0
        else:
            word = parts[0]
        result.append((word.strip(), freq))
    return result, had_float


# ----------------------------------------------------------------------
# Frequency conversion
# ----------------------------------------------------------------------
def normalize_frequency(entries):
    entries = [(w, f) for w, f in entries if not (isinstance(f, float) and f != f)]
    if not entries:
        return []
    if not any(
        isinstance(freq, float) and not freq.is_integer() for _, freq in entries
    ):
        return [(w, int(f)) for w, f in entries]
    maximum = max(f for _, f in entries)
    if maximum == 0:
        return [(w, 0) for w, _ in entries]
    scale = 1_000_000 / maximum
    return [(w, max(1, round(f * scale))) for w, f in entries]


def normalize_apostrophes(word):
    return word.replace("’", "'").replace("ʻ", "'").replace("ʼ", "'").replace("`", "'")


# ----------------------------------------------------------------------
# Main processing
# ----------------------------------------------------------------------
def process_file(path):
    language = path.parent.name
    print(f"\nProcessing {path}")
    offensive = "_offensive" in path.name
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    entries, had_float = parse_lines(lines)
    stats = defaultdict(int)
    cleaned = []
    for word, freq in entries:
        original = word
        word = normalize_unicode(word)
        word = normalize_apostrophes(word)
        word, fixed = fix_mojibake(word)
        if fixed:
            stats["mojibake_fixed"] += 1
        word = word.strip()
        if not word:
            stats["empty"] += 1
            continue
        if is_garbage(word):
            stats["garbage"] += 1
            continue
        # Skip script validation for offensive lists
        if not offensive:
            if not valid_script(word, language):
                stats["foreign_script"] += 1
                continue
        cleaned.append((word, freq))
    cleaned = normalize_frequency(cleaned)
    merged = {}
    for word, freq in cleaned:
        if word not in merged or freq > merged[word]:
            merged[word] = freq
    result = sorted(merged.items(), key=lambda x: (-x[1], x[0]))
    tmp = path.with_suffix(".tmp.gz")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for word, freq in result:
            f.write(f"{word} {freq}\n")
    tmp.replace(path)
    report = {
        "file": str(path),
        "before": len(entries),
        "after": len(result),
        "removed": dict(stats),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main():
    files = sorted(DATA_DIR.glob("*/*_full.txt.gz"))
    reports = []
    for file in files:
        reports.append(process_file(file))
    with open("normalization_report.json", "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

"""Deterministic romanisations for vocabulary translations.

A translation sidecar carries, per gloss, a romanisation (`r`) beside the
word (`w`). Wiktionary supplies most of them; the hand-written Bengali
glosses carry none, and a handful of other entries come through blank. This
module fills the gaps the same way every time, so a rebuild changes nothing
and the app can rely on the spelling: it matches what the user types on a
romanised layout against these strings to nudge the English word.

Two real transliterators and one fallback:

* Bengali is spelt the way people type it on a phonetic (Avro) layout —
  "ghrina", "bhalo", "shobdo" — not the way a library does it ("ghr̥ṇā").
  The inherent vowel is written `o` except at the end of a word, where
  Bengali drops it unless the word ends in a conjunct.
* Cyrillic follows the plain Russian-style table with the Serbian, Ukrainian,
  Belarusian, Kazakh and Macedonian extras.
* Everything else goes through `unidecode` when it is installed, and stays
  blank when it is not.

Latin-script words (including Vietnamese and Turkish, whose diacritics the
app folds itself) are never romanised.
"""

from __future__ import annotations

import unicodedata

try:  # pragma: no cover - exercised only where the package is installed
    from unidecode import unidecode as _unidecode
except ImportError:  # pragma: no cover
    _unidecode = None

# ---------------------------------------------------------------------------
# Bengali
# ---------------------------------------------------------------------------

BN_CONSONANTS = {
    "ক": "k", "খ": "kh", "গ": "g", "ঘ": "gh", "ঙ": "ng",
    "চ": "ch", "ছ": "chh", "জ": "j", "ঝ": "jh", "ঞ": "n",
    "ট": "t", "ঠ": "th", "ড": "d", "ঢ": "dh", "ণ": "n",
    "ত": "t", "থ": "th", "দ": "d", "ধ": "dh", "ন": "n",
    "প": "p", "ফ": "f", "ব": "b", "ভ": "bh", "ম": "m",
    "য": "j", "র": "r", "ল": "l", "শ": "sh", "ষ": "sh", "স": "s", "হ": "h",
    "ড়": "r", "ঢ়": "rh", "য়": "y", "ৎ": "t",
}
# Nukta forms may arrive decomposed (base + U+09BC); NFC does not recompose them.
BN_NUKTA = {"ড": "r", "ঢ": "rh", "য": "y"}
BN_VOWELS = {
    "অ": "o", "আ": "a", "ই": "i", "ঈ": "i", "উ": "u", "ঊ": "u",
    "ঋ": "ri", "এ": "e", "ঐ": "oi", "ও": "o", "ঔ": "ou",
}
BN_VOWEL_SIGNS = {
    "া": "a", "ি": "i", "ী": "i", "ু": "u", "ূ": "u", "ৃ": "ri",
    "ে": "e", "ৈ": "oi", "ো": "o", "ৌ": "ou",
}
BN_HASANTA = "্"
BN_NUKTA_SIGN = "়"
BN_ANUSVARA = "ং"
BN_VISARGA = "ঃ"
BN_CHANDRABINDU = "ঁ"
BN_DIGITS = {chr(0x09E6 + i): str(i) for i in range(10)}
# Khanda-ta never takes a vowel; it is written without the inherent one.
BN_NO_INHERENT = {"ৎ"}


def _romanize_bengali_word(word: str) -> str:
    chars = list(word)
    out: list[str] = []
    i = 0
    # Whether the consonant about to be written continues a conjunct (or
    # follows a visarga, which doubles the next consonant): a word ending in
    # one keeps its inherent vowel ("shobdo"), a plain final consonant does
    # not ("mon").
    in_conjunct = False
    n = len(chars)
    while i < n:
        ch = chars[i]
        if ch in BN_CONSONANTS:
            base = BN_CONSONANTS[ch]
            if i + 1 < n and chars[i + 1] == BN_NUKTA_SIGN and ch in BN_NUKTA:
                base = BN_NUKTA[ch]
                i += 1
            out.append(base)
            nxt = chars[i + 1] if i + 1 < n else ""
            if nxt == BN_HASANTA:
                # Ya-phala is a glide, not a consonant: ব্যক্তি is "byokti".
                if i + 2 < n and chars[i + 2] == "য" and not (i + 3 < n and chars[i + 3] == BN_NUKTA_SIGN):
                    out.append("y")
                    in_conjunct = True
                    i += 3
                    # The glide carries the vowel that follows it.
                    nxt2 = chars[i] if i < n else ""
                    if nxt2 == BN_HASANTA:
                        i += 1
                        continue
                    if nxt2 in BN_VOWEL_SIGNS:
                        out.append(BN_VOWEL_SIGNS[nxt2])
                        in_conjunct = False
                        i += 1
                        continue
                    # A bare glide keeps its vowel even at the end: "sahajyo".
                    out.append("o")
                    in_conjunct = False
                    continue
                in_conjunct = True
                i += 2
                continue
            if nxt in BN_VOWEL_SIGNS:
                out.append(BN_VOWEL_SIGNS[nxt])
                in_conjunct = False
                i += 2
                continue
            if ch in BN_NO_INHERENT:
                in_conjunct = False
                i += 1
                continue
            # Inherent vowel: written unless the consonant ends the word and
            # is not the tail of a conjunct.
            final = (i + 1 >= n) or (chars[i + 1] == BN_CHANDRABINDU and i + 2 >= n)
            if not final or in_conjunct:
                out.append("o")
            in_conjunct = False
            i += 1
            continue
        if ch in BN_VOWELS:
            out.append(BN_VOWELS[ch])
            in_conjunct = False
            i += 1
            continue
        if ch in BN_VOWEL_SIGNS:
            # A stray sign with no consonant before it: write the vowel anyway.
            out.append(BN_VOWEL_SIGNS[ch])
            i += 1
            continue
        if ch == BN_ANUSVARA:
            out.append("ng")
            in_conjunct = False
            i += 1
            continue
        if ch == BN_VISARGA:
            # Doubles the following consonant ("dukkho"); silent at the end.
            if i + 1 < n and chars[i + 1] in BN_CONSONANTS:
                out.append(BN_CONSONANTS[chars[i + 1]][0])
                in_conjunct = True
            i += 1
            continue
        if ch in (BN_CHANDRABINDU, BN_HASANTA, BN_NUKTA_SIGN):
            i += 1
            continue
        if ch in BN_DIGITS:
            out.append(BN_DIGITS[ch])
            i += 1
            continue
        out.append(ch)
        in_conjunct = False
        i += 1
    return "".join(out)


def romanize_bengali(text: str) -> str:
    """Bengali script as typed on a phonetic layout: "ঘৃণা" → "ghrina"."""
    return " ".join(_romanize_bengali_word(w) for w in unicodedata.normalize("NFC", text).split(" "))


# ---------------------------------------------------------------------------
# Cyrillic
# ---------------------------------------------------------------------------

CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    # Ukrainian and Belarusian
    "і": "i", "ї": "yi", "є": "ye", "ґ": "g", "ў": "w",
    # Serbian and Macedonian
    "ђ": "dj", "ј": "j", "љ": "lj", "њ": "nj", "ћ": "c", "џ": "dz",
    "ѓ": "gj", "ѕ": "dz", "ќ": "kj",
    # Kazakh and the other Turkic ones
    "ә": "a", "ғ": "gh", "қ": "q", "ң": "ng", "ө": "o", "ұ": "u", "ү": "u", "һ": "h",
    # Bulgarian
    "ѫ": "a",
}


def romanize_cyrillic(text: str) -> str:
    out = []
    for ch in unicodedata.normalize("NFC", text):
        lower = ch.lower()
        if lower in CYRILLIC:
            mapped = CYRILLIC[lower]
            out.append(mapped.capitalize() if ch != lower and mapped else mapped)
        else:
            out.append(ch)
    return "".join(out)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def _is_latin_letter(ch: str) -> bool:
    code = ord(ch)
    return code < 0x0250 or 0x1E00 <= code <= 0x1EFF or 0x2C60 <= code <= 0x2C7F or 0xA720 <= code <= 0xA7FF


def needs_romanization(text: str) -> bool:
    """True when the text has a letter from a non-Latin script."""
    return any(unicodedata.category(ch).startswith("L") and not _is_latin_letter(ch) for ch in text)


def _script_of(text: str) -> str:
    for ch in text:
        if not unicodedata.category(ch).startswith("L"):
            continue
        code = ord(ch)
        if 0x0980 <= code <= 0x09FF:
            return "bengali"
        if 0x0400 <= code <= 0x052F:
            return "cyrillic"
    return "other"


def romanize(text: str, code: str = "") -> str:
    """The romanisation of [text], or "" when nothing here can spell it."""
    if not needs_romanization(text):
        return ""
    script = _script_of(text)
    if script == "bengali":
        return romanize_bengali(text)
    if script == "cyrillic":
        return romanize_cyrillic(text)
    if _unidecode is None:
        return ""
    romanized = " ".join(_unidecode(text).split()).strip()
    # A string the fallback could not read comes back as its own question marks.
    return "" if not romanized or set(romanized) <= {"?", " "} else romanized


def fill_romanizations(table: dict[str, dict]) -> int:
    """
    Adds `r` beside every non-Latin `w` that lacks one, in place, keeping the
    two lists aligned; returns how many were added.
    """
    added = 0
    for slot in table.values():
        words = slot.get("w") or []
        romans = list(slot.get("r") or [])
        romans += [""] * (len(words) - len(romans))
        for i, word in enumerate(words):
            if romans[i]:
                continue
            spelled = romanize(word)
            if spelled:
                romans[i] = spelled
                added += 1
        if any(romans):
            slot["r"] = romans[: len(words)]
        else:
            slot.pop("r", None)
    return added

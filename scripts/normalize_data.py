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

import argparse
import gzip
import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REPO_DIR = DATA_DIR.parent
MIN_FREQUENCY = {
    "default": 2,
}


def is_subpath(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def get_git_changed_files() -> list[Path]:
    """
    Query git status to find new or updated data files.
    Returns a sorted list of Path objects for matching files.
    """
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain", "-z", "-uall"],
            cwd=REPO_DIR,
            capture_output=True,
            check=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"Error executing git status: {e}")
        return []

    raw = res.stdout
    if not raw:
        return []

    entries = raw.split(b"\x00")
    changed_files = []
    i = 0
    while i < len(entries):
        entry = entries[i]
        if not entry:
            i += 1
            continue

        status = entry[:2].decode("utf-8", errors="replace")
        path_str = entry[3:].decode("utf-8", errors="replace")

        # If status indicates rename or copy, skip the original path entry following it
        if "R" in status or "C" in status:
            i += 1

        if path_str:
            file_path = (REPO_DIR / path_str).resolve()
            if (
                file_path.is_file()
                and file_path.name.endswith(".txt.gz")
                and is_subpath(file_path, DATA_DIR)
            ):
                changed_files.append(file_path)

        i += 1

    return sorted(set(changed_files))

# ----------------------------------------------------------------------
# Language script hints
# ----------------------------------------------------------------------
LANGUAGE_SCRIPTS = {
    'aa': 'Latin',
    'ab': 'Cyrillic',
    'ace': 'Latin',
    'ady': 'Cyrillic',
    'af': 'Latin',
    'ak': 'Latin',
    'alt': 'Cyrillic',
    'am': 'Ethiopic',
    'ami': 'Latin',
    'an': 'Latin',
    'ang': 'Latin',
    'ann': 'Latin',
    'anp': 'Devanagari',
    'ar': 'Arabic',
    'arc': 'Syriac',
    'ary': 'Arabic',
    'arz': 'Arabic',
    'as': 'Bengali',
    'ast': 'Latin',
    'atj': 'Latin',
    'av': 'Cyrillic',
    'avk': 'Latin',
    'awa': 'Devanagari',
    'ay': 'Latin',
    'az': 'Latin',
    'azb': 'Arabic',
    'ba': 'Cyrillic',
    'ban': 'Latin',
    'bar': 'Latin',
    'bbc': 'Latin',
    'bcl': 'Latin',
    'bdr': 'Latin',
    'be': 'Cyrillic',
    'be-tarask': 'Cyrillic',
    'bew': 'Latin',
    'bg': 'Cyrillic',
    'bgn': 'Arabic',
    'bh': 'Devanagari',
    'bho': 'Devanagari',
    'bi': 'Latin',
    'bik': 'Latin',
    'bjn': 'Latin',
    'blk': 'Myanmar',
    'blo': 'Latin',
    'bm': 'Latin',
    'bn': 'Bengali',
    'bo': 'Tibetan',
    'bol': 'Latin',
    'bpy': 'Bengali',
    'br': 'Latin',
    'brx': 'Devanagari',
    'bs': 'Latin',
    'btm': 'Latin',
    'bua': 'Cyrillic',
    'bug': 'Latin',
    'bxr': 'Cyrillic',
    'ca': 'Latin',
    'cbk': 'Latin',
    'cbk-zam': 'Latin',
    'ccp': ('Chakma', 'Latin'),
    'cdo': ('Latin', 'CJK'),
    'ce': 'Cyrillic',
    'ceb': 'Latin',
    'ch': 'Latin',
    'chr': 'Cherokee',
    'chy': 'Latin',
    'ckb': 'Arabic',
    'co': 'Latin',
    'cr': ('Canadian', 'Latin'),
    'crh': ('Cyrillic', 'Latin'),
    'cs': 'Latin',
    'csb': 'Latin',
    'cu': 'Cyrillic',
    'cv': 'Cyrillic',
    'cy': 'Latin',
    'da': 'Latin',
    'dag': 'Latin',
    'de': 'Latin',
    'dga': 'Latin',
    'din': 'Latin',
    'diq': 'Latin',
    'div': 'Thaana',
    'doi': 'Devanagari',
    'dsb': 'Latin',
    'dtp': 'Latin',
    'dty': 'Devanagari',
    'dv': 'Thaana',
    'dz': 'Tibetan',
    'ee': 'Latin',
    'el': 'Greek',
    'eml': 'Latin',
    'en': 'Latin',
    'eo': 'Latin',
    'es': 'Latin',
    'et': 'Latin',
    'eu': 'Latin',
    'ext': 'Latin',
    'fa': 'Arabic',
    'fat': 'Latin',
    'ff': 'Latin',
    'fi': 'Latin',
    'fil': 'Latin',
    'fj': 'Latin',
    'fo': 'Latin',
    'fon': 'Latin',
    'fr': 'Latin',
    'frp': 'Latin',
    'frr': 'Latin',
    'fur': 'Latin',
    'fy': 'Latin',
    'ga': 'Latin',
    'gag': 'Latin',
    'gan': None,
    'gcr': 'Latin',
    'gd': 'Latin',
    'gl': 'Latin',
    'glk': 'Arabic',
    'gn': 'Latin',
    'gom': 'Devanagari',
    'gor': 'Latin',
    'got': 'Gothic',
    'gpe': 'Latin',
    'gsw': 'Latin',
    'gu': 'Gujarati',
    'guc': 'Latin',
    'gur': 'Latin',
    'guw': 'Latin',
    'gv': 'Latin',
    'ha': 'Latin',
    'hak': ('Latin', 'CJK'),
    'haw': 'Latin',
    'he': 'Hebrew',
    'hi': 'Devanagari',
    'hif': ('Devanagari', 'Latin'),
    'hr': 'Latin',
    'hsb': 'Latin',
    'ht': 'Latin',
    'hu': 'Latin',
    'hy': 'Armenian',
    'hyw': 'Armenian',
    'ia': 'Latin',
    'iba': 'Latin',
    'id': 'Latin',
    'ie': 'Latin',
    'ig': 'Latin',
    'igl': 'Latin',
    'ik': 'Latin',
    'ilo': 'Latin',
    'inh': 'Cyrillic',
    'io': 'Latin',
    'is': 'Latin',
    'isv': 'Latin',
    'it': 'Latin',
    'iu': 'Canadian',
    'ja': None,
    'jam': 'Latin',
    'jbo': 'Latin',
    'jv': 'Latin',
    'ka': 'Georgian',
    'kaa': ('Cyrillic', 'Latin'),
    'kab': 'Latin',
    'kai': 'Latin',
    'kaj': 'Latin',
    'kbd': 'Cyrillic',
    'kbp': 'Latin',
    'kcg': 'Latin',
    'kck': 'Latin',
    'kg': 'Latin',
    'kge': 'Latin',
    'ki': 'Latin',
    'kk': 'Cyrillic',
    'kl': 'Latin',
    'km': 'Khmer',
    'kn': 'Kannada',
    'knc': 'Latin',
    'ko': 'Hangul',
    'koi': 'Cyrillic',
    'kok': 'Latin',
    'krc': 'Cyrillic',
    'ks': ('Arabic', 'Devanagari'),
    'ksh': 'Latin',
    'ku': 'Arabic',
    'kus': 'Latin',
    'kv': 'Cyrillic',
    'kw': 'Latin',
    'ky': 'Cyrillic',
    'la': 'Latin',
    'lad': ('Latin', 'Hebrew'),
    'lb': 'Latin',
    'lbe': 'Cyrillic',
    'lez': 'Cyrillic',
    'lfn': 'Latin',
    'lg': 'Latin',
    'li': 'Latin',
    'lij': 'Latin',
    'lld': 'Latin',
    'lmo': 'Latin',
    'ln': 'Latin',
    'lo': 'Lao',
    'loz': 'Latin',
    'lt': 'Latin',
    'ltg': 'Latin',
    'lub': 'Latin',
    'lv': 'Latin',
    'lzh': None,
    'mad': 'Latin',
    'mag': 'Devanagari',
    'mai': 'Devanagari',
    'map-bms': 'Latin',
    'mdf': 'Cyrillic',
    'mg': 'Latin',
    'mhr': 'Cyrillic',
    'mi': 'Latin',
    'min': 'Latin',
    'mk': 'Cyrillic',
    'ml': 'Malayalam',
    'mn': 'Cyrillic',
    'mni': 'Meetei',
    'mnw': 'Myanmar',
    'mos': 'Latin',
    'mr': 'Devanagari',
    'mrj': 'Cyrillic',
    'ms': 'Latin',
    'mt': 'Latin',
    'mwl': 'Latin',
    'my': 'Myanmar',
    'myv': 'Cyrillic',
    'mzn': 'Arabic',
    'nah': 'Latin',
    'nan': ('Latin', 'CJK'),
    'nap': 'Latin',
    'nb': 'Latin',
    'nd': 'Latin',
    'nds': 'Latin',
    'nds-nl': 'Latin',
    'ne': 'Devanagari',
    'new': 'Devanagari',
    'nia': 'Latin',
    'nl': 'Latin',
    'nn': 'Latin',
    'no': 'Latin',
    'nov': 'Latin',
    'nqo': 'Nko',
    'nr': 'Latin',
    'nrm': 'Latin',
    'nso': 'Latin',
    'nup': 'Latin',
    'nv': 'Latin',
    'ny': 'Latin',
    'oc': 'Latin',
    'olo': 'Latin',
    'om': 'Latin',
    'or': 'Oriya',
    'os': 'Cyrillic',
    'pa': 'Gurmukhi',
    'pag': 'Latin',
    'pam': 'Latin',
    'pap': 'Latin',
    'pcd': 'Latin',
    'pcm': 'Latin',
    'pdc': 'Latin',
    'pfl': 'Latin',
    'pi': 'Devanagari',
    'pl': 'Latin',
    'plt': 'Latin',
    'pms': 'Latin',
    'pnb': 'Arabic',
    'pnt': 'Greek',
    'ppl': 'Latin',
    'ps': 'Arabic',
    'pt': 'Latin',
    'pt_br': 'Latin',
    'pwn': 'Latin',
    'qu': 'Latin',
    'quc': 'Latin',
    'qya': 'Latin',
    'raj': 'Devanagari',
    'rif': ('Tifinagh', 'Latin', 'Arabic'),
    'rhg': ('Hanifi', 'Arabic', 'Latin'),
    'rki': 'Myanmar',
    'rm': 'Latin',
    'rmy': 'Latin',
    'rn': 'Latin',
    'ro': 'Latin',
    'roa-tara': 'Latin',
    'rsk': 'Cyrillic',
    'ru': 'Cyrillic',
    'rue': 'Cyrillic',
    'rup': 'Latin',
    'rw': 'Latin',
    'sa': 'Devanagari',
    'sah': 'Cyrillic',
    'sat': 'Ol Chiki',
    'sc': 'Latin',
    'scn': 'Latin',
    'sco': 'Latin',
    'sd': 'Arabic',
    'se': 'Latin',
    'sg': 'Latin',
    'sgs': 'Latin',
    'sh': 'Latin',
    'shi': ('Tifinagh', 'Latin'),
    'shn': 'Myanmar',
    'si': 'Sinhala',
    'sk': 'Latin',
    'skr': 'Arabic',
    'sl': 'Latin',
    'sm': 'Latin',
    'smn': 'Latin',
    'sn': 'Latin',
    'sna': 'Latin',
    'so': 'Latin',
    'sq': 'Latin',
    'sr': 'Cyrillic',
    'srn': 'Latin',
    'ss': 'Latin',
    'ssw': 'Latin',
    'st': 'Latin',
    'stq': 'Latin',
    'su': 'Latin',
    'sun': 'Latin',
    'sv': 'Latin',
    'sw': 'Latin',
    'syl': ('Syloti', 'Bengali'),
    'syr': 'Syriac',
    'szl': 'Latin',
    'szy': 'Latin',
    'ta': 'Tamil',
    'tay': 'Latin',
    'tcy': 'Kannada',
    'tdd': 'Tai',
    'te': 'Telugu',
    'tet': 'Latin',
    'tg': 'Cyrillic',
    'th': 'Thai',
    'ti': 'Ethiopic',
    'tig': 'Ethiopic',
    'tk': 'Latin',
    'tl': 'Latin',
    'tlh': 'Latin',
    'tly': ('Arabic', 'Cyrillic', 'Latin'),
    'tn': 'Latin',
    'to': 'Latin',
    'tok': 'Latin',
    'tpi': 'Latin',
    'tr': 'Latin',
    'trv': 'Latin',
    'ts': 'Latin',
    'tt': 'Cyrillic',
    'tum': 'Latin',
    'tw': 'Latin',
    'ty': 'Latin',
    'tyv': 'Cyrillic',
    'udm': 'Cyrillic',
    'ug': 'Arabic',
    'uk': 'Cyrillic',
    'ur': 'Arabic',
    'uz': 'Latin',
    've': 'Latin',
    'vec': 'Latin',
    'vep': 'Latin',
    'vi': 'Latin',
    'vls': 'Latin',
    'vo': 'Latin',
    'vro': 'Latin',
    'wa': 'Latin',
    'war': 'Latin',
    'wo': 'Latin',
    'wuu': None,
    'xal': 'Cyrillic',
    'xh': 'Latin',
    'xmf': 'Georgian',
    'yi': 'Hebrew',
    'yo': 'Latin',
    'yue': None,
    'yue_Hans': None,
    'za': 'Latin',
    'ze_en': 'Latin',
    'ze_zh': None,
    'zea': 'Latin',
    'zgh': 'Tifinagh',
    'zh': None,
    'zh_cn': None,
    'zh_tw': None,
    'zu': 'Latin',
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
MOJIBAKE_RE = re.compile(r"(Ã.|Â.|â€.|â€™|â€œ|â€|ï¿½)")


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

    if isinstance(expected, (list, tuple)):
        allowed_scripts = [s.upper() for s in expected]
    else:
        allowed_scripts = [expected.upper()]
    has_letters = False

    for char in word:
        if char.isalpha():
            has_letters = True
            name = unicodedata.name(char, "")

            # 1. Primary check: Does the character belong to the expected script?
            if any(s in name for s in allowed_scripts):
                continue

            # 2. Exception: Safelist cross-script linguistic modifier letters
            # This saves Uzbek, Ukrainian, Belarusian, and Breton words
            if name.startswith("MODIFIER LETTER"):
                continue

            # 3. Exception: Safelist Roman numerals for Latin languages
            if "LATIN" in allowed_scripts and name.startswith("ROMAN NUMERAL"):
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
    # Securely create a temp file name by appending .tmp to the full original name
    tmp = path.parent / f"{path.name}.tmp"

    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for word, freq in result:
            f.write(f"{word} {freq}\n")

    # Verify the file was actually created by the OS before replacing
    if tmp.exists():
        tmp.replace(path)
    else:
        raise FileNotFoundError(f"Failed to create temporary file: {tmp}")
    report = {
        "file": str(path),
        "before": len(entries),
        "after": len(result),
        "removed": dict(stats),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Normalize multilingual keyboard wordlists."
    )
    parser.add_argument(
        "--mode",
        choices=["all", "git", "git-status"],
        default="all",
        help="Normalization mode: 'all' to process all wordlists (default), or 'git' / 'git-status' to process only new or updated files from git status.",
    )
    parser.add_argument(
        "--git",
        "--git-status",
        action="store_true",
        dest="git_flag",
        help="Shorthand flag to normalize only new/updated files according to git status.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Optional specific file(s) to normalize. Overrides --mode if provided.",
    )
    args = parser.parse_args()

    if args.files:
        files = [p.resolve() for p in args.files if p.is_file()]
    elif args.git_flag or args.mode in ("git", "git-status"):
        files = get_git_changed_files()
        print(f"Git status mode: found {len(files)} new/updated file(s) to normalize.")
    else:
        files = sorted(DATA_DIR.glob("*/*_full.txt.gz"))

    if not files:
        print("No files to process.")
        return

    reports = []
    for file in files:
        reports.append(process_file(file))

    report_path = Path("normalization_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    print(f"\nSaved normalization report for {len(reports)} file(s) to {report_path.resolve()}")



if __name__ == "__main__":
    main()

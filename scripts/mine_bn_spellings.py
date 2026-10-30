#!/usr/bin/env python3
"""Mine Bangla spellings from people's romanized comments, for the app's map.

    python scripts/mine_bn_spellings.py BANGLATLIT_DIR APP_DIR OUT.tsv \
        [--min-posts N] [--min-share S]

BANGLATLIT_DIR is a checkout of https://github.com/farhanishmam/BanglaTLit (MIT):
romanized comments with a Bangla reference written by human annotators. APP_DIR
is a WMKeyboard checkout. OUT.tsv gets `spelling, word, posts, share, form`, most
posts first, where `form` is `new` for a spelling the app's map lacks, `extra`
for a reading of one it has that it does not list, and `second` for one it lists
behind another.

Only the annotated TrickBD comments are read. BanglaTLit's train file also holds
4,167 Wikipedia sentences that are Dakshina's (via Bhasha-Abhijnaanam) and 3,500
from Shibli et al., and it repeats its own validation and test rows. All are
left out: the first two so the source stays one thing, and so Dakshina and the
two BanglaTLit splits stay fair tests of what this produces.

A post counts once for a spelling, so one person repeating a word is one vote.
A pair is kept when its word is one the app's word lists know (an annotator's
typo or a stranger's name is not), when its spelling is not an English word (the
map outranks everything, so `for` would stop being able to mean for), when it has
at least two letters (`a` and `r` are half of every longer word as it is typed),
when the spelling is capitalized in under half of the posts away from the start
of a sentence (that is a name), and when it is not profanity. The map's rule for
names and profanity is the same as for the rest of it: leave them out.
"""

import argparse
import collections
import csv
import gzip
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BANGLA = re.compile(r"^[ঀ-ৣৰৱ]+$")
ROMAN = re.compile(r"^[A-Za-z]+$")
EDGE = re.compile(r"^[^\wঀ-৿]+|[^\wঀ-৿]+$")

# Profanity and slurs, as stems, on both sides of the pair. The Bangla column is
# what a keyboard would write, so it is what matters; the Latin one catches a
# pair whose reference was softened by its annotator.
BAD_BANGLA = re.compile("চোদ|চুদ|চুত|চোট|খানকি|খানকী|মাগি|মাগী|ভোদা|গান্ডু|গাণ্ডু|পুটকি|হারামি|হারামী|বেশ্যা|ধোন|সেক্স|কুত্তার|শুয়োর")
BAD_EXACT = {"বাল", "শালা", "শালি", "শালী", "মাল", "লেওড়া", "লেওরা", "ল্যাওড়া", "আবাল", "বাঞ্চোত"}
BAD_ROMAN = re.compile(r"chud|chod|khanki|magi|voda|bhoda|gandu|sex|fuck|shit|bitch|haram")
# Spellings BAD_ROMAN hits that are ordinary words.
ROMAN_OK = {"chodo", "chodda", "choddo", "bhodro", "vodro", "magic", "imagine", "magician"}


# BanglaTLit's stand-ins for the names it anonymized; `imran` is not ইউজার.
PLACEHOLDERS = {"ইউজার", "ইউসার", "অমুক"}

# The rest of this came from reading every pair the filters let through.
# English words the two lists rank too low to catch, and acronyms. They go in the
# loanword asset, which tells the app the keys may well be English.
LOANWORDS = set("""
    adb apk blogging browse btc captcha cashback clicker cmd config dns dolby downloader dslr dubbing
    emulator freelancing ftp handset hd htc http img installer ios itel kbps kitkat kyc limitation ltc
    matchmaking mcq micromax moderator multiplayer playlist plugin png pointer popup preset psd referral
    rename saver simulator subscriber tester thumbnail txt url vpn watermark winrar
""".split())

# Typos, a real word's keys given to another word, site jargon, names.
REJECTED = set("""
    aji bg bl calo chalo cz dieci dinar dl doroner fack fak ff gangstar gf ic jone jony kw laj
    neonbati np ns nought nuton obbosoy pb pir rokon sc sd shohag tg tp tuner tunar tunner wp xm
""".split())

# Overrides of the map's first reading that TrickBD's habits should not decide:
# a worse or wrong reading, English, a colloquial or merely different spelling of
# what the map has, or a word personal chat means more often than a forum does.
KEEP_LEAD = set("""
    acha admin again akhono ay chilo content deya dewar diche fb gese ghonta gola hoiche it jai jan jeno
    joto kan karo kibhabe kindly koran month nia niya noi paisi published rate seita solution then tir
    too tune
""".split())

# A spelling's first reading gives way only on this much evidence.
OVERRIDE_POSTS = 10
OVERRIDE_SHARE = 0.7

# How much of the counted English list counts as English. `chrome` is at 20k; the
# subtitles' Banglish starts soon after (`kano` 28k, `tk` 37k).
ENGLISH_HEAD = 25_000


def precomposed(word):
    """The form the app's map has to hold; see SpellingMapTest."""
    word = unicodedata.normalize("NFC", word)
    return word.replace("ড়", "ড়").replace("ঢ়", "ঢ়").replace("য়", "য়")


def strip(token):
    return EDGE.sub("", token)


def normal(text):
    return re.sub(r"[^\wঀ-৿]+", " ", text).strip().lower()


def rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader)
        yield from reader


def other_sources(data):
    """Normalized romanized text of the sources that are not TrickBD comments."""
    try:
        import openpyxl
    except ImportError:
        sys.exit("needs openpyxl, to read the two source workbooks BanglaTLit ships")
    seen = set()
    for name in ("Bhasha-Abhijnaanam-Bangla-Ann-4.6k-Clean-WestBengal Dialect.xlsx",
                 "AutoBackTransliteration-Springer-Annotated-Unclean-5k.xlsx"):
        sheet = openpyxl.load_workbook(data / "Data Sources" / name, read_only=True).worksheets[0]
        for row in sheet.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, str) and not re.search(r"[ঀ-৿]", cell):
                    seen.add(normal(cell))
    return seen


def known_words(app):
    known = set()
    with gzip.open(ROOT / "data/bn/bn_full_v2.txt.gz", "rt", encoding="utf-8") as f:
        for line in f:
            known.add(precomposed(line.rsplit(" ", 1)[0]))
    for line in open(app / "app/dictionaries-src/bn.txt", encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            known.add(precomposed(line.rsplit(" ", 1)[0]))
    return known


def english_words(app):
    """The bundled English list, and the head of the counted one: `chrome` and
    `config` are in only the second. TrickBD is a tech site, and a keyboard
    that writes ক্রোম for someone typing chrome in English is worse than one
    that leaves a loanword to the hand-written list."""
    words = set()
    for line in open(app / "app/dictionaries-src/en.txt", encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            words.add(line.rsplit(" ", 1)[0].lower())
    with gzip.open(ROOT / "data/en/en_full.txt.gz", "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= ENGLISH_HEAD:
                break
            words.add(line.rsplit(" ", 1)[0].lower())
    return words


def app_map(app):
    forms = collections.defaultdict(list)
    for name in ("en_bn.tsv", "bn_rom.tsv"):
        for line in open(app / "app/src/main/assets/dictionaries" / name, encoding="utf-8"):
            if line.startswith("#") or "\t" not in line:
                continue
            key, value = line.rstrip("\n").split("\t")[:2]
            forms[key.strip().lower()].append(precomposed(value.strip()))
    return forms


def profane(spelling, word):
    if word in BAD_EXACT or BAD_BANGLA.search(word):
        return True
    return spelling not in ROMAN_OK and BAD_ROMAN.search(spelling) is not None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("banglatlit", type=Path)
    parser.add_argument("app", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--min-posts", type=int, default=2)
    parser.add_argument("--min-share", type=float, default=0.5)
    parser.add_argument("--apply", type=Path, metavar="REPLAY",
                        help="the harness's output over OUT.tsv: rewrite the app's two assets with what it says is needed")
    args = parser.parse_args()

    data = args.banglatlit / "data"
    csv.field_size_limit(10**7)
    excluded = other_sources(data)
    for name in ("BanglaTLiT_val.csv", "BanglaTLiT_test.csv"):
        excluded |= {normal(row[1]) for row in rows(data / name) if len(row) >= 3}

    posts = collections.defaultdict(collections.Counter)
    capital = collections.Counter()
    inner = collections.Counter()
    used = aligned = 0
    for row in rows(data / "BanglaTLit_train.csv"):
        if len(row) < 3 or not re.search(r"[ঀ-৿]", row[2]) or normal(row[1]) in excluded:
            continue
        used += 1
        roman = [t for t in map(strip, row[1].split()) if t]
        bangla = [t for t in map(strip, row[2].split()) if t]
        if len(roman) != len(bangla):
            continue
        aligned += 1
        pairs = set()
        for i, (r, b) in enumerate(zip(roman, bangla)):
            if ROMAN.match(r) and BANGLA.match(b):
                pairs.add((r.lower(), precomposed(b)))
                if i > 0:
                    inner[r.lower()] += 1
                    capital[r.lower()] += r[0].isupper()
        for spelling, word in pairs:
            posts[spelling][word] += 1

    known = known_words(args.app)
    english = english_words(args.app)
    forms = app_map(args.app)
    dropped = collections.Counter()
    kept = []
    for spelling, words in posts.items():
        total = sum(words.values())
        if len(spelling) < 2:
            dropped["one letter"] += 1
            continue
        if spelling in english and spelling not in forms:
            dropped["an English word"] += 1
            continue
        if inner[spelling] and capital[spelling] * 2 >= inner[spelling]:
            dropped["capitalized, a name"] += 1
            continue
        for word, count in words.items():
            if count < args.min_posts or count / total < args.min_share:
                dropped["too little evidence"] += 1
            elif word in PLACEHOLDERS or spelling in REJECTED:
                dropped["placeholder or reviewed out"] += 1
            elif word not in known:
                dropped["word in no list"] += 1
            elif profane(spelling, word):
                dropped["profanity"] += 1
            elif word == (forms[spelling] or [None])[0]:
                dropped["already mapped"] += 1
            else:
                form = "new" if not forms[spelling] else "second" if word in forms[spelling] else "extra"
                kept.append((spelling, word, count, count / total, form))
    kept.sort(key=lambda k: (-k[2], k[0], k[1]))
    with open(args.out, "w", encoding="utf-8") as f:
        for spelling, word, count, share, form in kept:
            f.write(f"{spelling}\t{word}\t{count}\t{share:.2f}\t{form}\n")
    print(f"{used} comments, {aligned} aligned, {len(posts)} spellings; kept {len(kept)} pairs")
    print("dropped:", ", ".join(f"{k} {v}" for k, v in dropped.most_common()))
    if args.apply:
        apply_to_app(args.app, kept, args.apply)


def apply_to_app(app, kept, replay):
    """Writes the pairs the app does not already commit into its two assets.

    A new spelling goes at the end of bn_rom.tsv, or en_bn.tsv if it is a
    LOANWORDS one. Another reading of a listed spelling goes behind what is
    there, so it is offered and not committed, unless it has OVERRIDE_POSTS and
    OVERRIDE_SHARE, in which case it takes the first place. en_bn.tsv's own
    readings are not overridden: it is loaded first and is hand-written.
    """
    right = set()
    with open(replay, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p[3].split(",")[3] == "0":
                right.add((p[0], p[1]))
    assets = app / "app/src/main/assets/dictionaries"
    en_lines = open(assets / "en_bn.tsv", encoding="utf-8").read().rstrip("\n").split("\n")
    en_keys = {l.split("\t")[0].strip().lower() for l in en_lines if "\t" in l and not l.startswith("#")}
    rom_lines = open(assets / "bn_rom.tsv", encoding="utf-8").read().rstrip("\n").split("\n")
    lead, added, loan = {}, [], []
    for spelling, word, count, share, form in kept:
        if (spelling, word) in right:
            continue
        if (form != "new" and count >= OVERRIDE_POSTS and share >= OVERRIDE_SHARE
                and spelling not in en_keys and spelling not in KEEP_LEAD and spelling not in lead):
            lead[spelling] = word
        elif form == "second":
            continue
        elif spelling in LOANWORDS:
            loan.append((spelling, word))
        else:
            added.append((spelling, word))
    out, moved = [], set()
    for line in rom_lines:
        if line.startswith("#") or "\t" not in line:
            out.append(line)
            continue
        key, value = line.split("\t")[:2]
        if key in lead:
            if key not in moved:
                out.append(f"{key}\t{lead[key]}")
                moved.add(key)
            if value == lead[key]:
                continue
        out.append(line)
    out += [f"{s}\t{w}" for s, w in added if lead.get(s) != w]
    en_lines += [f"{s}\t{w}" for s, w in loan]
    (assets / "bn_rom.tsv").write_text("\n".join(out) + "\n", encoding="utf-8")
    (assets / "en_bn.tsv").write_text("\n".join(en_lines) + "\n", encoding="utf-8")
    print(f"bn_rom.tsv: {len(added)} added, {len(moved)} first readings changed; en_bn.tsv: {len(loan)} added")


if __name__ == "__main__":
    main()

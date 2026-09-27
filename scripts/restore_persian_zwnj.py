#!/usr/bin/env python3
"""
Put the half-space (ZWNJ, U+200C) back into the Persian word list.

WM Keyboard #406. The Persian list is counted from OpenSubtitles, and the
subtitle text had every ZWNJ removed: the list holds 364k words and not one of
them contains U+200C. Standard Persian writes a half-space in exactly the
places a keyboard is most used for, so the list spelled میکنم, نمیشود and
سگها where the language writes می‌کنم, نمی‌شود and سگ‌ها. A word list with no
ZWNJ also makes the correctly typed word unknown, so autocorrect "fixed" it
back to the run-together one.

The spelling is restored by rule, using the list itself as the evidence for
each rule. Precision matters more than recall here: a word left alone is what
the list already had, while a half-space in the wrong place is a new mistake.

 * **می / نمی, the continuous prefix.** A remainder R is a verb when the list
   has both میR and نمیR (the negative form is what separates میکنم from
   میدان or میوه, which have none). The same R with an object clitic
   (میبینمت), a past-stem ending with a نR twin (میگفتند / نگفتند), or both a
   subjunctive بR and a negative نR also count.
 * **ها and its clitics, the plural.** سگها → سگ‌ها when the stem is itself a
   word at least a tenth as frequent as the plural. Two-letter stems only from
   a list of nouns: با|هاش, ال|هام and ات|هام are words, not plurals.
 * **اند / ایم / اید after a silent ه**, the perfect: شده‌اند, رفته‌اید. The
   other endings are left alone. -ای is mostly a colloquial plural here
   (راهای, کوهای for راه‌ها, کوه‌ها), and -ام / -ات / -اش read the same way
   (کارهات) or are an Arabic plural (اشتباهات).
 * **تر / ترین after ه.** ساده‌تر, کوتاه‌ترین. بهتر is written joined.

Nothing else is changed, the counts are kept, and a run on a list that already
has its half-spaces changes nothing: the rules only match words spelled with
letters alone.

Usage: scripts/restore_persian_zwnj.py [--dry-run] [--show N] [path]
"""

import argparse
import gzip
import re
from collections import Counter, defaultdict
from pathlib import Path

ZWNJ = "‌"

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "fa" / "fa_full.txt.gz"

# Persian letters only: a word with a digit, a dot, a ZWNJ already, or any
# other script is not one these rules can reason about.
LETTERS = re.compile(r"^[ء-غف-يپچژکگیآ]+$")

MIN_COUNT = 3

OBJECT_CLITICS = ("تون", "شون", "مون", "تان", "شان", "مان", "مت", "مش", "ت", "ش", "م")
PAST_ENDINGS = (
    "تند", "دند", "تیم", "دیم", "تید", "دید", "تین", "دین",
    "تم", "دم", "تی", "دی", "تن", "دن", "ت", "د",
)

# Nouns that start with می and whose remainder happens to pass a verb test.
NOT_PREFIXED = {
    "میدان", "میان", "میانه", "میانی", "میزبان", "میهمان", "میخانه", "میلیون",
    "میزان", "میلاد", "میراث", "میمون", "میوه", "میله", "میهن",
}

PLURALS = (
    "هایمان", "هایتان", "هایشان", "هامون", "هاتون", "هاشون",
    "هایی", "هایم", "هایت", "هایش", "های", "هام", "هات", "هاش", "ها",
)

# Words that end in ها but are not a plural.
NOT_PLURAL = {"تنها", "تنهایی", "تنهای", "انتها", "انتهای", "منتها", "بعدها"}
NOT_PLURAL_PARTS = ("نهایت", "گراهام", "تنها", "انتها")

# The only two-letter stems a plural is built on here. Most two-letter
# "stems" in the list are the start of another word (الهام, اتهام, باهاش).
SHORT_NOUNS = {
    "زن", "مو", "صد", "جا", "در", "پا", "شب", "سگ", "گل", "کد", "آب", "رگ",
    "لب", "سر", "دل", "یخ", "رز", "پل", "خط", "غم", "ژن", "کت", "نت", "چک",
    "ده", "شش", "آن", "بز", "خر", "پر", "بو", "جو", "دم",
}

HEH_ENDINGS = ("اند", "ایم", "اید")
# Stems ending in ه that are not a past participle: بره (lamb), اوه (oh), and
# the colloquial verbs منه, میره.
NOT_PARTICIPLE = {"بره", "منه", "اوه", "میره"}

COMPARATIVES = ("ترین", "تر")
# A final اه is a pronounced h, and most words ending in it are nouns
# (راه, گناه, پناه); these are the adjectives among them.
ADJECTIVES_IN_AH = {"کوتاه", "سیاه", "آگاه", "تباه", "گمراه"}


class Restorer:
    def __init__(self, counts):
        self.counts = counts
        self.verbs = {
            word[3:]
            for word, count in counts.items()
            if word.startswith("نمی") and len(word) >= 5 and count >= MIN_COUNT
            and self.count("می" + word[3:]) >= MIN_COUNT
        }

    def count(self, word):
        return self.counts.get(word, 0)

    def is_verb(self, rest):
        if rest in self.verbs:
            return True
        for clitic in OBJECT_CLITICS:
            if rest.endswith(clitic) and rest[: -len(clitic)] in self.verbs:
                return True
        if len(rest) >= 3 and rest.endswith(PAST_ENDINGS) and self.count(rest) >= 20 \
                and self.count("ن" + rest) >= MIN_COUNT:
            return True
        return len(rest) >= 3 and self.count("ب" + rest) >= MIN_COUNT \
            and self.count("ن" + rest) >= MIN_COUNT

    def restore(self, word):
        """[word] with its half-space, and which rule put it there; None when unchanged."""
        if len(word) < 4 or not LETTERS.match(word):
            return None
        if word not in NOT_PREFIXED:
            for prefix in ("نمی", "می"):
                rest = word[len(prefix):]
                if word.startswith(prefix) and len(rest) >= 2 and self.is_verb(rest):
                    return prefix + ZWNJ + rest, "prefix"
        if word in NOT_PLURAL or any(part in word for part in NOT_PLURAL_PARTS):
            return None
        for plural in PLURALS:
            if word.endswith(plural):
                stem = word[: -len(plural)]
                long_enough = len(stem) >= 3 or stem in SHORT_NOUNS
                if long_enough and self.count(stem) >= 20 and self.count(stem) * 10 >= self.count(word):
                    return stem + ZWNJ + plural, "plural"
                break
        for ending in COMPARATIVES:
            if word.endswith(ending):
                stem = word[: -len(ending)]
                adjective = stem in ADJECTIVES_IN_AH or (
                    stem.endswith("ه") and not stem.endswith(("اه", "وه", "به", "جه", "مه"))
                )
                if len(stem) >= 3 and adjective and self.count(stem) >= 200:
                    return stem + ZWNJ + ending, "comparative"
                break
        for ending in HEH_ENDINGS:
            if word.endswith(ending):
                stem = word[: -len(ending)]
                if len(stem) >= 3 and stem.endswith("ه") and not stem.endswith("اه") \
                        and stem not in NOT_PARTICIPLE \
                        and self.count(stem) >= 100 and self.count(stem) >= self.count(word):
                    return stem + ZWNJ + ending, "heh"
                break
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show", type=int, default=0, help="print the N most frequent changes per rule")
    args = parser.parse_args()

    with gzip.open(args.path, "rt", encoding="utf-8") as f:
        entries = []
        for line in f:
            word, _, count = line.rstrip("\n").rpartition(" ")
            if word:
                entries.append((word, int(count)))
    restorer = Restorer(dict(entries))

    merged = {}
    changed = Counter()
    examples = defaultdict(list)
    for word, count in entries:
        fixed = restorer.restore(word)
        if fixed:
            changed[fixed[1]] += 1
            if len(examples[fixed[1]]) < args.show:
                examples[fixed[1]].append(f"{word}→{fixed[0]}")
            word = fixed[0]
        merged[word] = merged.get(word, 0) + count

    print(f"{args.path}: {len(entries)} words, {sum(changed.values())} given a half-space {dict(changed)}")
    for rule, items in examples.items():
        print(f"{rule}: " + " ".join(items))
    if args.dry_run:
        return

    result = sorted(merged.items(), key=lambda x: (-x[1], x[0]))
    tmp = args.path.parent / f"{args.path.name}.tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for word, count in result:
            f.write(f"{word} {count}\n")
    tmp.replace(args.path)


if __name__ == "__main__":
    main()

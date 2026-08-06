"""Merge romanized-Bangla n-gram counts from a Facebook data export into the
existing personal dictionary (data/bn/bn_rom*.txt.gz).

Streams message JSON directly out of the export zip(s) (no extraction).
Reads inbox, archived_threads and e2ee_cutover sections; skips
filtered_threads (message requests / spam). Group chats count as long as the
export owner sent at least one real message in them; 1:1 chats need
MIN_OWN_MESSAGES so seller/stranger threads don't pollute the dictionary.
Messages are deduped across sections (e2ee_cutover overlaps inbox history).

Counts are ADDED to the existing bn_rom files — run this once per export, or
counts get doubled.

Usage: python3 scripts/import_facebook_chats.py <owner name> <export.zip> [more.zip ...]
"""

import gzip
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

MIN_OWN_MESSAGES = 10

SECTION = re.compile(
    r".*/messages/(inbox|archived_threads|e2ee_cutover)/([^/]+)/message_\d+\.json$"
)

# Messenger boilerplate stored in `content` but never typed by a human.
# Names are prepended ("Faisal added X to the group.") so patterns anchor at
# the end or on the fixed template body, not at the start.
BOILERPLATE = re.compile(
    r"sent an attachment\.$"
    r"|added (.* to the group|a participant)\.$"
    r"|(joined|left|created) the group( chat)?\.?$"
    r"|removed (.* from the group|a participant from the group)\.$"
    r"|(voted for|(removed|changed) (his|her|their) vote (for|to)|added \".*\" to) .* poll\.$"
    r"|created a poll"
    r"|this poll is no longer available\.$"
    r"|(pinned|unpinned) a message\.$"
    r"|named the group "
    r"|(changed|removed) the group photo\.$"
    r"|changed the theme"
    r"|created a custom theme\.$"
    r"|changed the quick reaction"
    r"|(started|joined|missed|ended) (a|an|the) (video |audio )?(call|chat)"
    r"|missed your call"
    r"|(started|stopped) sharing video"
    r"|set (the |your |his |her |their )?nickname"
    r"|cleared (the |your |his |her |their )?(own )?nickname"
    r"|turned (on|off) (member approval|live updates|message sharing)"
    r"|set (the )?disappearing message"
    r"|unsent a message\.?$"
    r"|liked a message$"
    r"|reacted .* to your message"
    r"|waved (hello|at)"
    r"|you are now connected"
    r"|you can now (message|call)"
    r"|sent a (sticker|GIF|location|live location)\.?$",
    re.IGNORECASE,
)

# Bot participants whose messages are machine-generated, not typed by a person.
SKIP_SENDERS = {"Meta AI"}

# Keys that mark a message as a non-text event even when `content` is present.
NON_TEXT_KEYS = ("call_duration", "sticker")

MENTION = re.compile(r"@[\w.]+")
EDITED_SUFFIX = re.compile(r"\s*\(edited\)\s*$")
URL = re.compile(r"https?://\S+|www\.\S+")
# Latin-script word: letters plus internal apostrophes (e.g. don't, o'rokom).
# A letter run touching a digit is thrown away rather than split: with a number
# row on the keyboard, "kisu" gets mistyped as "ki6u", and splitting that would
# quietly file "ki" and "u" as two real words. Nothing can recover the intended
# spelling, so the whole token goes.
WORD = re.compile(r"(?<![0-9a-z])[a-z]+(?:'[a-z]+)*(?![0-9a-z])")
# Sentence-ish boundaries: n-grams must not span these
SENT_SPLIT = re.compile(r"[.!?,;:\n।…]+")


def fix_mojibake(s):
    # Facebook exports store UTF-8 bytes as latin-1-escaped JSON strings.
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def iter_threads(zip_paths):
    by_thread = {}
    for zp in zip_paths:
        zf = zipfile.ZipFile(zp)
        for name in zf.namelist():
            m = SECTION.match(name)
            if m:
                by_thread.setdefault(m.group(2), []).append((zf, name))
    for thread, files in by_thread.items():
        participants = set()
        msgs = []
        for zf, fn in files:
            with zf.open(fn) as f:
                data = json.load(f)
            for p in data.get("participants", []):
                participants.add(fix_mojibake(p.get("name", "")))
            msgs.extend(data.get("messages", []))
        yield thread, participants, msgs


def is_real_text(m):
    content = m.get("content")
    if not content or "share" in m:
        return None
    if any(k in m for k in NON_TEXT_KEYS):
        return None
    if fix_mojibake(m.get("sender_name", "")) in SKIP_SENDERS:
        return None
    text = fix_mojibake(content)
    if BOILERPLATE.search(text):
        return None
    return EDITED_SUFFIX.sub("", text)


def main():
    owner, zip_paths = sys.argv[1], sys.argv[2:]
    root = Path(__file__).resolve().parent.parent

    uni, bi, tri = Counter(), Counter(), Counter()
    threads_kept = threads_dropped = messages_used = dupes = 0
    seen = set()

    for thread, participants, msgs in iter_threads(zip_paths):
        own = sum(
            1
            for m in msgs
            if fix_mojibake(m.get("sender_name", "")) == owner
            and is_real_text(m) is not None
        )
        is_group = len(participants) > 2
        if own < (1 if is_group else MIN_OWN_MESSAGES):
            threads_dropped += 1
            continue
        threads_kept += 1
        for m in msgs:
            text = is_real_text(m)
            if text is None:
                continue
            key = (m.get("sender_name"), m.get("timestamp_ms"), m["content"])
            if key in seen:
                dupes += 1
                continue
            seen.add(key)
            messages_used += 1
            text = MENTION.sub(" ", URL.sub(" ", text)).lower()
            for sentence in SENT_SPLIT.split(text):
                words = WORD.findall(sentence)
                uni.update(words)
                bi.update(zip(words, words[1:]))
                tri.update(zip(words, words[1:], words[2:]))

    out = root / "data" / "bn"

    def merge(counter, path, min_count, joiner=" "):
        existing = Counter()
        if path.exists():
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    parts = line.rsplit(" ", 1)
                    if len(parts) == 2:
                        toks = tuple(parts[0].split(joiner))
                        existing[toks if len(toks) > 1 else toks[0]] = int(parts[1])
        added = sum(1 for k, c in counter.items() if c >= min_count and k not in existing)
        for k, c in counter.items():
            if c >= min_count or k in existing:
                existing[k] += c
        kept = sorted(existing.items(), key=lambda kc: (-kc[1], kc[0]))
        with gzip.open(path, "wt", encoding="utf-8") as f:
            for k, c in kept:
                key = k if isinstance(k, str) else joiner.join(k)
                f.write(f"{key} {c}\n")
        print(f"{path.name}: {len(kept)} entries ({added} new, {len(counter)} raw fb)")

    merge(uni, out / "bn_rom.txt.gz", min_count=2)
    merge(bi, out / "bn_rom_bigrams.txt.gz", min_count=3)
    merge(tri, out / "bn_rom_trigrams.txt.gz", min_count=3)

    print(
        f"threads kept={threads_kept} dropped={threads_dropped} "
        f"messages used={messages_used} cross-section dupes={dupes}"
    )


if __name__ == "__main__":
    main()

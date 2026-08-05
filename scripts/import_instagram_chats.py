"""Build a personal romanized-Bangla dictionary (uni/bi/trigrams) from an Instagram data export.

Streams message JSON directly out of the export zip (no extraction), keeps only
personal threads (where the export owner sent at least MIN_OWN_MESSAGES), and
counts word n-grams from both sides of those conversations.

Usage: python3 scripts/import_instagram_chats.py <export.zip> <owner name>
"""

import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

MIN_OWN_MESSAGES = 10

# Instagram boilerplate that appears in `content` but was never typed by a human.
# Anchored loosely at the end: senders' nicknames are prepended ("akaza reacted ...").
BOILERPLATE = re.compile(
    r"sent an attachment\.$"
    r"|shared a story\.$"
    r"|liked a message$"
    r"|reacted .* to your (message|story)\s*$"
    r"|unsent a message\.?$"
    r"|wasn't notified about this message because they're in quiet mode\.$"
    r"|(started|missed) (an audio|a video) call\.?"
    r"|this poll is no longer available\.$"
    r"|changed the theme"
    r"|(named the group|changed the group photo|added .* to the group|left the group)"
    r"|set (the )?disappearing message"
    r"|^say hi to "
    r"|use the heart on any message to unlock"
    r"|created a note"
    r"|attempted to call you"
    r"|sent a (sticker|doodle)\.?"
    r"|update your app to view"
    r"|added a sticker to your message"
    r"|(started|missed|joined|left) (a video chat|an audio chat)"
    r"|(video chat|audio call) (started|ended)"
    r"|set (your|the) nickname"
    r"|cleared the nickname",
    re.IGNORECASE,
)

# Bot participants whose messages are machine-generated, not typed by a person.
SKIP_SENDERS = {"Meta AI"}

MENTION = re.compile(r"@[\w.]+")

EDITED_SUFFIX = re.compile(r"\s*\(edited\)\s*$")

URL = re.compile(r"https?://\S+|www\.\S+")
# Latin-script word: letters plus internal apostrophes (e.g. don't, o'rokom)
WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")
# Sentence-ish boundaries: n-grams must not span these
SENT_SPLIT = re.compile(r"[.!?,;:\n।…]+")


def fix_mojibake(s):
    # Instagram exports store UTF-8 bytes as latin-1-escaped JSON strings.
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def iter_threads(zf):
    by_thread = {}
    for name in zf.namelist():
        m = re.match(r".*/messages/inbox/([^/]+)/message_\d+\.json$", name)
        if m:
            by_thread.setdefault(m.group(1), []).append(name)
    for thread, files in by_thread.items():
        msgs = []
        for fn in files:
            with zf.open(fn) as f:
                msgs.extend(json.load(f).get("messages", []))
        yield thread, msgs


def main():
    zip_path, owner = sys.argv[1], sys.argv[2]
    root = Path(__file__).resolve().parent.parent

    uni, bi, tri = Counter(), Counter(), Counter()
    threads_kept = threads_dropped = messages_used = 0

    with zipfile.ZipFile(zip_path) as zf:
        for thread, msgs in iter_threads(zf):
            own = sum(
                1
                for m in msgs
                if fix_mojibake(m.get("sender_name", "")) == owner
                and m.get("content")
                and not BOILERPLATE.search(fix_mojibake(m["content"]))
            )
            if own < MIN_OWN_MESSAGES:
                threads_dropped += 1
                continue
            threads_kept += 1
            for m in msgs:
                content = m.get("content")
                if not content or "share" in m:
                    continue
                if fix_mojibake(m.get("sender_name", "")) in SKIP_SENDERS:
                    continue
                text = fix_mojibake(content)
                if BOILERPLATE.search(text):
                    continue
                text = EDITED_SUFFIX.sub("", text)
                messages_used += 1
                text = MENTION.sub(" ", URL.sub(" ", text)).lower()
                for sentence in SENT_SPLIT.split(text):
                    words = WORD.findall(sentence)
                    uni.update(words)
                    bi.update(zip(words, words[1:]))
                    tri.update(zip(words, words[1:], words[2:]))

    out = root / "data" / "bn"

    def dump(counter, path, min_count, joiner=" "):
        kept = [(k, c) for k, c in counter.items() if c >= min_count]
        kept.sort(key=lambda kc: (-kc[1], kc[0]))
        import gzip

        with gzip.open(path, "wt", encoding="utf-8") as f:
            for k, c in kept:
                key = k if isinstance(k, str) else joiner.join(k)
                f.write(f"{key} {c}\n")
        print(f"{path.name}: {len(kept)} entries (of {len(counter)} raw)")

    dump(uni, out / "bn_rom.txt.gz", min_count=2)
    dump(bi, out / "bn_rom_bigrams.txt.gz", min_count=3)
    dump(tri, out / "bn_rom_trigrams.txt.gz", min_count=3)

    print(
        f"threads kept={threads_kept} dropped={threads_dropped} "
        f"messages used={messages_used}"
    )


if __name__ == "__main__":
    main()

"""Restore Klingon's capitals to a word list that was folded to lower case.

In Klingon a capital is a letter of its own: q and Q are two consonants, and
D, H, I and S are only ever written as capitals. The Glot500 import used to
lower-case every list, which merged words like qaH ("sir") and QaH ("help")
and left the keyboard nothing to tell them apart by.

    git show b18bf33:data/tlh/tlh_full.txt.gz | gunzip > /tmp/tlh_reference.txt
    gunzip -c data/tlh/tlh_full.txt.gz > /tmp/tlh_folded.txt
    python3 scripts/recase_klingon.py /tmp/tlh_folded.txt /tmp/tlh_reference.txt /tmp/tlh_full.txt
    gzip -9n -c /tmp/tlh_full.txt > data/tlh/tlh_full.txt.gz

The reference is the original klingonska.org list, which is written in
Klingon's own case. A word it has takes every spelling it gives that word;
any other is spelled out letter by letter (d, h, i and s are always capitals,
the h of ch, gh and tlh never is) and takes the case of its q's from the
longest reference word it starts with. A word holding a letter Klingon does
not have is dropped as stray text from the corpus.
"""
import re, sys, collections

TOKENS = ["tlh", "ch", "gh", "ng", "a", "b", "D", "e", "H", "I", "j", "l", "m", "n", "o", "p", "q", "r", "S", "t", "u", "v", "w", "y", "'"]
FOLDED = sorted({t.lower() for t in TOKENS}, key=len, reverse=True)

def tokens(lower):
    """Split a folded word into Klingon letters, or None if it is not spelled in them."""
    out, at = [], 0
    while at < len(lower):
        for t in FOLDED:
            if lower.startswith(t, at):
                out.append(t); at += len(t); break
        else:
            return None
    return out

DETERMINED = {"d": "D", "h": "H", "i": "I", "s": "S"}

def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"): continue
        parts = line.rsplit(" ", 1)
        word, freq = (parts[0], int(parts[1])) if len(parts) == 2 and parts[1].isdigit() else (line, 1)
        rows.append((word, freq))
    return rows

def main(current, reference, out):
    ref = collections.defaultdict(list)
    for word, _ in load(reference):
        if word not in ref[word.lower()]: ref[word.lower()].append(word)
    # Longest-first prefixes of reference words, by token, to take the case of q from a known root.
    roots = {k: v[0] for k, v in ref.items() if len(v) == 1 and " " not in k}
    merged = collections.Counter()
    dropped = 0
    for word, freq in load(current):
        lower = word.lower()
        if lower in ref:
            for spelling in ref[lower]: merged[spelling] += freq
            continue
        parts = [recase(part, roots) for part in lower.split(" ")]
        if any(p is None for p in parts):
            dropped += 1; continue
        merged[" ".join(parts)] += freq
    with open(out, "w", encoding="utf-8") as f:
        for word, freq in sorted(merged.items(), key=lambda kv: (-kv[1], kv[0])):
            f.write(f"{word} {freq}\n")
    print(f"kept {len(merged)} spellings, dropped {dropped} not spelled in Klingon letters", file=sys.stderr)

def recase(lower, roots):
    """One folded word in Klingon's own case, or None when it is not spelled in Klingon letters."""
    toks = tokens(lower)
    if not toks:
        return None
    cased = [DETERMINED.get(t, t) for t in toks]
    # q vs Q: borrow from the longest reference word the word starts with.
    for end in range(len(toks), 0, -1):
        root = roots.get("".join(toks[:end]))
        if root is None: continue
        rt = tokens(root.lower())
        # Walk the root's own letters to read their case back.
        at = 0
        for i, t in enumerate(rt):
            cased[i] = root[at:at + len(t)]
            at += len(t)
        # The one common suffix spelled with Q: -Qo' (don't).
        rest = "".join(toks[end:])
        if rest.startswith("qo'"):
            cased[end] = "Q"
        break
    return "".join(cased)

if __name__ == "__main__":
    main(*sys.argv[1:4])

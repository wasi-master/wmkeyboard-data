#!/usr/bin/env python3
"""
build_stroke_dict.py — Convert CJK stroke-order data into WMKeyboard's StrokeDictionary TSV.

Format:
  strokeCode<TAB>hanzi<TAB>freq

where:
  strokeCode = 1-5 stroke class sequence (1=一 héng, 2=丨 shù, 3=丿 piě, 4=丶 diǎn, 5=乙/𠃍 zhé)
  hanzi      = Simplified Hanzi character
  freq       = integer frequency (higher = more common)

Output:
  cjk/stroke.tsv
"""

import hashlib
import os
import re
import sys
import urllib.request

# Primary data source URL
DATA_URL = "https://raw.githubusercontent.com/yefeijiang/Chinese-characters-code-table/master/%E5%85%A8%E9%83%A8%E6%B1%89%E5%AD%97%E7%A0%81%E8%A1%A8.TXT"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CJK_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_TSV = os.path.join(CJK_DIR, "stroke.tsv")
PINYIN_TSV = os.path.join(CJK_DIR, "pinyin.tsv")

HANZI_RE = re.compile(r"^[\u4e00-\u9fff\u3400-\u4dbf\ud840-\ud869\uded6-\udf00]$")
STROKE_RE = re.compile(r"^[1-5]+$")

def load_freq_map():
    freqs = {}
    if os.path.exists(PINYIN_TSV):
        with open(PINYIN_TSV, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 3 and len(parts[1]) == 1:
                    word = parts[1]
                    try:
                        freq = int(parts[2])
                        if word not in freqs or freq > freqs[word]:
                            freqs[word] = freq
                    except ValueError:
                        pass
    return freqs

def fetch_stroke_data():
    print(f"Fetching stroke data from {DATA_URL}...")
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "WMKeyboard-DictBuilder/1.0"})
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("gbk", errors="ignore")

def main():
    freq_map = load_freq_map()
    text = fetch_stroke_data()
    lines = text.splitlines()

    entries = []
    seen = set()

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("-") or "汉字" in line or "UNICODE" in line:
            continue
        parts = line.split()
        if len(parts) < 9:
            continue
        hz = parts[0].strip()
        stk = parts[8].strip()

        if not HANZI_RE.match(hz) or not STROKE_RE.match(stk):
            continue
        if hz in seen:
            continue
        seen.add(hz)

        # Frequency: from pinyin.tsv if available, otherwise based on table rank
        if hz in freq_map:
            freq = freq_map[hz]
        else:
            freq = max(1, 500 - int((len(entries) / 20900) * 490))

        entries.append((stk, hz, freq))

    # Sort entries by strokeCode, then by frequency descending
    entries.sort(key=lambda x: (x[0], -x[2], x[1]))

    print(f"Writing {len(entries)} entries to {OUTPUT_TSV}...")
    with open(OUTPUT_TSV, "w", encoding="utf-8") as f:
        for stk, hz, freq in entries:
            f.write(f"{stk}\t{hz}\t{freq}\n")

    # Stats
    size_bytes = os.path.getsize(OUTPUT_TSV)
    hasher = hashlib.sha256()
    with open(OUTPUT_TSV, "rb") as f:
        hasher.update(f.read())
    sha256_hex = hasher.hexdigest()

    print("\n--- Output Statistics ---")
    print(f"File: {OUTPUT_TSV}")
    print(f"Size: {size_bytes} bytes")
    print(f"SHA-256: {sha256_hex}")

if __name__ == "__main__":
    main()

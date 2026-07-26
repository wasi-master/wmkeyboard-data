#!/usr/bin/env python3
"""
build_cangjie_dict.py — Convert Unihan kCangjie data into WMKeyboard's CangjieDictionary TSV.

Format:
  code<TAB>hanzi<TAB>freq

where:
  code  = Cangjie radical code, 1–5 characters (lowercase ASCII a–y)
  hanzi = Han character
  freq  = integer frequency (higher = more common)

Data Source:
  Unicode Unihan database (Unihan_DictionaryLikeData.txt in Unihan.zip)
  https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip

Output:
  cjk/cangjie.tsv
"""

import argparse
import collections
import hashlib
import io
import math
import os
import re
import sys
import urllib.request
import zipfile

UNIHAN_URL = "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CJK_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_TSV = os.path.join(CJK_DIR, "cangjie.tsv")
PINYIN_TSV = os.path.join(CJK_DIR, "pinyin.tsv")


def load_pinyin_freq_map():
    """Loads frequency map for single Hanzi characters from pinyin.tsv if available."""
    freqs = {}
    if os.path.exists(PINYIN_TSV):
        with open(PINYIN_TSV, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#"):
                    continue
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


def fetch_unihan_zip(unihan_path=None):
    """Loads Unihan.zip data from local path or downloads from official Unicode URL."""
    if unihan_path and os.path.exists(unihan_path):
        print(f"Reading Unihan zip from local file: {unihan_path}")
        with open(unihan_path, "rb") as f:
            return f.read()

    print(f"Downloading Unihan.zip from {UNIHAN_URL}...")
    req = urllib.request.Request(UNIHAN_URL, headers={"User-Agent": "WMKeyboard-DictBuilder/1.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def process_cangjie_data(zdata, pinyin_freqs):
    z = zipfile.ZipFile(io.BytesIO(zdata))

    # 1. Load Traditional -> Simplified variant mapping
    trad_to_simp = {}
    if "Unihan_Variants.txt" in z.namelist():
        var_content = z.read("Unihan_Variants.txt").decode("utf-8")
        for line in var_content.splitlines():
            if line and not line.startswith("#"):
                parts = line.split("\t")
                if len(parts) >= 3 and parts[1] == "kSimplifiedVariant":
                    cp, val = parts[0].strip(), parts[2].strip()
                    try:
                        hz = chr(int(cp[2:], 16))
                        for v in val.split():
                            if v.startswith("U+"):
                                trad_to_simp[hz] = chr(int(v[2:], 16))
                    except Exception:
                        pass

    # 2. Load readings for kHanyuPinlu character frequency counts
    pinlu_freqs = {}
    max_pinlu = 0
    if "Unihan_Readings.txt" in z.namelist():
        readings_content = z.read("Unihan_Readings.txt").decode("utf-8")
        for line in readings_content.splitlines():
            if line and not line.startswith("#"):
                parts = line.split("\t")
                if len(parts) >= 3 and parts[1] == "kHanyuPinlu":
                    cp, val = parts[0].strip(), parts[2].strip()
                    try:
                        hz = chr(int(cp[2:], 16))
                        matches = re.findall(r"\((\d+)\)", val)
                        if matches:
                            cnt = sum(int(m) for m in matches)
                            pinlu_freqs[hz] = cnt
                            if cnt > max_pinlu:
                                max_pinlu = cnt
                    except Exception:
                        pass

    # 3. Load standard character set membership indicators
    unihan_core = set()
    bigfive = set()
    tgh = set()
    dict_content = z.read("Unihan_DictionaryLikeData.txt").decode("utf-8")
    for line in dict_content.splitlines():
        if line and not line.startswith("#"):
            parts = line.split("\t")
            if len(parts) >= 3:
                cp, field = parts[0].strip(), parts[1].strip()
                try:
                    hz = chr(int(cp[2:], 16))
                    if field == "kUnihanCore2020":
                        unihan_core.add(hz)
                    elif field == "kBigFive":
                        bigfive.add(hz)
                    elif field in ("kTGHZ2013", "kTGH"):
                        tgh.add(hz)
                except Exception:
                    pass

    # 4. Parse kCangjie lines and apply Hard Validation
    valid_entries = []
    rejections = collections.Counter()
    total_parsed = 0

    for line in dict_content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        cp_str, field, raw_code = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if field != "kCangjie":
            continue

        total_parsed += 1

        # Check codepoint
        if not cp_str.startswith("U+"):
            rejections["invalid_codepoint_prefix"] += 1
            continue

        try:
            codepoint = int(cp_str[2:], 16)
            hanzi = chr(codepoint)
        except Exception:
            rejections["invalid_codepoint_hex"] += 1
            continue

        if not hanzi:
            rejections["empty_hanzi"] += 1
            continue

        # Code lowercasing
        code = raw_code.lower()

        # Hard Validation Rule 1: code is 1 to 5 characters long (inclusive)
        if len(code) < 1 or len(code) > 5:
            rejections[f"code_length_outside_1_to_5 (length={len(code)})"] += 1
            continue

        # Hard Validation Rule 2: every character of code is in a-y (NOT z)
        invalid_chars = [c for c in code if not ("a" <= c <= "y")]
        if invalid_chars:
            if "z" in invalid_chars:
                rejections["code_contains_z"] += 1
            else:
                rejections["code_contains_non_a_y_char"] += 1
            continue

        # Compute frequency
        if hanzi in pinyin_freqs:
            freq = pinyin_freqs[hanzi]
        elif hanzi in trad_to_simp and trad_to_simp[hanzi] in pinyin_freqs:
            freq = pinyin_freqs[trad_to_simp[hanzi]]
        elif hanzi in pinlu_freqs:
            cnt = pinlu_freqs[hanzi]
            freq = int(50 + (math.log(cnt) / math.log(max_pinlu)) * 850) if max_pinlu > 1 else 50
        elif hanzi in tgh:
            freq = 40
        elif hanzi in bigfive:
            freq = 30
        elif hanzi in unihan_core:
            freq = 20
        else:
            freq = 0

        valid_entries.append((code, hanzi, freq))

    return total_parsed, valid_entries, rejections


def main():
    parser = argparse.ArgumentParser(description="Build WMKeyboard Cangjie dictionary TSV from Unihan database.")
    parser.add_argument("--unihan", type=str, help="Path to local Unihan.zip file")
    args = parser.parse_args()

    pinyin_freqs = load_pinyin_freq_map()
    zdata = fetch_unihan_zip(args.unihan)

    total_parsed, entries, rejections = process_cangjie_data(zdata, pinyin_freqs)

    # Sort entries by code ascending, then freq descending, then hanzi ascending
    entries.sort(key=lambda x: (x[0], -x[2], x[1]))

    print(f"Writing {len(entries)} entries to {OUTPUT_TSV}...")
    with open(OUTPUT_TSV, "w", encoding="utf-8") as f:
        f.write("# Cangjie dictionary (Unihan database, Unicode License V3)\n")
        f.write("# Format: code\thanzi\tfreq\n")
        for code, hanzi, freq in entries:
            f.write(f"{code}\t{hanzi}\t{freq}\n")

    # Stats and Verification
    size_bytes = os.path.getsize(OUTPUT_TSV)
    hasher = hashlib.sha256()
    with open(OUTPUT_TSV, "rb") as f:
        hasher.update(f.read())
    sha256_hex = hasher.hexdigest()

    print("\n--- Output Statistics ---")
    print(f"Total source kCangjie entries parsed: {total_parsed}")
    print(f"Total rows written: {len(entries)}")

    rejected_count = sum(rejections.values())
    print(f"Total source entries rejected: {rejected_count}")
    if rejections:
        print("Rejection details by reason:")
        for reason, count in sorted(rejections.items()):
            print(f"  - {reason}: {count}")
    else:
        print("Rejection details by reason: None (0 rejected)")

    print(f"\nFile: {OUTPUT_TSV}")
    print(f"Size: {size_bytes} bytes")
    print(f"SHA-256: {sha256_hex}")


if __name__ == "__main__":
    main()

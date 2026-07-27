#!/usr/bin/env python3
"""
Import KDE kemoji binary dictionary files (.dict) and convert them to gzip-compressed JSON files.

Data Source: KDE kemoji (https://github.com/KDE/kemoji)
License: Unicode License Agreement (v3) / CC0-1.0 (derived from Unicode CLDR annotations & Unicode Emoji Data)
"""

import glob
import gzip
import json
import os
import pathlib
import struct
import sys
import zlib
import langcodes

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KEMOJI_DIR = pathlib.Path("/tmp/kemoji/data")

CATEGORY_NAMES = {
    0: "Component",
    1: "All",
    2: "Recent",
    3: "Favorite",
    4: "Custom",
    5: "Smileys & Emotion",
    6: "People & Body",
    7: "Animals & Nature",
    8: "Food & Drink",
    9: "Travel & Places",
    10: "Activities",
    11: "Objects",
    12: "Symbols",
    13: "Flags",
}

# Special mappings for language codes in wmkeyboard-data
EXPLICIT_MAPPINGS = {
    "fil": ["fil", "tl"],
    "zh": ["zh", "zh_cn"],
    "zh_Hant": ["zh_tw"],
    "pt": ["pt", "pt_br"],
    "ff_Adlm": ["ff"],
}

def get_language_display_name(code: str) -> str:
    try:
        name = langcodes.Language.get(code.replace('_', '-')).display_name()
        if "Unknown" in name:
            return code
        return name
    except Exception:
        return code

def parse_kemoji_dict(file_path: str):
    """
    Parses Qt qCompress + QDataStream binary .dict file from KDE kemoji.
    Returns list of dicts: {'emoji': ..., 'name': ..., 'keywords': [...], 'category': ..., 'unqualified': ...}
    """
    with open(file_path, "rb") as f:
        data = f.read()

    expected_len = struct.unpack(">I", data[:4])[0]
    decompressed = zlib.decompress(data[4:])
    if len(decompressed) != expected_len:
        raise ValueError(f"Decompressed length mismatch in {file_path}")

    pos = 0

    def read_uint32():
        nonlocal pos
        val = struct.unpack_from(">I", decompressed, pos)[0]
        pos += 4
        return val

    def read_int32():
        nonlocal pos
        val = struct.unpack_from(">i", decompressed, pos)[0]
        pos += 4
        return val

    def read_qstring():
        nonlocal pos
        length = read_uint32()
        if length == 0xFFFFFFFF:
            return ""
        b = decompressed[pos : pos + length]
        pos += length
        return b.decode("utf-16be")

    magic = read_uint32()
    if magic != 0x656D6F6A:
        raise ValueError(f"Invalid magic number {hex(magic)} in {file_path}")
    version = read_uint32()
    count = read_uint32()

    emojis = []
    for _ in range(count):
        unicode_str = read_qstring()
        unqualified_str = read_qstring()
        name_str = read_qstring()
        cat_id = read_int32()
        alt_count = read_uint32()
        alt_names = [read_qstring() for _ in range(alt_count)]

        cat_name = CATEGORY_NAMES.get(cat_id, "Smileys & Emotion")

        item = {
            "emoji": unicode_str,
            "name": name_str,
            "keywords": alt_names,
            "category": cat_name,
        }
        if unqualified_str:
            item["unqualified"] = unqualified_str

        emojis.append(item)

    return emojis

def write_emoji_json_gz(lang_code: str, emojis: list):
    lang_dir = DATA_DIR / lang_code
    lang_dir.mkdir(parents=True, exist_ok=True)

    json_gz_file = lang_dir / f"{lang_code}_emoji.json.gz"
    tsv_gz_file = lang_dir / f"{lang_code}_emoji.tsv.gz"

    # Remove old TSV file if it exists
    if tsv_gz_file.exists():
        tsv_gz_file.unlink()

    with gzip.open(json_gz_file, "wt", encoding="utf-8") as gf:
        json.dump(emojis, gf, ensure_ascii=False, indent=2)

def main():
    if not KEMOJI_DIR.exists():
        print(f"Error: Kemoji directory {KEMOJI_DIR} does not exist. Please clone KDE kemoji first.")
        sys.exit(1)

    dict_files = sorted(KEMOJI_DIR.glob("*.dict"))
    print(f"Found {len(dict_files)} kemoji .dict files in {KEMOJI_DIR}")

    existing_langs = set(
        d.name for d in DATA_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
    )

    kemoji_langs = set(f.stem for f in dict_files)

    targets = {}
    skipped = []

    for fpath in dict_files:
        klang = fpath.stem
        if klang in EXPLICIT_MAPPINGS:
            targets[klang] = EXPLICIT_MAPPINGS[klang]
            continue

        klang_lower = klang.lower().replace("-", "_")
        parts = klang_lower.split("_")
        base_lang = parts[0]

        is_variant = len(parts) > 1

        if is_variant:
            if base_lang in kemoji_langs or base_lang in targets or base_lang in existing_langs:
                skipped.append((klang, f"Base language '{base_lang}' exists, skipping regional subvariant"))
            else:
                targets[klang] = [base_lang]
        else:
            targets[klang] = [klang_lower]

    print(f"Skipping {len(skipped)} regional subvariants.")
    print(f"Processing {len(dict_files) - len(skipped)} kemoji dictionary files into JSON...")

    processed_count = 0
    total_emoji_count = 0

    for klang, lang_codes in sorted(targets.items()):
        dict_file = KEMOJI_DIR / f"{klang}.dict"
        emojis = parse_kemoji_dict(str(dict_file))

        for lang_code in lang_codes:
            write_emoji_json_gz(lang_code, emojis)
            processed_count += 1
            total_emoji_count += len(emojis)

    # Clean up any leftover tsv.gz files across all data dirs
    for old_tsv in DATA_DIR.glob("*/*_emoji.tsv.gz"):
        old_tsv.unlink()

    print(f"\nSuccessfully generated {processed_count} emoji JSON dictionary files.")
    print(f"Total emoji entries written across all files: {total_emoji_count:,}")

if __name__ == "__main__":
    main()

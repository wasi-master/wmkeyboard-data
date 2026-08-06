#!/usr/bin/env python3
"""
import_glot500_sources.py

Imports data from Glot500 (cis-lmu/Glot500 on HuggingFace) for languages
that are weak (< 5,000 words) or empty (0 words) in wmkeyboard-data, and
merges the newly extracted word frequencies with any existing word lists.
"""

import gzip
import os
import re
import collections
from pathlib import Path
from datasets import load_dataset, get_dataset_config_names

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Mapping from wmkeyboard-data folder names to Glot500 config names
# (ISO 639-1 / 639-3 or custom code -> Glot500 dataset config)
GLOT500_MAP = {
    # Empty / Broken
    "arz": ["arz_Arab"],
    "pam": ["pam_Latn"],
    
    # Extremely Weak (< 1,000 words)
    "nap": ["nap_Latn"],
    "tok": ["tok_Latn"],
    
    # Moderately Weak (1,000 - 5,000 words)
    "kg":  ["kon_Latn"],
    "crh": ["crh_Latn", "crh_Cyrl"],
    "kaa": ["kaa_Latn", "kaa_Cyrl"],
    "jbo": ["jbo_Latn"],
    "tlh": ["tlh_Latn"],
    "nr":  ["nbl_Latn"],
    "ban": ["ban_Latn"],
    "sg":  ["sag_Latn"],
    "ak":  ["aka_Latn", "twi_Latn"],
    "ny":  ["nya_Latn"],
    "ln":  ["lin_Latn"],
    "se":  ["sme_Latn"],
    "quc": ["quc_Latn"],
    "bik": ["bcl_Latn"],
    "cv":  ["chv_Cyrl"],
    "udm": ["udm_Cyrl"],
    "mhr": ["mhr_Cyrl"],
    "myv": ["myv_Cyrl"],
    "gag": ["gag_Latn"],
    "dv":  ["div_Thaa"],
    "diq": ["diq_Latn"],
    "ast": ["ast_Latn"],
    "an":  ["arg_Latn"],
    "bar": ["bar_Latn"],
    "dsb": ["dsb_Latn"],
    "hsb": ["hsb_Latn"],
    "pms": ["pms_Latn"],
    "vec": ["vec_Latn"],
    "wa":  ["wln_Latn"],
    "ksh": ["ksh_Latn"],
    "frr": ["frr_Latn"],
    "stq": ["stq_Latn"],
    "vro": ["vro_Latn"],
    "sah": ["sah_Cyrl"],
    "xal": ["xal_Cyrl"],
    "bxr": ["bxr_Cyrl"],
    "ace": ["ace_Latn"],
    "bjn": ["bjn_Latn"],
    "min": ["min_Latn"],
    "pag": ["pag_Latn"],
    "hil": ["hil_Latn"],
    "ilo": ["ilo_Latn"],
    "ceb": ["ceb_Latn"],
    "war": ["war_Latn"],
}

# Regexp for tokenization across different scripts
WORD_TOKENIZER = re.compile(r"[\w'-]+", re.UNICODE)

def load_existing_wordlist(lang_dir: Path, lang_code: str) -> collections.Counter:
    """Load existing word list and frequencies from <lang>_full.txt.gz if present."""
    full_gz = lang_dir / f"{lang_code}_full.txt.gz"
    counter = collections.Counter()
    if not full_gz.exists():
        return counter
    
    try:
        with gzip.open(full_gz, "rt", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[-1].isdigit():
                    word = " ".join(parts[:-1]).lower()
                    freq = int(parts[-1])
                elif len(parts) == 1:
                    word = parts[0].lower()
                    freq = 1
                else:
                    word = line.lower()
                    freq = 1
                
                # Basic sanity check
                if word and not word.isdigit():
                    counter[word] += freq
    except Exception as e:
        print(f"  [Warning] Failed to read existing {full_gz}: {e}")
    
    return counter


def extract_glot500_frequencies(configs: list) -> collections.Counter:
    """Extract word frequencies from Glot500 HuggingFace dataset configs."""
    counter = collections.Counter()
    for conf in configs:
        print(f"  [Glot500] Fetching config '{conf}'...")
        try:
            ds = load_dataset("cis-lmu/Glot500", conf, split="train")
            for item in ds:
                text = item.get("text", "")
                if not text:
                    continue
                tokens = WORD_TOKENIZER.findall(text.lower())
                for tok in tokens:
                    # Filter pure numeric tokens and overly short punctuation artifacts
                    if not tok.isdigit() and len(tok) > 1 or (len(tok) == 1 and tok.isalpha()):
                        counter[tok] += 1
        except Exception as e:
            print(f"  [Error] Failed to load Glot500 config '{conf}': {e}")
    
    return counter


def save_merged_wordlist(lang_dir: Path, lang_code: str, merged_counter: collections.Counter, max_words: int = 150000):
    """Sort, format, and save the merged word frequency list to <lang>_full.txt.gz."""
    lang_dir.mkdir(parents=True, exist_ok=True)
    full_gz = lang_dir / f"{lang_code}_full.txt.gz"
    
    # Sort by frequency descending, then alphabetically
    sorted_words = sorted(merged_counter.items(), key=lambda x: (-x[1], x[0]))
    if max_words:
        sorted_words = sorted_words[:max_words]
        
    with gzip.open(full_gz, "wt", encoding="utf-8") as f:
        for word, freq in sorted_words:
            f.write(f"{word} {freq}\n")
            
    print(f"  [Saved] {full_gz.relative_to(DATA_DIR.parent)} ({len(sorted_words):,} words)")


def main():
    print(f"Starting Glot500 source ingestion for weak languages...")
    print(f"Targeting {len(GLOT500_MAP)} language folders in {DATA_DIR}")
    
    updated_count = 0
    for lang_code, configs in sorted(GLOT500_MAP.items()):
        lang_dir = DATA_DIR / lang_code
        print(f"\nProcessing '{lang_code}' (Glot500 configs: {configs})...")
        
        existing = load_existing_wordlist(lang_dir, lang_code)
        existing_count = len(existing)
        print(f"  Existing words: {existing_count:,}")
        
        glot_counter = extract_glot500_frequencies(configs)
        glot_count = len(glot_counter)
        print(f"  Glot500 extracted words: {glot_count:,}")
        
        if not glot_counter:
            print(f"  [Skipping] No words extracted for '{lang_code}'")
            continue
            
        # Merge frequencies
        merged = existing + glot_counter
        merged_count = len(merged)
        print(f"  Merged unique words: {merged_count:,} (added {merged_count - existing_count:,} new words)")
        
        save_merged_wordlist(lang_dir, lang_code, merged)
        updated_count += 1
        
    print(f"\nCompleted! Successfully updated {updated_count} language dictionaries with Glot500 data.")

if __name__ == "__main__":
    main()

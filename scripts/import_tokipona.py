#!/usr/bin/env python3
"""
Extract words from lipu Linku (official Toki Pona dictionary API: https://api.linku.la/v1/words)
and save as a wordlist for Toki Pona (tok) in data/tok/tok_full.txt.gz.
"""

import json
import gzip
import urllib.request
import ssl
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TOK_DIR = DATA_DIR / "tok"
TOK_FILE = TOK_DIR / "tok_full.txt.gz"
URL = "https://api.linku.la/v1/words"

def main():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    print(f"Fetching Toki Pona word dataset from {URL}...")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        
    print(f"Fetched {len(data)} Toki Pona word entries from lipu Linku.")
    
    word_entries = []
    for word, info in data.items():
        word = unicodedata.normalize("NFKC", word).strip().lower()
        if not word:
            continue
            
        usage_dict = info.get("usage", {})
        if usage_dict:
            freq_pct = max(usage_dict.values())
        else:
            freq_pct = 1.0
            
        # Scale usage percentage (0-100%) to integer frequency score (1-1000)
        freq = max(1, round(freq_pct * 10))
        word_entries.append((word, freq))
        
    # Deduplicate and sort by frequency descending, then alphabetically ascending
    merged = {}
    for w, f in word_entries:
        if w not in merged or f > merged[w]:
            merged[w] = f
            
    sorted_words = sorted(merged.items(), key=lambda x: (-x[1], x[0]))
    
    TOK_DIR.mkdir(parents=True, exist_ok=True)
    with gzip.open(TOK_FILE, "wt", encoding="utf-8") as f:
        for word, freq in sorted_words:
            f.write(f"{word} {freq}\n")
            
    print(f"Successfully saved {len(sorted_words)} Toki Pona words to {TOK_FILE}")

if __name__ == "__main__":
    main()

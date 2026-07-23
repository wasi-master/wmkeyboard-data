#!/usr/bin/env python3
import gzip
import re
import sys
import json
import zipfile
import os
from pathlib import Path
from collections import defaultdict

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
    from huggingface_hub import hf_hub_download

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

HF_LANG_MAP = {
    'hin': 'hi',
    'ben': 'bn',
    'urd': 'ur',
    'tam': 'ta',
    'tel': 'te',
    'mal': 'ml',
    'pan': 'pa',
    'mar': 'mr',
    'guj': 'gu',
    'kan': 'kn',
    'nep': 'ne'
}

def main():
    print("Downloading and processing Aksharantar zip files...")
    
    for hf_lang, wm_lang in HF_LANG_MAP.items():
        print(f"Processing {hf_lang} -> {wm_lang}")
        try:
            zip_path = hf_hub_download(repo_id="ai4bharat/Aksharantar", filename=f"{hf_lang}.zip", repo_type="dataset")
        except Exception as e:
            print(f"Failed to download {hf_lang}.zip: {e}")
            continue
            
        freq_map = defaultdict(int)
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            for fname in z.namelist():
                if 'train' in fname and fname.endswith('.json'):
                    print(f"  Reading {fname} inside zip...")
                    with z.open(fname) as f:
                        for line in f:
                            if not line.strip():
                                continue
                            try:
                                item = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                                
                            eng_word = item.get('english word', '')
                            if not eng_word:
                                continue
                            eng_word = str(eng_word).lower().strip()
                            eng_word = re.sub(r"[^\w'-]", "", eng_word)
                            if not eng_word or not any(c.isalpha() for c in eng_word):
                                continue
                            freq_map[eng_word] += 1
                                
        if not freq_map:
            print(f"  No words found for {wm_lang}")
            continue
            
        print(f"  Saving data for {wm_lang} (from {hf_lang})...")
        out_dir = DATA_DIR / wm_lang
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{wm_lang}_rom.txt.gz"
        
        sorted_entries = sorted(freq_map.items(), key=lambda item: (-item[1], item[0]))
        
        with gzip.open(out_file, "wt", encoding="utf-8") as f:
            for word, freq in sorted_entries:
                f.write(f"{word} {freq}\n")
                
        print(f"  Saved {len(sorted_entries)} unique words to {out_file}")

if __name__ == "__main__":
    main()


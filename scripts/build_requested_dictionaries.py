#!/usr/bin/env python3
"""
Build word frequency lists for:
- bgn (Western Balochi)
- blo (Anii)
- ccp (Chakma)
- fil (Filipino)
- quc (K'iche')
- rhg (Rohingya)
- syr (Syriac)
- yue / yue_Hans (Cantonese Traditional & Simplified)

All data sources are non-GPL (CC-BY, CC-BY-SA, MIT, Apache-2.0, CC0, Public Domain).
"""

import os
import re
import gzip
import urllib.request
import pandas as pd
import xml.etree.ElementTree as ET
from collections import Counter
from datasets import load_dataset
import opencc

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def save_wordlist(lang, counter):
    if not counter:
        print(f"Warning: Counter empty for {lang}")
        return
    lang_dir = os.path.join(DATA_DIR, lang)
    os.makedirs(lang_dir, exist_ok=True)
    out_path = os.path.join(lang_dir, f"{lang}_full.txt.gz")
    
    sorted_words = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    
    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        for word, count in sorted_words:
            if word and not word.isspace():
                f.write(f"{word} {count}\n")
                
    print(f"Saved {lang}: {len(sorted_words)} words to {out_path}")

def build_fil():
    print("--- Building fil (Filipino) ---")
    counter = Counter()
    tl_path = os.path.join(DATA_DIR, "tl", "tl_full.txt.gz")
    if os.path.exists(tl_path):
        with gzip.open(tl_path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.rsplit(" ", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    word = parts[0]
                    count = int(parts[1])
                    counter[word] += count
    save_wordlist("fil", counter)

def build_ccp():
    print("--- Building ccp (Chakma) ---")
    counter = Counter()
    for split in ["monolingual", "parallel"]:
        try:
            ds = load_dataset("amlan107/chakma-nmt-complete-dataset", split=split)
            for row in ds:
                ccp_text = row.get("ccp")
                if ccp_text:
                    words = re.findall(r"[\u11100-\u1114F\w]+", ccp_text)
                    for w in words:
                        if not w.isdigit() and len(w) > 0:
                            counter[w] += 1
        except Exception as e:
            print("Error loading amlan107/chakma-nmt-complete-dataset:", e)
            
    try:
        ds = load_dataset("dipongkar01/chakma-language", split="train")
        for row in ds:
            out_text = str(row.get("output") or "") + " " + str(row.get("input") or "")
            words = re.findall(r"[\u11100-\u1114F\w]+", out_text)
            for w in words:
                if not w.isdigit() and len(w) > 0:
                    counter[w] += 1
    except Exception as e:
        print("Error loading dipongkar01/chakma-language:", e)

    save_wordlist("ccp", counter)

def build_bgn():
    print("--- Building bgn (Western Balochi) ---")
    counter = Counter()
    try:
        ds = load_dataset("Zaanthai/balochi-dictionary", split="train")
        for row in ds:
            w_lat = row.get("word_latin")
            w_arb = row.get("word_arabic")
            freq = row.get("frequency") or 100
            if w_lat:
                counter[w_lat.strip()] += int(freq)
            if w_arb:
                counter[w_arb.strip()] += int(freq)
    except Exception as e:
        print("Error loading Zaanthai/balochi-dictionary:", e)

    try:
        ds = load_dataset("mainkilora/Balochi-Multilingual-dataset", split="train")
        for row in ds:
            inp = str(row.get("input") or "")
            words = re.findall(r"[\u0600-\u06FF\w]+", inp)
            for w in words:
                if not w.isdigit():
                    counter[w] += 5
    except Exception as e:
        print("Error loading mainkilora/Balochi-Multilingual-dataset:", e)

    try:
        ds = load_dataset("shayak111/Balochi-Multilingual-dataset", split="train")
        for row in ds:
            inp = str(row.get("input") or "")
            words = re.findall(r"[\u0600-\u06FF\w]+", inp)
            for w in words:
                if not w.isdigit():
                    counter[w] += 5
    except Exception as e:
        print("Error loading shayak111/Balochi-Multilingual-dataset:", e)

    save_wordlist("bgn", counter)

def build_syr():
    print("--- Building syr (Syriac) ---")
    counter = Counter()
    url = "https://raw.githubusercontent.com/ETCBC/peshitta/master/tf/0.1/word.tf"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            text = resp.read().decode("utf-8")
            words = re.findall(r"[\u0700-\u074F]+", text)
            for w in words:
                counter[w] += 1
    except Exception as e:
        print("Error fetching Syriac Peshitta:", e)
            
    save_wordlist("syr", counter)

def build_blo():
    print("--- Building blo (Anii) ---")
    counter = Counter()
    cldr_urls = [
        "https://raw.githubusercontent.com/unicode-org/cldr/main/common/main/blo.xml",
        "https://raw.githubusercontent.com/unicode-org/cldr/main/common/annotations/blo.xml"
    ]
    for url in cldr_urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp:
                text = resp.read().decode("utf-8")
                root = ET.fromstring(text)
                for elem in root.iter():
                    if elem.text:
                        words = re.findall(r"[a-zA-ZɛɩŋɔʊǝɗɓƐƖŊƆƱƏƊƁ\'’]+", elem.text)
                        for w in words:
                            if len(w) > 1 and not w.isdigit():
                                counter[w] += 1
        except Exception as e:
            print(f"Error fetching CLDR Anii from {url}:", e)
            
    save_wordlist("blo", counter)

def build_ebible_langs():
    print("--- Fetching eBible corpus for rhg, quc ---")
    try:
        df = pd.read_parquet("hf://datasets/DavidCBaines/ebible_corpus/bible_corpus.parquet")
        
        # 1. rhg (Rohingya)
        print("Processing rhg (Rohingya)...")
        rhg_counter = Counter()
        rhg_df = df[df["translation_id"].isin(["rhg", "rhgc"])]
        for text in rhg_df["text"].dropna():
            words = re.findall(r"[\u10D00-\u10D3F\u0600-\u06FF\w]+", text)
            for w in words:
                if not w.isdigit():
                    rhg_counter[w] += 1
        save_wordlist("rhg", rhg_counter)
        
        # 2. quc (K'iche')
        print("Processing quc (K'iche')...")
        quc_counter = Counter()
        quc_df = df[df["translation_id"] == "quctt"]
        for text in quc_df["text"].dropna():
            words = re.findall(r"[a-zA-ZäëïöüÄËÏÖÜ\'’]+", text)
            for w in words:
                if len(w) > 1:
                    quc_counter[w] += 1
        save_wordlist("quc", quc_counter)

    except Exception as e:
        print("Error in build_ebible_langs:", e)

def build_yue_hans():
    print("--- Building yue_Hans (Simplified Cantonese) ---")
    yue_path = os.path.join(DATA_DIR, "yue", "yue_full.txt.gz")
    if not os.path.exists(yue_path):
        print("yue_full.txt.gz does not exist yet.")
        return
        
    converter = opencc.OpenCC("t2s")
    counter = Counter()
    
    with gzip.open(yue_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].isdigit():
                word = parts[0]
                count = int(parts[1])
                simplified_word = converter.convert(word)
                counter[simplified_word] += count
                
    save_wordlist("yue_Hans", counter)

if __name__ == "__main__":
    build_fil()
    build_ccp()
    build_bgn()
    build_syr()
    build_blo()
    build_ebible_langs()
    build_yue_hans()

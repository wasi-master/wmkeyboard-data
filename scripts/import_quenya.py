#!/usr/bin/env python3
"""
Extract words from Ardalambion Quenya word list (https://ardalambion.net/quen-eng.htm)
and save as a wordlist for the Quenya language (qya) in data/qya/qya_full.txt.gz.
"""

import os
import re
import html
import gzip
import urllib.request
import ssl
import unicodedata
from pathlib import Path
import bs4

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QYA_DIR = DATA_DIR / "qya"
QYA_FILE = QYA_DIR / "qya_full.txt.gz"
CACHE_HTML = Path(__file__).resolve().parent.parent / ".cache_quen-eng.htm"

URL = "https://ardalambion.net/quen-eng.htm"

def fetch_html():
    if CACHE_HTML.exists():
        print(f"Reading cached HTML from {CACHE_HTML}")
        with open(CACHE_HTML, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    print(f"Fetching {URL}...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
        
    with open(CACHE_HTML, "w", encoding="utf-8") as f:
        f.write(content)
        
    return content

def expand_parentheses(text):
    m = re.search(r"([a-zA-ZáéíóúÁÉÍÓÚäëïöüÄËÏÖÜâêîôûÂÊÎÔÛñÑþÞāēīōū]+)\(([a-zA-ZáéíóúÁÉÍÓÚäëïöüÄËÏÖÜâêîôûÂÊÎÔÛñÑþÞāēīōū]+)\)([a-zA-ZáéíóúÁÉÍÓÚäëïöüÄËÏÖÜâêîôûÂÊÎÔÛñÑþÞāēīōū]*)", text)
    if m:
        base_before = m.group(1)
        inside = m.group(2)
        base_after = m.group(3)
        w1 = base_before + base_after
        w2 = base_before + inside + base_after
        return expand_parentheses(w1) + expand_parentheses(w2)
    
    text = re.sub(r"\([^)]*\)", " ", text)
    return [text]

def clean_and_normalize(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("ʻ", "'").replace("ʼ", "'").replace("`", "'")
    text = text.replace("ā", "á").replace("ē", "é").replace("ī", "í").replace("ō", "ó").replace("ū", "ú")
    text = unicodedata.normalize("NFC", text)
    return text

VALID_1_LETTER = {"a", "á", "e", "é", "i", "í", "o", "ó", "u", "ú", "y"}

def extract_quenya_words(raw_html):
    soup = bs4.BeautifulSoup(raw_html, "html.parser")
    paragraphs = soup.find_all(["p", "P"])
    extracted = set()

    for p in paragraphs:
        for b in p.find_all(["b", "B"]):
            raw_text = html.unescape(b.get_text()).strip()
            if not raw_text:
                continue
            
            raw_text = re.sub(r"\([^)]*spelt[^)]*\)", "", raw_text, flags=re.I)
            raw_text = re.sub(r'\("([^"]+)"\)', "", raw_text)
            raw_text = re.sub(r"\(see [^)]+\)", "", raw_text, flags=re.I)
            raw_text = re.sub(r"\(also [^)]+\)", "", raw_text, flags=re.I)
            
            parts = re.split(r"[,;/]|\s+-\s+|\s+or\s+|\s+also\s+", raw_text)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                if part.startswith("see ") or part.startswith("so spelt") or part == "variant of" or part == "q.v.":
                    continue
                    
                expanded_parts = expand_parentheses(part)
                for exp in expanded_parts:
                    exp = re.sub(r"[\#\†\?\*\[\]\!\=\`\«\»\(\)]", " ", exp).strip()
                    tokens = re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚäëïöüÄËÏÖÜâêîôûÂÊÎÔÛñÑþÞ\-\']+", exp)
                    for tok in tokens:
                        tok = clean_and_normalize(tok)
                        tok = tok.strip("-'·. ")
                        if not tok:
                            continue
                        
                        subwords = [tok]
                        if "-" in tok:
                            splits = [s.strip("-'·. ") for s in tok.split("-") if s.strip("-'·. ")]
                            subwords.extend(splits)
                            
                        for w in subwords:
                            w = w.strip("-'·. ")
                            if not w:
                                continue
                            if len(w) == 1 and w.lower() not in VALID_1_LETTER:
                                continue
                            if re.search(r"[a-zA-ZáéíóúÁÉÍÓÚäëïöüÄËÏÖÜñÑþÞ]", w):
                                extracted.add(w)
                                extracted.add(w.lower())
                                
    return sorted(list(extracted), key=lambda x: (unicodedata.normalize('NFD', x.lower()), x))

def main():
    raw_html = fetch_html()
    words = extract_quenya_words(raw_html)
    print(f"Extracted {len(words)} unique Quenya words.")

    QYA_DIR.mkdir(parents=True, exist_ok=True)
    with gzip.open(QYA_FILE, "wt", encoding="utf-8") as f:
        for w in words:
            f.write(f"{w} 1\n")
            
    print(f"Saved wordlist to {QYA_FILE}")

if __name__ == "__main__":
    main()

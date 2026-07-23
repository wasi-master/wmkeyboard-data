#!/usr/bin/env python3
"""
Wikipedia Importer

Downloads a Wikipedia XML dump (e.g. https://dumps.wikimedia.org/satwiki/20260701/satwiki-20260701-pages-articles-multistream.xml.bz2),
extracts text using WikiExtractor, removes punctuation and optionally Latin words,
counts word occurrences, and saves a gzipped wordlist file in "word count" format
per line to data/<lang>/<lang>_full.txt.gz.

Usage:
    python3 scripts/wikipedia_importer.py <dump_url_or_path> [options]

Examples:
    python3 scripts/wikipedia_importer.py https://dumps.wikimedia.org/satwiki/20260701/satwiki-20260701-pages-articles-multistream.xml.bz2 --remove-latin
    python3 scripts/wikipedia_importer.py https://dumps.wikimedia.org/orwiki/latest/orwiki-latest-pages-articles.xml.bz2 --lang or
"""

import argparse
import collections
import gzip
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def infer_language_code(url_or_path: str) -> str:
    """Extract language code from Wikipedia dump URL or filename."""
    filename = Path(url_or_path).name
    # Match patterns like satwiki-20260701-pages... or satwiki or /satwiki/
    match = re.search(r'([a-z0-9_]+)wiki', url_or_path, re.IGNORECASE)
    if match:
        code = match.group(1).lower()
        return code
    # Fallback to first part of filename before hyphen or dot
    base = filename.split('-')[0].split('.')[0]
    return base.lower()


def download_file(url: str, dest_path: Path):
    """Download a file with progress reporting."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} to {dest_path}...")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Wikipedia Importer)"})
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        total_size = resp.getheader("Content-Length")
        total_bytes = int(total_size) if total_size else None
        
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_bytes:
                    pct = (downloaded / total_bytes) * 100
                    print(f"\rDownloaded {downloaded / (1024*1024):.1f} / {total_bytes / (1024*1024):.1f} MB ({pct:.1f}%)", end="", flush=True)
                else:
                    print(f"\rDownloaded {downloaded / (1024*1024):.1f} MB", end="", flush=True)
        print()


def run_wikiextractor(dump_path: Path, output_dir: Path, processes: int = None):
    """Run WikiExtractor as a subprocess using python module execution, streaming output to extracted.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "extracted.json"
    print(f"Running WikiExtractor on {dump_path}...")
    
    cmd = [
        sys.executable,
        "-m",
        "wikiextractor.WikiExtractor",
        str(dump_path),
        "-o",
        "-",
        "--json",
        "--quiet",
    ]
    if processes:
        cmd.extend(["--processes", str(processes)])
        
    with open(output_file, "w", encoding="utf-8") as out_f:
        proc = subprocess.run(cmd, stdout=out_f)
        
    if proc.returncode != 0:
        raise RuntimeError(f"WikiExtractor failed with exit code {proc.returncode}")
    print(f"WikiExtractor completed extraction to {output_file}")


def is_latin_word(word: str) -> bool:
    """Check if word contains any ASCII Latin letters [a-zA-Z]."""
    return bool(re.search(r'[a-zA-Z]', word))


def extract_words_from_text(text: str, remove_latin: bool = False, min_length: int = 1) -> list[str]:
    """
    Normalize text, remove punctuation, digits, symbols,
    and optionally filter out Latin script words.
    """
    text = unicodedata.normalize("NFKC", text)
    
    cleaned_chars = []
    for char in text:
        cat = unicodedata.category(char)
        # Keep letters (L) and marks (M) - replace punctuation (P), symbols (S), numbers (N) with space
        if cat.startswith("L") or cat.startswith("M"):
            cleaned_chars.append(char)
        else:
            cleaned_chars.append(" ")
            
    cleaned_text = "".join(cleaned_chars)
    tokens = cleaned_text.split()
    
    words = []
    for token in tokens:
        token = token.lower()
        if len(token) < min_length:
            continue
        if remove_latin and is_latin_word(token):
            continue
        words.append(token)
        
    return words


def process_extracted_files(extract_dir: Path, remove_latin: bool = False, min_length: int = 1) -> collections.Counter:
    """
    Walk through WikiExtractor files and count word frequencies.
    Handles JSON format, XML <doc> tag format, and raw text format.
    """
    counts = collections.Counter()
    file_count = 0
    article_count = 0
    
    for root, _, files in os.walk(extract_dir):
        for fname in sorted(files):
            if fname.startswith("."):
                continue
            filepath = Path(root) / fname
            file_count += 1
            
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                current_article_lines = []
                
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    
                    # Try parsing JSON format
                    if line_str.startswith("{") and line_str.endswith("}"):
                        try:
                            doc = json.loads(line_str)
                            text = doc.get("text", "")
                            if text:
                                article_count += 1
                                words = extract_words_from_text(text, remove_latin=remove_latin, min_length=min_length)
                                counts.update(words)
                            continue
                        except json.JSONDecodeError:
                            pass
                    
                    # Handle XML <doc> / </doc> format or raw text
                    if line_str.startswith("<doc") or line_str.startswith("</doc>"):
                        if current_article_lines:
                            article_text = "\n".join(current_article_lines)
                            if article_text.strip():
                                article_count += 1
                                words = extract_words_from_text(article_text, remove_latin=remove_latin, min_length=min_length)
                                counts.update(words)
                            current_article_lines = []
                    else:
                        current_article_lines.append(line_str)
                        
                if current_article_lines:
                    article_text = "\n".join(current_article_lines)
                    if article_text.strip():
                        article_count += 1
                        words = extract_words_from_text(article_text, remove_latin=remove_latin, min_length=min_length)
                        counts.update(words)
                        
    print(f"Processed {article_count} articles across {file_count} extracted files.")
    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Download and import Wikipedia dumps into frequency wordlists."
    )
    parser.add_argument(
        "url_or_path",
        help="URL or local filepath to Wikipedia XML dump (.xml.bz2 or .xml)",
    )
    parser.add_argument(
        "--lang",
        help="Language code (e.g. 'sat', 'or', 'bn'). Inferred from dump URL if not specified.",
    )
    parser.add_argument(
        "--remove-latin",
        action="store_true",
        help="Remove words containing Latin script letters (a-z, A-Z).",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Path to save gzipped wordlist (default: data/<lang>/<lang>_full.txt.gz).",
    )
    parser.add_argument(
        "--min-freq",
        type=int,
        default=1,
        help="Minimum word frequency threshold to include in output (default: 1).",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=1,
        help="Minimum word length to include (default: 1).",
    )
    parser.add_argument(
        "--processes",
        type=int,
        help="Number of parallel processes for WikiExtractor.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Do not delete temporary downloaded and extracted dump files.",
    )
    
    args = parser.parse_args()
    
    lang = args.lang or infer_language_code(args.url_or_path)
    print(f"Target language code: {lang}")
    
    # Setup paths
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        lang_dir = DATA_DIR / lang
        output_path = lang_dir / f"{lang}_full.txt.gz"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    url_or_path = args.url_or_path
    is_url = url_or_path.startswith("http://") or url_or_path.startswith("https://")
    
    temp_dir = Path(tempfile.mkdtemp(prefix=f"wiki_import_{lang}_"))
    
    try:
        if is_url:
            filename = Path(url_or_path).name
            dump_file = temp_dir / filename
            download_file(url_or_path, dump_file)
        else:
            dump_file = Path(url_or_path).resolve()
            if not dump_file.exists():
                sys.exit(f"Error: Local file {dump_file} does not exist.")
                
        extract_dir = temp_dir / "extracted"
        run_wikiextractor(dump_file, extract_dir, processes=args.processes)
        
        print("Extracting words and computing frequencies...")
        counts = process_extracted_files(
            extract_dir, remove_latin=args.remove_latin, min_length=args.min_length
        )
        
        # Filter by min_freq and sort
        sorted_words = [
            (word, count)
            for word, count in counts.items()
            if count >= args.min_freq
        ]
        sorted_words.sort(key=lambda x: (-x[1], x[0]))
        
        print(f"Writing {len(sorted_words)} unique words to {output_path}...")
        with gzip.open(output_path, "wt", encoding="utf-8") as f:
            for word, count in sorted_words:
                f.write(f"{word} {count}\n")
                
        file_size_kb = output_path.stat().st_size / 1024
        print(f"Successfully generated {output_path} ({file_size_kb:.1f} KB, {len(sorted_words)} words).")
        
    finally:
        if not args.keep_temp:
            print(f"Cleaning up temporary directory {temp_dir}...")
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()

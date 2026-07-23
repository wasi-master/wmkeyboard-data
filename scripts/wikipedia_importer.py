#!/usr/bin/env python3
"""
Wikipedia Importer

Downloads Wikipedia XML dumps (e.g. https://dumps.wikimedia.org/satwiki/20260701/satwiki-20260701-pages-articles-multistream.xml.bz2),
extracts text using WikiExtractor, removes punctuation and optionally Latin words,
counts word occurrences, and saves gzipped wordlist files in "word count" format
per line to data/<lang>/<lang>_full.txt.gz.

Supports multi-threaded downloads/imports across CPU cores for processing multiple wikis in parallel.

Usage:
    python3 scripts/wikipedia_importer.py <dump_url_or_path> [options]
    python3 scripts/wikipedia_importer.py -f links.txt -t 8 [options]
    python3 scripts/wikipedia_importer.py url1 url2 url3 -t 4 [options]

Examples:
    python3 scripts/wikipedia_importer.py https://dumps.wikimedia.org/satwiki/20260701/satwiki-20260701-pages-articles-multistream.xml.bz2 --remove-latin
    python3 scripts/wikipedia_importer.py -f wiki_links.txt -t 8 --remove-latin
"""

import argparse
import collections
import concurrent.futures
import gzip
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
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


def download_file(url: str, dest_path: Path, prefix: str = "", verbose_progress: bool = True):
    """Download a file with progress reporting."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    p_str = f"{prefix} " if prefix else ""
    print(f"{p_str}Downloading {url} to {dest_path}...")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Wikipedia Importer)"})
    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        total_size = resp.getheader("Content-Length")
        total_bytes = int(total_size) if total_size else None
        
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        last_log_time = 0
        
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                
                now = time.time()
                if verbose_progress:
                    if total_bytes:
                        pct = (downloaded / total_bytes) * 100
                        print(f"\r{p_str}Downloaded {downloaded / (1024*1024):.1f} / {total_bytes / (1024*1024):.1f} MB ({pct:.1f}%)", end="", flush=True)
                    else:
                        print(f"\r{p_str}Downloaded {downloaded / (1024*1024):.1f} MB", end="", flush=True)
                else:
                    if now - last_log_time >= 5:
                        if total_bytes:
                            pct = (downloaded / total_bytes) * 100
                            print(f"{p_str}Downloaded {downloaded / (1024*1024):.1f} / {total_bytes / (1024*1024):.1f} MB ({pct:.1f}%)")
                        else:
                            print(f"{p_str}Downloaded {downloaded / (1024*1024):.1f} MB")
                        last_log_time = now
        if verbose_progress:
            print()
        else:
            print(f"{p_str}Finished downloading {url}")


def run_wikiextractor(dump_path: Path, output_dir: Path, processes: int = None, prefix: str = ""):
    """Run WikiExtractor as a subprocess using python module execution, streaming output to extracted.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "extracted.json"
    p_str = f"{prefix} " if prefix else ""
    print(f"{p_str}Running WikiExtractor on {dump_path}...")
    
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
    print(f"{p_str}WikiExtractor completed extraction to {output_file}")


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


def process_extracted_files(extract_dir: Path, remove_latin: bool = False, min_length: int = 1, prefix: str = "") -> collections.Counter:
    """
    Walk through WikiExtractor files and count word frequencies.
    Handles JSON format, XML <doc> tag format, and raw text format.
    """
    p_str = f"{prefix} " if prefix else ""
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
                        
    print(f"{p_str}Processed {article_count} articles across {file_count} extracted files.")
    return counts


def process_single_dump(url_or_path: str, args, multi_threaded: bool = False) -> tuple[bool, str]:
    """Process a single Wikipedia dump URL or file path. Returns (success, result_message)."""
    lang = args.lang or infer_language_code(url_or_path)
    prefix = f"[{lang}]"
    p_str = f"{prefix} "
    print(f"{p_str}Target language code: {lang}")
    
    if args.output:
        if multi_threaded:
            output_path = Path(args.output).parent / f"{lang}_full.txt.gz"
        else:
            output_path = Path(args.output).resolve()
    else:
        lang_dir = DATA_DIR / lang
        output_path = lang_dir / f"{lang}_full.txt.gz"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    is_url = url_or_path.startswith("http://") or url_or_path.startswith("https://")
    temp_dir = Path(tempfile.mkdtemp(prefix=f"wiki_import_{lang}_"))
    
    try:
        if is_url:
            filename = Path(url_or_path).name
            dump_file = temp_dir / filename
            download_file(url_or_path, dump_file, prefix=prefix, verbose_progress=not multi_threaded)
        else:
            dump_file = Path(url_or_path).resolve()
            if not dump_file.exists():
                msg = f"{p_str}Error: Local file {dump_file} does not exist."
                print(msg)
                return False, msg
                
        extract_dir = temp_dir / "extracted"
        processes = args.processes if args.processes else (1 if multi_threaded else None)
        run_wikiextractor(dump_file, extract_dir, processes=processes, prefix=prefix)
        
        print(f"{p_str}Extracting words and computing frequencies...")
        counts = process_extracted_files(
            extract_dir, remove_latin=args.remove_latin, min_length=args.min_length, prefix=prefix
        )
        
        # Filter by min_freq and sort
        sorted_words = [
            (word, count)
            for word, count in counts.items()
            if count >= args.min_freq
        ]
        sorted_words.sort(key=lambda x: (-x[1], x[0]))
        
        print(f"{p_str}Writing {len(sorted_words)} unique words to {output_path}...")
        with gzip.open(output_path, "wt", encoding="utf-8") as f:
            for word, count in sorted_words:
                f.write(f"{word} {count}\n")
                
        file_size_kb = output_path.stat().st_size / 1024
        msg = f"{p_str}Successfully generated {output_path} ({file_size_kb:.1f} KB, {len(sorted_words)} words)."
        print(msg)
        return True, msg
    except Exception as e:
        msg = f"{p_str}Failed processing {url_or_path}: {e}"
        print(msg)
        return False, msg
    finally:
        if not args.keep_temp:
            print(f"{p_str}Cleaning up temporary directory {temp_dir}...")
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="Download and import Wikipedia dumps into frequency wordlists."
    )
    parser.add_argument(
        "url_or_path",
        nargs="*",
        help="URL(s) or local filepath(s) to Wikipedia XML dump (.xml.bz2 or .xml)",
    )
    parser.add_argument(
        "-f", "--file",
        help="Text file containing a list of Wikipedia dump URLs to process",
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=1,
        help="Number of concurrent download/import worker threads (default: 1; set to 0 or -1 to use all CPU cores).",
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
        help="Number of parallel processes for WikiExtractor per dump.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Do not delete temporary downloaded and extracted dump files.",
    )
    
    args = parser.parse_args()
    
    links = []
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: File '{args.file}' not found.")
            sys.exit(1)
            
        with open(file_path, "r", encoding="utf-8") as f:
            links.extend([line.strip() for line in f if line.strip() and not line.startswith("#")])
            
    if args.url_or_path:
        links.extend(args.url_or_path)
        
    if not links:
        parser.print_help()
        sys.exit(1)
        
    cpu_cores = os.cpu_count() or 4
    if args.threads <= 0:
        max_workers = cpu_cores
    else:
        max_workers = args.threads
        
    multi_threaded = len(links) > 1 and max_workers > 1
    
    print(f"Processing {len(links)} dump(s) using {max_workers} worker thread(s)... (CPU cores available: {cpu_cores})")
    
    results = []
    if multi_threaded:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_link = {
                executor.submit(process_single_dump, link, args, True): link
                for link in links
            }
            for future in concurrent.futures.as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    success, msg = future.result()
                    results.append((link, success, msg))
                except Exception as exc:
                    results.append((link, False, str(exc)))
    else:
        for link in links:
            success, msg = process_single_dump(link, args, multi_threaded=False)
            results.append((link, success, msg))
            
    print("\n" + "=" * 50)
    print("IMPORT SUMMARY")
    print("=" * 50)
    successes = sum(1 for _, s, _ in results if s)
    failures = sum(1 for _, s, _ in results if not s)
    print(f"Total: {len(results)} | Succeeded: {successes} | Failed: {failures}\n")
    
    for link, success, msg in results:
        status_tag = "[SUCCESS]" if success else "[FAILED]"
        print(f"{status_tag} {link} -> {msg}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""Download a Leipzig Coropora Collection tarball, extract the words.txt wordlist,
convert it to the project's "word frequency" format, gzip it, and place it in
data/<lang>/<lang>_full.txt.gz.

Usage:
    python3 scripts/import_leipzig.py <code> <size>
        e.g. python3 scripts/import_leipzig.py hye 300k

    python3 scripts/import_leipzig.py <url>
        e.g. python3 scripts/import_leipzig.py https://downloads.wortschatz-leipzig.de/corpora/hye_wikipedia_2021_300K.tar.gz
"""

import argparse
import gzip
import json
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

from tqdm import tqdm

SCRIPT_DIR = Path(__file__).resolve().parent
JSON_PATH = SCRIPT_DIR / "leipzig.json"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

BASE_URL = "https://downloads.wortschatz-leipzig.de/corpora"

ISO6393_TO_FOLDER = {
    "afr": "af",
    "amh": "am",
    "ara": "ar",
    "arg": "an",
    "asm": "as",
    "ast": "ast",
    "aze": "az",
    "bak": "ba",
    "bar": "bar",
    "bel": "be",
    "ben": "bn",
    "bho": "bho",
    "bik": "bik",
    "bos": "bs",
    "bre": "br",
    "bua": "bua",
    "bul": "bg",
    "ces": "cs",
    "dan": "da",
    "deu": "de",
    "ell": "el",
    "eng": "en",
    "est": "et",
    "fin": "fi",
    "fra": "fr",
    "guj": "gu",
    "hin": "hi",
    "hau": "ha",
    "hye": "hy",
    "ibo": "ig",
    "ita": "it",
    "kan": "kn",
    "kaz": "kk",
    "kat": "ka",
    "kck": "kck",
    "khm": "km",
    "lat": "la",
    "lao": "lo",
    "lug": "lg",
    "mar": "mr",
    "mon": "mn",
    "msa": "ms",
    "mya": "my",
    "nep": "ne",
    "nld": "nl",
    "glg": "gl",
    "nso": "nso",
    "ori": "or",
    "pan": "pa",
    "epo": "eo",
    "eus": "eu",
    "pol": "pl",
    "por": "pt",
    "lav": "lv",
    "ron": "ro",
    "run": "rn",
    "rus": "ru",
    "sin": "si",
    "sna": "sna",
    "sot": "st",
    "spa": "es",
    "swa": "sw",
    "swe": "sv",
    "tam": "ta",
    "tat": "tt",
    "tel": "te",
    "tgl": "tl",
    "tha": "th",
    "tso": "ts",
    "tur": "tr",
    "ukr": "uk",
    "urd": "ur",
    "uzb": "uz",
    "vie": "vi",
    "xho": "xh",
    "yor": "yo",
    "zul": "zu",
}

PREFERRED_TYPES = ["wikipedia", "web", "community", "news", "newscrawl"]


def extract_lang_code(url_or_filename: str) -> str:
    name = Path(url_or_filename).name
    stem = name
    if stem.endswith(".tar.gz"):
        stem = stem[: -len(".tar.gz")]
    elif stem.endswith(".tgz"):
        stem = stem[:-4]
    elif stem.endswith(".tar"):
        stem = stem[:-4]
    return stem.split("_")[0].split("-")[0]


def resolve_lang_folder(code: str) -> str:
    if code in ISO6393_TO_FOLDER:
        return ISO6393_TO_FOLDER[code]
    print(f"WARNING: no folder mapping for code '{code}', using code as folder name")
    exit()
    if len(code) <= 2:
        return code
    short = code[:2]
    if (DATA_DIR / short).is_dir():
        return short
    return code


def download(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "WMKeyboard-DictBuilder/1.0"})
    with urlopen(req) as response, open(dest, "wb") as f:
        total_size = int(response.headers.get("Content-Length", 0))
        with tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading") as bar:
            while chunk := response.read(8192):
                f.write(chunk)
                bar.update(len(chunk))


def load_index() -> list:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_size(size: str) -> str:
    size = size.strip()
    size_lower = size.lower()
    if size_lower.endswith("k"):
        return size.upper()
    if size_lower.endswith("m"):
        return size.upper()
    return size


def find_corpus(code: str, size: str, index: list) -> str:
    code = code.lower()
    size_norm = normalize_size(size)

    candidates = []
    for entry in index:
        name = entry["corpusName"]
        parts = name.split("_")
        entry_code = parts[0].split("-")[0].lower()
        entry_size = parts[-1]
        if entry_code == code and entry_size.lower() == size_norm.lower():
            candidates.append(entry)

    if candidates:
        def sort_key(entry):
            name = entry["corpusName"].lower()
            score = len(PREFERRED_TYPES)
            for i, pref in enumerate(PREFERRED_TYPES):
                if pref in name:
                    score = i
                    break
            year = 0
            for part in name.split("_"):
                if part.isdigit() and len(part) == 4:
                    year = int(part)
                    break
            return (score, -year)

        candidates.sort(key=sort_key)
        return candidates[0]["corpusName"]

    return None


def build_url(corpus_name: str) -> str:
    return f"{BASE_URL}/{corpus_name}.tar.gz"


def fallback_url(code: str, size: str) -> str:
    code = code.lower()
    size_norm = normalize_size(size)
    return build_url(f"{code}_wikipedia_2021_{size_norm}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a Leipzig Corpora Collection wordlist")
    parser.add_argument(
        "target",
        help="Leipzig download URL, or ISO 639-3 code + size (e.g. hye 300k)",
    )
    parser.add_argument(
        "size",
        nargs="?",
        help="Word count size when target is a code (e.g. 300k, 1M)",
    )
    args = parser.parse_args()

    index = load_index()

    url = None
    code = None

    if args.size is None:
        if args.target.startswith("http://") or args.target.startswith("https://"):
            url = args.target
            code = extract_lang_code(url)
        else:
            print("ERROR: provide both a code and a size, or a full URL")
            sys.exit(1)
    else:
        code = args.target
        size = args.size
        corpus_name = find_corpus(code, size, index)
        if corpus_name:
            url = build_url(corpus_name)
            print(f"Resolved:       {corpus_name}")
        else:
            url = fallback_url(code, size)
            if url:
                print(f"Resolved:       {code}_wikipedia_*_{size.upper()} (from naming convention)")
            else:
                print(f"ERROR: no corpus found for code={code} size={size}")
                sys.exit(1)

    lang_folder = resolve_lang_folder(code)
    url_filename = Path(url).name

    print(f"Leipzig code:    {code}")
    print(f"Target folder:   {lang_folder}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tarball = tmp_path / url_filename

        print(f"Downloading {url}")
        download(url, tarball)

        print("Extracting tarball ...")
        with tarfile.open(tarball, "r:gz") as tar:
            tar.extractall(tmp_path, filter="data")

        candidates = sorted(tmp_path.rglob("*words.txt"))
        if not candidates:
            print("ERROR: no *words.txt found inside tarball")
            sys.exit(1)
        words_path = candidates[0]
        print(f"Found wordlist:   {words_path.name}")

        out_dir = DATA_DIR / lang_folder
        out_dir.mkdir(parents=True, exist_ok=True)
        out_txt = out_dir / f"{lang_folder}_full.txt"
        out_gz = out_dir / f"{lang_folder}_full.txt.gz"

        print(f"Converting format and writing {out_txt.name}")
        with open(words_path, "r", encoding="utf-8", errors="ignore") as inf, \
             open(out_txt, "w", encoding="utf-8") as outf:
            for line in inf:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 3:
                    outf.write(f"{parts[1]} {parts[2]}\n")
                elif len(parts) == 2:
                    outf.write(f"{parts[0]} {parts[1]}\n")
                elif parts:
                    outf.write(line)

        print(f"Compressing to {out_gz.name}")
        with open(out_txt, "rb") as f_in, gzip.open(out_gz, "wb") as f_out:
            f_out.writelines(f_in)

        print(f"Removing temporary {out_txt.name}")
        out_txt.unlink()

        print(f"Done -> {out_gz}")


if __name__ == "__main__":
    main()

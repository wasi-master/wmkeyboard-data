#!/usr/bin/env python3

"""Download a Leipzig Corpora Collection tarball, extract the words.txt wordlist,
convert it to the project's "word frequency" format, gzip it, and place it in
data/<lang>/<lang>_full.txt.gz.

Usage:
    python3 scripts/import_leipzig.py <code> <size>
        e.g. python3 scripts/import_leipzig.py hye 300k

    python3 scripts/import_leipzig.py <url>
        e.g. python3 scripts/import_leipzig.py https://downloads.wortschatz-leipzig.de/corpora/hye_wikipedia_2021_300K.tar.gz

    python3 scripts/import_leipzig.py --file links.txt
        Downloads and processes multiple URLs listed in a text file sequentially.
"""

import argparse
import gzip
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

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
    "kas": "ks",
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
    "kas": "ks",   # Kashmiri
    "lat": "la",   # Latin
    "ltz": "lb",   # Luxembourgish
    "mai": "mai",  # Maithili (No 2-letter code exists)
    "plt": "plt",  # Plateau Malagasy (No 2-letter code exists)
    "mwl": "mwl",  # Mirandese (No 2-letter code exists)
    "nob": "nb",   # Norwegian Bokmål
    "pms": "pms",  # Piedmontese (No 2-letter code exists)
    "san": "sa",   # Sanskrit
    "ceb": "ceb",  # Cebuano (No 2-letter code exists)
    "kab": "kab",  # Kabyle (No 2-letter code exists)
    "gle": "ga",   # Irish
    "srd": "sc",   # Sardinian
    "snd": "sd",   # Sindhi
    "tcy": "tcy",   # Tulu (No 2-letter code exists)
    "jav": "jv",       # Javanese
    "pus": "ps",       # Pashto
    "xho": "xh",       # Xhosa
    "som": "so",       # Somali
    "aka": "ak",       # Akan
    "hat": "ht",       # Haitian Creole
    "wol": "wo",       # Wolof
    "que": "qu",       # Quechua
    "kir": "ky",       # Kyrgyz
    "bod": "bo",       # Tibetan
    "tgk": "tg",       # Tajik
    "tir": "ti",       # Tigrinya
    "bam": "bm",       # Bambara
    "nya": "ny",       # Chichewa / Nyanja
    "ful": "ff",       # Fulah
    "lug": "lg",       # Ganda / Luganda
    "ssw-za": "ss-ZA", # Swati (South Africa)
    "sot": "st",       # Southern Sotho
    "tsn": "tn",       # Tswana
    "tuk": "tk",       # Turkmen
    "uig": "ug",       # Uyghur
    "mlt": "mt",       # Maltese
    "cym": "cy",       # Welsh
    "sco": "sco",      # Scots (No 2-letter code exists)
    "mri-nz": "mi-NZ", # Maori (New Zealand)
    "nav": "nv",       # Navajo
    "fao": "fo",       # Faroese
    "kal-gl": "kl-GL", # Kalaallisut / Greenlandic (Greenland)
    "cos": "co",       # Corsican
    "oci": "oc",       # Occitan
    "roh": "rm",       # Romansh
    "arg": "an",       # Aragonese
    "bak": "ba",       # Bashkir
    "che": "ce",       # Chechen
    "chv": "cv",       # Chuvash
    "kon": "kg",       # Kongo
    "aar": "aa",       # Afar
    "ewe": "ee",       # Ewe
    "fry": "fy",       # Western Frisian
    "grn": "gn",       # Guarani
    "ido": "io",       # Ido
    "ina": "ia",       # Interlingua
    "ile": "ie",       # Interlingue
    "kik": "ki",       # Kikuyu
    "lim": "li",       # Limburgish
    "lin": "ln",       # Lingala
    "div-mv": "dv-MV", # Divehi / Maldivian (Maldives)
    "glv": "gv",       # Manx
    "nbl": "nr",       # South Ndebele
    "ndo": "nd",       # North Ndebele
    "sme": "se",       # Northern Sami
    "nno": "nn",       # Norwegian Nynorsk
    "orm": "om",       # Oromo
    "oss": "os",       # Ossetian
    "run": "rn",       # Rundi
    "kin_": "rw",      # Kinyarwanda (accounting for the underscore in your key)
    "sna-zw": "sn-ZW", # Shona (Zimbabwe)
    "hbs": "sh",       # Serbo-Croatian
    "sun-id": "su-ID", # Sundanese (Indonesia)
    "tat": "tt",       # Tatar
    "tso": "ts",       # Tsonga
    "ven": "ve",       # Venda
    "vol": "vo",       # Volapük
    "wln": "wa",       # Walloon
    "yid": "yi",       # Yiddish
    "zha": "za",       # Zhuang
    "kur": "ku",        # Kurdish
    "ckb": "ckb",       # Central Kurdish (Sorani)
    "min": "min",       # Minangkabau
    "mad": "mad",       # Madurese
    "bug": "bug",       # Buginese
    "ban": "ban",       # Balinese
    "ilo": "ilo",       # Ilocano
    "war": "war",       # Waray
    "bcl": "bcl",       # Bicolano
    "knn": "kok",       # Maharashtrian Konkani
    "gom": "kok",       # Goan Konkani
    "kok": "kok"        # Konkani
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
    if len(code) <= 2:
        return code
    short = code[:2]
    if (DATA_DIR / short).is_dir():
        return short
    return code


def download(url: str, dest: Path) -> None:
    """Download file using aria2c."""
    command = [
        "aria2c",
        "--console-log-level=warn",
        "--summary-interval=1",
        "-x", "16",                 # Max connection per server
        "-s", "16",                 # Split file into 16 parts
        "--min-split-size=1M",
        "-d", str(dest.parent),
        "-o", str(dest.name),
        url
    ]

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("\nERROR: 'aria2c' is not installed or not in PATH.")
        print("Please install it (e.g., 'sudo apt install aria2c' or 'brew install aria2').")
        raise
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: aria2c failed with return code {e.returncode}")
        raise


def load_index() -> list:
    if JSON_PATH.exists():
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


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


def process_item(target: str, size: str, index: list) -> None:
    url = None
    code = None

    if size is None:
        if target.startswith("http://") or target.startswith("https://"):
            url = target
            code = extract_lang_code(url)
        else:
            print(f"ERROR: target '{target}' is not a valid URL.")
            return
    else:
        code = target
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
                return

    lang_folder = resolve_lang_folder(code)
    url_filename = Path(url).name

    print(f"Leipzig code:    {code}")
    print(f"Target folder:   {lang_folder}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tarball = tmp_path / url_filename

        print(f"Downloading {url} ...")
        try:
            download(url, tarball)
        except Exception as e:
            print(f"ERROR: Failed to download {url}: {e}")
            return

        print("Extracting tarball ...")
        try:
            with tarfile.open(tarball, "r:gz") as tar:
                tar.extractall(tmp_path, filter="data")
        except Exception as e:
            print(f"ERROR: failed to extract {tarball.name}: {e}")
            return

        candidates = sorted(tmp_path.rglob("*words.txt"))
        if not candidates:
            print("ERROR: no *words.txt found inside tarball")
            return

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

        print(f"Done -> {out_gz}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a Leipzig Corpora Collection wordlist")
    parser.add_argument(
        "target",
        nargs="?",
        help="Leipzig download URL, or ISO 639-3 code (e.g. hye)",
    )
    parser.add_argument(
        "size",
        nargs="?",
        help="Word count size when target is a code (e.g. 300k, 1M)",
    )
    parser.add_argument(
        "-f", "--file",
        help="Text file containing a list of URLs to download sequentially",
    )
    args = parser.parse_args()

    # Need at least a file, or a target
    if not args.file and not args.target:
        parser.print_help()
        sys.exit(1)

    index = load_index()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: File '{args.file}' not found.")
            sys.exit(1)

        with open(file_path, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        print(f"Found {len(links)} links in {args.file}. Starting sequential download...")
        for i, link in enumerate(links, 1):
            print(f"--- Processing item {i}/{len(links)} ---")
            process_item(link, None, index)
            print("-" * 40)
    else:
        # Standard fallback for positional arguments
        if args.size is None and not (args.target.startswith("http://") or args.target.startswith("https://")):
            print("ERROR: provide both a code and a size, or a full URL")
            sys.exit(1)

        process_item(args.target, args.size, index)


if __name__ == "__main__":
    main()

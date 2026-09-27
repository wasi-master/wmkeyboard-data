#!/usr/bin/env python3
"""Build one offline language pack per folder of data/.

    python scripts/build_language_packs.py OUT_DIR [FOLDER ...]

Each pack is `wmkb-lang-<folder>.zip` and holds everything WM Keyboard would
otherwise download for the languages in that folder: word lists
(`<code>_full.txt.gz`, `<code>_aosp.txt.gz`, the romanized ones), word pairs
(`<code>_bigrams.txt.gz`, `<code>_trigrams.txt.gz`) and emoji names
(`<code>_emoji.json.gz`). Chinese, Japanese and Cantonese also carry their
conversion dictionaries from cjk/. The app's "Import" on a language's screen
installs a pack as it is, recognising each file by its name, so a phone with
no internet (or a build with no internet permission) gets the same data a
download would.

The offensive-word lists are left out: the app never downloads them. The
repository's LICENSE and NOTICE go in every pack, and the licence of each
conversion dictionary goes in with it.

Zips are built deterministically (fixed timestamps, sorted entries), so an
unchanged folder rebuilds to the same bytes and the workflow can skip
re-uploading it. Files that are already gzip are stored, not deflated again.
"""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CJK = ROOT / "cjk"

# Conversion dictionaries, by the folder of the language they serve. Mirrors
# CjkDictCatalog in the app (langId and path of each pack).
CJK_BY_FOLDER = {
    "zh": ["pinyin.tsv", "stroke.tsv", "cangjie.tsv"],
    "ja": ["ja_kana.tsv"],
    "yue": ["jyutping.tsv"],
}

# The licence file that goes with each conversion dictionary, where there is one.
CJK_LICENSES = {
    "ja_kana.tsv": "LICENSE_mozc.txt",
    "stroke.tsv": "LICENSE_stroke.txt",
    "cangjie.tsv": "LICENSE_cangjie.txt",
    "jyutping.tsv": "LICENSE_jyutping.txt",
}

FIXED_TIME = (2024, 1, 1, 0, 0, 0)


def wanted(path: Path) -> bool:
    name = path.name
    if not path.is_file() or name.startswith("."):
        return False
    if "_offensive" in name:
        return False
    return name.endswith((".txt.gz", ".json.gz"))


def add(archive: zipfile.ZipFile, source: Path, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname, date_time=FIXED_TIME)
    info.external_attr = 0o644 << 16
    info.compress_type = zipfile.ZIP_STORED if source.suffix == ".gz" else zipfile.ZIP_DEFLATED
    archive.writestr(info, source.read_bytes())


def build(folder: str, out_dir: Path) -> Path | None:
    files = sorted(p for p in (DATA / folder).iterdir() if wanted(p))
    cjk = [CJK / name for name in CJK_BY_FOLDER.get(folder, []) if (CJK / name).is_file()]
    if not files and not cjk:
        return None
    target = out_dir / f"wmkb-lang-{folder}.zip"
    with zipfile.ZipFile(target, "w") as archive:
        for extra in ("LICENSE", "NOTICE"):
            if (ROOT / extra).is_file():
                add(archive, ROOT / extra, extra)
        for path in files:
            add(archive, path, f"data/{folder}/{path.name}")
        for path in cjk:
            add(archive, path, f"cjk/{path.name}")
            license_name = CJK_LICENSES.get(path.name)
            if license_name and (CJK / license_name).is_file():
                add(archive, CJK / license_name, f"cjk/{license_name}")
    return target


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    folders = sys.argv[2:] or sorted(p.name for p in DATA.iterdir() if p.is_dir())
    built = 0
    for folder in folders:
        if not (DATA / folder).is_dir():
            continue
        target = build(folder, out_dir)
        if target is not None:
            built += 1
            print(f"{target.name}\t{target.stat().st_size}")
    print(f"{built} packs", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

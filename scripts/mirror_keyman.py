#!/usr/bin/env python3
"""
Mirror the typing rules (.kmx) of every Keyman keyboard WM Keyboard bundles, as
keyman/<id>/<id>.kmx.gz, for the app to fall back on when keyman.com is down or
no longer serves a keyboard.

The app asks keyman.com first, every time. This copy is only read when that
fails, so a mirror a few versions behind costs nothing but freshness, and the
next successful request to keyman.com replaces it on the phone.

Source: https://api.keyman.com/keyboard/<id> for the current version and
licence, then https://downloads.keyman.com/keyboards/<id>/<version>/<pkg>. Only
keyboards whose licence the API reports as "mit" are mirrored, which is the same
check the app makes before it downloads rules at all; the upstream repository
also holds freeware keyboards whose terms do not allow redistribution.

What each keyboard folder holds:
- <id>.kmx.gz   the .kmx from the package, byte for byte, gzip-compressed
                (mtime 0, so an unchanged file re-gzips to the same bytes and
                git sees no change)
- meta.json     id, version, licence, the SHA-256 and size of the uncompressed
                .kmx, and the package it was taken from
- LICENSE.md    the keyboard's licence file, which names the copyright holder
                the MIT licence asks to be credited: the package's own, or,
                for the packages that carry none, the one beside the
                keyboard's source in keymanapp/keyboards (the API's sourcePath)

Nothing else from the package (fonts, help, images, the desktop on-screen
keyboard) is copied. The .kmx is not modified.

A keyboard that later disappears from keyman.com, or turns non-MIT, keeps its
folder: keeping a copy for exactly that case is the point. --prune removes the
folders of keyboards the app no longer bundles.

Usage:
    python3 scripts/mirror_keyman.py [--layouts DIR] [--force] [--prune] [--jobs N]

--layouts is WM Keyboard's app/src/main/assets/layouts, where each kmn_*.json
names its Keyman keyboard. It defaults to a WMKeyboard checkout beside this one.
"""

import argparse
import gzip
import hashlib
import io
import json
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "keyman"
DEFAULT_LAYOUTS = ROOT.parent / "WMKeyboard" / "app" / "src" / "main" / "assets" / "layouts"
API = "https://api.keyman.com/keyboard/"
DOWNLOADS = "https://downloads.keyman.com/keyboards/"
# The source repository, for the LICENSE.md a package does not carry itself.
SOURCE = "https://raw.githubusercontent.com/keymanapp/keyboards/master/"
UA = "wmkeyboard-data mirror_keyman.py (+https://github.com/wasi-master/wmkeyboard-data)"

# Same ceilings the app enforces, so nothing is mirrored that the app would refuse.
MAX_PACKAGE_BYTES = 32 * 1024 * 1024
MAX_KMX_BYTES = 16 * 1024 * 1024
KMX_MAGIC = b"KXTS"


def keyboard_ids(layouts: Path) -> list[str]:
    ids = set()
    for path in sorted(layouts.glob("kmn_*.wmlayout.json")):
        layout = json.loads(path.read_text(encoding="utf-8"))["layout"]
        kid = (layout.get("keyman") or {}).get("keyboardId")
        if kid:
            ids.add(kid)
    return sorted(ids)


def fetch(url: str, cap: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read(cap + 1)
    if len(data) > cap:
        raise ValueError(f"over {cap} bytes")
    return data


def pick(zf: zipfile.ZipFile, wanted: str) -> bytes | None:
    """An entry by base name, compared case-insensitively, as the app does."""
    for info in zf.infolist():
        if info.filename.rsplit("/", 1)[-1].lower() == wanted.lower():
            if info.file_size > MAX_KMX_BYTES:
                return None
            return zf.read(info)
    return None


def source_licence(meta: dict) -> bytes | None:
    path = (meta.get("sourcePath") or "").strip("/")
    if not path:
        return None
    try:
        return fetch(f"{SOURCE}{path}/LICENSE.md", 1024 * 1024)
    except urllib.error.HTTPError:
        return None


def mirror_one(kid: str, force: bool) -> tuple[str, str]:
    folder = OUT / kid
    try:
        meta = json.loads(fetch(API + kid, 1024 * 1024))
    except urllib.error.HTTPError as e:
        return kid, f"api {e.code}" + (" (kept old copy)" if folder.exists() else "")
    version = (meta.get("version") or "").strip()
    license_ = (meta.get("license") or "").strip().lower()
    package = (meta.get("packageFilename") or f"{kid}.kmp").rsplit("/", 1)[-1]
    if not version:
        return kid, "no version"
    if license_ != "mit":
        return kid, f"licence {license_ or 'unknown'}, not mirrored"

    meta_path = folder / "meta.json"
    if not force and meta_path.is_file():
        old = json.loads(meta_path.read_text(encoding="utf-8"))
        if old.get("version") == version and (folder / f"{kid}.kmx.gz").is_file():
            if not (folder / "LICENSE.md").is_file():
                licence_text = source_licence(meta)
                if licence_text is None:
                    return kid, "current (no LICENSE.md anywhere)"
                (folder / "LICENSE.md").write_bytes(licence_text)
            return kid, "current"

    url = f"{DOWNLOADS}{kid}/{version}/{package}"
    zf = zipfile.ZipFile(io.BytesIO(fetch(url, MAX_PACKAGE_BYTES)))
    kmx = pick(zf, f"{kid}.kmx")
    if kmx is None:
        return kid, "package has no .kmx"
    if not kmx.startswith(KMX_MAGIC):
        return kid, "not a .kmx (bad magic)"
    licence_text = pick(zf, "LICENSE.md") or source_licence(meta)

    folder.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, compresslevel=9, mtime=0) as gz:
        gz.write(kmx)
    (folder / f"{kid}.kmx.gz").write_bytes(buf.getvalue())
    if licence_text is not None:
        (folder / "LICENSE.md").write_bytes(licence_text)
    record = {
        "id": kid,
        "version": version,
        "license": license_,
        "sha256": hashlib.sha256(kmx).hexdigest(),
        "bytes": len(kmx),
        "source": url,
    }
    meta_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return kid, f"mirrored {version}" + ("" if licence_text is not None else " (no LICENSE.md anywhere)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--layouts", type=Path, default=DEFAULT_LAYOUTS)
    ap.add_argument("--force", action="store_true", help="re-download keyboards already at the current version")
    ap.add_argument("--prune", action="store_true", help="remove folders of keyboards the app no longer bundles")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()

    if not args.layouts.is_dir():
        print(f"no layouts at {args.layouts}; pass --layouts", file=sys.stderr)
        return 2
    ids = keyboard_ids(args.layouts)
    print(f"{len(ids)} keyboards bundled")

    def run(kid: str) -> tuple[str, str]:
        try:
            return mirror_one(kid, args.force)
        except Exception as e:  # one bad package must not stop the rest
            return kid, f"error: {e}"

    counts: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for kid, status in pool.map(run, ids):
            head = status.split(" (")[0].split(" ")[0]
            counts[head] = counts.get(head, 0) + 1
            if not status.startswith(("current", "mirrored")) or "LICENSE" in status:
                print(f"  {kid}: {status}")

    if args.prune:
        wanted = set(ids)
        for folder in sorted(OUT.iterdir()) if OUT.is_dir() else []:
            if folder.is_dir() and folder.name not in wanted:
                shutil.rmtree(folder)
                print(f"  pruned {folder.name}")

    print(", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    mirrored = sorted(p.parent.name for p in OUT.glob("*/meta.json"))
    raw = sum(json.loads((OUT / k / "meta.json").read_text())["bytes"] for k in mirrored)
    packed = sum((OUT / k / f"{k}.kmx.gz").stat().st_size for k in mirrored)
    print(f"{len(mirrored)} keyboards in keyman/: {raw / 1e6:.2f} MB of rules, {packed / 1e6:.2f} MB gzipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())

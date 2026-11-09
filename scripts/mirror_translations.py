#!/usr/bin/env python3
"""Mirrors the Firefox Translations (Bergamot) model files WM Keyboard pins
into this repository's `translations` release.

Mozilla serves the files from its Remote Settings attachment CDN, which
answers any user agent naming Chrome (Chrome itself and every browser built on
it) with HTTP 406. The app downloads them from Mozilla first and from this
release when that fails, and the offline build's "Get the files" sheet links
here, because GitHub serves every browser.

The list of files is the app's own pin table, `BergamotCatalog.kt` (written by
the app repository's `native/bergamot-jni/catalog.py`), so the mirror holds
exactly what released apps check against. Each file is published as it comes
from Mozilla (zstd-packed), named `<sha256>-<name>.zst` like the `natives` and
`models` releases: never replaced, a re-pinned file gets a new name, and files
the app no longer pins stay for the versions that still do.

Every download is checked against its pinned size and SHA-256 before it is
uploaded. Files already in the release are skipped, so a run that stopped
part-way picks up where it was.

    scripts/mirror_translations.py                        # catalogue from the app's main branch
    scripts/mirror_translations.py --catalog ../WMKeyboard/core/intelligence/src/main/java/com/wasimaster/wmkeyboard/core/translate/BergamotCatalog.kt
    scripts/mirror_translations.py --dry-run              # list what is missing

Needs Python 3.9+ and an authenticated `gh` CLI.
"""
import argparse
import concurrent.futures
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request

REPO = "wasi-master/wmkeyboard-data"
TAG = "translations"
CDN = "https://firefox-settings-attachments.cdn.mozilla.net/main-workspace/translations-models-v2/"
CATALOG_URL = ("https://raw.githubusercontent.com/wasi-master/wmkeyboard/main/core/intelligence/src/main/java/"
               "com/wasimaster/wmkeyboard/core/translate/BergamotCatalog.kt")
# Anything without "Chrome/" in it gets the file; curl's and the app's own both do.
USER_AGENT = "WMKeyboard translations mirror"
RELEASE_TITLE = "Firefox Translations models"
RELEASE_NOTES = ("Mozilla's Firefox Translations models (MPL-2.0), mirrored for WM Keyboard's on-device "
                 "translator. Named <sha256>-<name>.zst, zstd-packed as Mozilla publishes them. "
                 "See translations/README.md.")

FILE_LINE = re.compile(r'f\((\w+), "([^"]+)", "([^"]+)", (\d+), "([0-9a-f]{64})", (\d+), "([0-9a-f]{64})"\)')


def catalog_files(text):
    """(name, path, size, sha256) for every distinct downloaded file in the catalogue."""
    seen = {}
    for _kind, name, path, size, sha, _raw_size, _raw_sha in FILE_LINE.findall(text):
        seen.setdefault(sha, (name, path, int(size), sha))
    return list(seen.values())


def asset_name(name, sha):
    return f"{sha}-{name}.zst"


def gh(*args, capture=True):
    return subprocess.run(["gh", *args], check=True, text=True, capture_output=capture).stdout


def existing_assets():
    try:
        out = gh("release", "view", TAG, "-R", REPO, "--json", "assets")
    except subprocess.CalledProcessError:
        return None
    return {a["name"]: a["size"] for a in json.loads(out)["assets"]}


def fetch(url, target, size, sha):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    length = 0
    with urllib.request.urlopen(request, timeout=120) as response, open(target, "wb") as out:
        while chunk := response.read(1 << 20):
            digest.update(chunk)
            out.write(chunk)
            length += len(chunk)
    if length != size or digest.hexdigest() != sha:
        raise ValueError(f"{url}: got {length} bytes, sha256 {digest.hexdigest()}; pinned {size}, {sha}")


def mirror_one(entry, work):
    name, path, size, sha = entry
    folder = pathlib.Path(tempfile.mkdtemp(dir=work))
    target = folder / asset_name(name, sha)
    try:
        fetch(CDN + path, target, size, sha)
        gh("release", "upload", TAG, str(target), "-R", REPO)
    finally:
        target.unlink(missing_ok=True)
        folder.rmdir()
    return target.name


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalog", help="path to BergamotCatalog.kt (default: the app's main branch)")
    parser.add_argument("--dry-run", action="store_true", help="list the files to upload and stop")
    parser.add_argument("--jobs", type=int, default=3, help="files in flight at once (default 3)")
    args = parser.parse_args()

    if args.catalog:
        text = pathlib.Path(args.catalog).read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(CATALOG_URL, timeout=60) as response:
            text = response.read().decode("utf-8")
    files = catalog_files(text)
    if not files:
        sys.exit("no files found in the catalogue")

    have = existing_assets()
    if have is None and not args.dry_run:
        gh("release", "create", TAG, "-R", REPO, "--title", RELEASE_TITLE, "--notes", RELEASE_NOTES, "--latest=false")
        have = {}
    have = have or {}
    for name, size in have.items():
        pinned = next((f for f in files if asset_name(f[0], f[3]) == name), None)
        if pinned and pinned[2] != size:
            sys.exit(f"{name} is in the release at {size} bytes, pinned at {pinned[2]}: delete it by hand")
    missing = [f for f in files if asset_name(f[0], f[3]) not in have]
    total = sum(f[2] for f in missing)
    print(f"{len(files)} files pinned, {len(files) - len(missing)} mirrored, "
          f"{len(missing)} to upload ({total / 1e6:.0f} MB)", flush=True)
    if args.dry_run:
        for name, _path, size, sha in missing:
            print(f"  {asset_name(name, sha)}  {size}")
        return

    failed = []
    with tempfile.TemporaryDirectory(prefix="wmkb-translations-") as work, \
            concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {pool.submit(mirror_one, f, work): f for f in missing}
        for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
            entry = futures[future]
            try:
                print(f"[{done}/{len(missing)}] {future.result()}", flush=True)
            except Exception as e:  # noqa: BLE001 - report every file, then fail at the end
                failed.append(entry)
                print(f"[{done}/{len(missing)}] FAILED {asset_name(entry[0], entry[3])}: {e}", flush=True)
    if failed:
        sys.exit(f"{len(failed)} files failed; run again to retry them")


if __name__ == "__main__":
    main()

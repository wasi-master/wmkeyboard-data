# WM Keyboard — Data

Host-only data files for **WM Keyboard**, an Android keyboard app I'm currently
developing. These are the large source/dictionary files the app downloads on
demand (they are deliberately **not** bundled in the APK, to keep it small), so
this repository is pushed first, on its own, for testing the app's download
paths before the app itself goes public.

This is **not** the addon repository (themes, layouts, snippets, emoji packs).
That lives separately.

## Contents

| Folder | What | Source |
|---|---|---|
| [`data/`](data/) | Per-language word-frequency lists (160+ languages, `<lang>/<lang>_full.txt.gz`, plus optional offensive lists) | Various (see [`data/README.md`](data/README.md)) |
| [`cjk/`](cjk/) | Chinese Pinyin (`pinyin.tsv`), Japanese kana (`ja_kana.tsv`) and Chinese stroke (`stroke.tsv`) conversion tables, plus the build scripts under `cjk/tools/` — see [`cjk/README.md`](cjk/README.md) | CC-CEDICT, Mozc, BSD 2-Clause |

The `data/` word lists are **gzip-compressed** (`<lang>_full.txt.gz` and `<lang>_offensive.txt.gz`) so every
file stays under GitHub's 100 MB limit — `gunzip` to get the plain
`{word} {count}` text. The `cjk/` tables are stored uncompressed.

## Licensing & attribution

- **`data/`** — the frequency word lists and offensive word lists are sourced from various
  open-source projects including Hermit Dave's FrequencyWords, the Leipzig Corpora Collection,
  and others. Most lists are licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/),
  but some are under MIT, Public Domain, or CC BY-SA 3.0. See [`data/README.md`](data/README.md)
  for the per-language attribution table and full licensing details.
- **`cjk/`** — `pinyin.tsv` from [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict)
  (CC BY-SA 4.0); `ja_kana.tsv` from the [Google Mozc](https://github.com/google/mozc)
  OSS dictionary (BSD 3-Clause); `stroke.tsv` from
  [yefeijiang/Chinese-characters-code-table](https://github.com/yefeijiang/Chinese-characters-code-table)
  (BSD 2-Clause). Per-file formats, checksums, sources and rebuild steps are in
  [`cjk/README.md`](cjk/README.md); the build scripts are in [`cjk/tools/`](cjk/tools/).

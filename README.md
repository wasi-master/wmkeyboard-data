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
| [`data/`](data/) | Per-language word-frequency lists (`<lang>/<lang>_full.txt.gz`), next-word prediction pairs (`<lang>/<lang>_bigrams.txt.gz`, `<lang>/<lang>_trigrams.txt.gz`), AOSP LatinIME's curated lists for 23 languages, plus Canadian and Australian English respelled from them (`<lang>/<stem>_aosp.txt.gz`), optional offensive lists (`<lang_offensive.txt.gz`), emoji search dictionaries (`<lang>/<lang>_emoji.json.gz`) across 160+ languages, and for the 14 phonetic languages the phonetic index built over the word list (`<lang>/<lang>_phonetic_v<n>r<n>.wmpi.gz`, rebuilt by [`scripts/build_phonetic_indexes.sh`](scripts/build_phonetic_indexes.sh)), and the neural context models the suggestion strip reads the sentence with (`<lang>/<lang>_context.wmlm`, int8 word-level transformers under 5 MB, trained by the app repository's `tools/wmlm` on Tatoeba and Leipzig text; `bn/bn_rom_context.wmlm` reads English and Banglish in one) | Various (see [`data/README.md`](data/README.md)) |
| [`vocab/`](vocab/) | Vocabulary packs for the Vocabulary tool (`<lang>/<packId>.wmvocab.json.gz`) plus per-language translation sidecars, built from GRE word lists with Wiktionary and WordNet — see [`vocab/README.md`](vocab/README.md) | Wiktionary (kaikki.org), WordNet, CMUdict, FrequencyWords |
| [`dictionary/`](dictionary/) | Offline English dictionaries for the Dictionary tool (`<lang>/<id>.wmdict.gz`): Open English WordNet and a common-words cut of Wiktionary, sorted one line per headword so the app binary-searches the file on disk — see [`dictionary/README.md`](dictionary/README.md) | Open English WordNet 2024 (CC BY 4.0), Wiktionary via kaikki.org (CC BY-SA 4.0, GFDL) |
| [`cjk/`](cjk/) | Chinese Pinyin (`pinyin.tsv`), Japanese kana (`ja_kana.tsv`) and Chinese stroke (`stroke.tsv`) conversion tables, the OpenCC phrase table behind Traditional output (`s2t_phrases.txt`), plus the build scripts under `cjk/tools/` — see [`cjk/README.md`](cjk/README.md) | CC-CEDICT, Mozc, BSD 2-Clause, OpenCC (Apache-2.0) |
| [`keyman/`](keyman/) | Typing rules (`<id>/<id>.kmx.gz`) for the 812 Keyman keyboards WM Keyboard bundles that have any, read only when keyman.com can't serve them — see [`keyman/README.md`](keyman/README.md) | [Keyman](https://keyman.com/) packages, per-keyboard MIT |
| [`fonts/`](fonts/) | Fonts the app fetches for a layout whose letters no phone font has: Klingon pIqaD — see [`fonts/README.md`](fonts/README.md) | Klingon pIqaD HaSta, SIL OFL 1.1 |
| [`models/`](models/) | Small on-device networks the app fetches on demand, pinned by SHA-256: the sticker editor's background remover (`cutout/u2netp.tflite`, 4.6 MB) — see [`models/README.md`](models/README.md) | U²-Net (Qin et al.), Apache-2.0 |
| [`spell/`](spell/) | Spelling dictionaries the app downloads for its native spell checkers: the Finnish dictionary for Voikko (`voikko/voikko-fi-2.6-mor-standard.zip`), beside the signed source release it is built from — see [`spell/voikko/README.md`](spell/voikko/README.md) | voikko-fi 2.6 (GPL 2 or later) |
| [`natives/`](natives/) | Where the app's on-demand native libraries are published: assets of the `natives` release, named `<sha256>-<library>`, pinned by the app that downloads them — see [`natives/README.md`](natives/README.md) | The WM Keyboard app repository's own build |

The phonetic indexes are binary tables the app memory-maps instead of folding the whole word list on the phone at every start. Each file name carries the table format and fold version it was written by; a new version is published under a new name beside the old one, which stays for the app versions that still fetch it.

The `data/` word lists, word pairs, and emoji dictionaries are **gzip-compressed** (`<lang>_full.txt.gz`, `<lang>_bigrams.txt.gz`, `<lang>_offensive.txt.gz`, and `<lang>_emoji.json.gz`) so every
file stays under GitHub's 100 MB limit — `gunzip` to get the plain text/JSON data. The `cjk/` tables are stored uncompressed.


## Licensing & attribution

- **`data/`** — the frequency word lists, word-pair prediction lists, offensive word lists, and emoji dictionaries are sourced from various
  open-source projects including Hermit Dave's FrequencyWords, the Leipzig Corpora Collection,
  the [Tatoeba sentence corpus](https://tatoeba.org/) (CC BY 2.0 FR / CC0),
  [KDE kemoji](https://github.com/KDE/kemoji) / Unicode CLDR, and others. Frequency lists are licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), MIT, Public Domain, or CC BY-SA 3.0. The `_aosp` lists are from AOSP LatinIME, Copyright (C) The Android Open Source Project, under the [Apache License 2.0](data/LICENSE-AOSP-APACHE-2.0.txt). Emoji dictionaries are derived from Unicode CLDR annotations & Unicode Emoji Data under the [Unicode License Agreement (v3)](https://www.unicode.org/license.txt) / [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/). See [`data/README.md`](data/README.md)
  for the per-language attribution table and full licensing details.

- **`cjk/`** — `pinyin.tsv` from [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict)
  (CC BY-SA 4.0); `ja_kana.tsv` from the [Google Mozc](https://github.com/google/mozc)
  OSS dictionary (BSD 3-Clause); `stroke.tsv` from
  [yefeijiang/Chinese-characters-code-table](https://github.com/yefeijiang/Chinese-characters-code-table)
  (BSD 2-Clause); `s2t_phrases.txt` from [OpenCC](https://github.com/BYVoid/OpenCC)
  (Apache-2.0). Per-file formats, checksums, sources and rebuild steps are in
  [`cjk/README.md`](cjk/README.md); the build scripts are in [`cjk/tools/`](cjk/tools/).

- **`models/`** — `cutout/u2netp.tflite` is the U²-Net-P salient-object network by Xuebin Qin et al.
  ([xuebinqin/U-2-Net](https://github.com/xuebinqin/U-2-Net), Apache-2.0), converted to LiteRT from the ONNX
  export [rembg](https://github.com/danielgatis/rembg) publishes. Provenance and checksums are in
  [`models/README.md`](models/README.md).

- **`spell/`** — `voikko/voikko-fi-2.6-mor-standard.zip` is built from
  [voikko-fi](https://github.com/voikko/corevoikko/tree/master/voikko-fi) 2.6, Copyright 2006-2026 Hannu
  Väisänen, Harri Pitkänen, Teemu Likonen and others, under the GNU General Public License 2 or
  later (`spell/voikko/COPYING`). Its corresponding source, the signed `voikko-fi-2.6.tar.gz`, sits
  beside it; see [`spell/voikko/README.md`](spell/voikko/README.md).

- **`keyman/`** — each keyboard's `.kmx` is unmodified from its package on
  downloads.keyman.com and is MIT licensed by its own copyright holder, named in
  that folder's `LICENSE.md`. Only keyboards the Keyman API lists as MIT are
  mirrored. Keyman is a product of SIL Global; this project is not affiliated
  with it. See [`keyman/README.md`](keyman/README.md).

- **`dictionary/`** — `oewn.wmdict.gz` is [Open English WordNet 2024](https://en-word.net/)
  under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), cut to single words and re-encoded;
  `wiktionary.wmdict.gz` is English Wiktionary text via [kaikki.org](https://kaikki.org/) under
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) and the GFDL, cut to common single words
  and a few senses each. Both files name their source and licence in their header; see
  [`dictionary/README.md`](dictionary/README.md).

- **`vocab/`** — definitions, examples and translations are Wiktionary text via
  [kaikki.org](https://kaikki.org/) under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/),
  with WordNet 3.0 (WordNet License), the CMU Pronouncing Dictionary (BSD 2-Clause) and the repo's own
  OpenSubtitles frequency list (CC BY-SA 4.0) filling gaps. Every pack carries an `attribution` block; see
  [`vocab/README.md`](vocab/README.md).

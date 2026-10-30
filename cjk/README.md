# CJK conversion tables

Reading→character tables that make Chinese and Japanese **typeable** in WM
Keyboard: type a reading (Pinyin, kana or a stroke sequence), pick a candidate.
The app downloads these on demand — they are host-only, not bundled in the APK —
and verifies each against a pinned SHA-256 before use.

All three are plain UTF-8 TSV, one entry per line, sorted most-frequent first, so
a lookup can offer the commonest candidate first. Lines beginning with `#` are
header comments.

## Files

| File | Format | Rows / size | Source | License |
|---|---|---|---|---|
| `pinyin_v2.tsv` | `reading⇥word⇥freq` — toneless concatenated Pinyin (lowercase ASCII) → Simplified Hanzi | ~121.4k · 2.6 MB | [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict); frequencies from [`data/zh_cn`](../data/zh_cn) | CC BY-SA 4.0 |
| `pinyin_ngrams.tsv` | `word⇥count` and `word⇥word⇥count` — how often each pinyin-pack word occurs and which follows which, for ranking whole readings (`wbxh` → 我不喜欢). Not a reading table; fetched with `pinyin_v2.tsv` | 84.6k words, 700k pairs · 11 MB | [OpenSubtitles 2018](https://opus.nlpl.eu/OpenSubtitles/corpus/version/OpenSubtitles) via OPUS (the corpus behind `data/zh_cn`) and the [Leipzig Corpora Collection](https://wortschatz.uni-leipzig.de/en/download/Chinese) `zho-cn_web_2015_1M` + `zho_news_2020_300K`; split into words with `pinyin_v2.tsv`'s vocabulary | counts only; Leipzig CC BY 4.0 |
| `eval/pinyin_eval.tsv` | `pinyin⇥initials⇥hanzi⇥source` — held-out clauses for scoring the Pinyin decoder (full reading and initials-only). Not fetched by the app | 3,000 rows (1,500 Tatoeba, 1,500 Leipzig) · 186 KB | [Tatoeba](https://tatoeba.org) Mandarin (`cmn`) sentences and Leipzig `zho_wikipedia_2018_10K`, neither of which either pinyin pack was counted from | CC BY 2.0 FR / CC BY 4.0 |
| `pinyin_ngrams_v2.tsv` | Same format as `pinyin_ngrams.tsv`, which it contains unchanged, plus 500k word pairs and 8.1k words from the 万象 grammar model | 92.8k words, 1.2M pairs · 19 MB | `pinyin_ngrams.tsv` + [RIME-LMDG](https://github.com/amzxyz/RIME-LMDG) `wanxiang-lts-zh-hans.gram` | counts only; Leipzig and 万象 CC BY 4.0 |
| `pinyin.tsv` | The same, before the 2026-10 rescore. Frozen: app versions before it pin these exact bytes, so it is never rebuilt in place | ~120.6k · 2.4 MB | [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict) | CC BY-SA 4.0 |
| `ja_kana.tsv` | `reading⇥word⇥freq` — hiragana reading → kanji/kana surface | ~1.08M · 40 MB | [Google Mozc](https://github.com/google/mozc) OSS dictionary (`dictionary_oss`) | BSD 3-Clause |
| `stroke.tsv` | `strokeCode⇥hanzi⇥freq` — 1–5 stroke-class sequence → Simplified Hanzi | ~20.9k · 445 KB | [yefeijiang/Chinese-characters-code-table](https://github.com/yefeijiang/Chinese-characters-code-table); frequencies from CC-CEDICT ordering | BSD 2-Clause |
| `cangjie.tsv` | `code⇥hanzi⇥freq` — 1–5 Cangjie radical code (lowercase ASCII a–y) → Hanzi | ~29.2k · 351 KB | [Unicode Unihan Database](https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip) (`kCangjie` field) | Unicode License V3 |
| `jyutping.tsv` | `reading⇥word⇥freq` — toneless concatenated Jyutping (lowercase ASCII) → Traditional Hanzi | ~162.6k · 3.4 MB | [rime-cantonese](https://github.com/rime/rime-cantonese) & [CC-Canto](https://cantonese.org/); frequencies and generated standard-vocabulary rows from [`data/zh_tw`](../data/zh_tw) | CC BY 4.0 / CC BY-SA 3.0 / CC BY-SA 4.0 |
| `s2t_phrases.txt` | `simplified⇥traditional [alternatives…]` — Simplified word → its Traditional spelling, OpenCC text format, sorted by key; the first value is the conversion. Used by Traditional output, not for typing | ~49.8k · 1.0 MB | [OpenCC](https://github.com/BYVoid/OpenCC) 1.4.2: `STPhrases` plus `STPhrases_GeneratedFromRegionalPhrases` | Apache-2.0 |
| `jyutping_syllables.txt` | `syllable` — valid toneless Cantonese Jyutping syllable inventory (lowercase ASCII) | 701 rows · ~3.1 KB | [lshk-org/jyutping-table](https://github.com/lshk-org/jyutping-table) | CC BY 4.0 |
| `hanja.tsv` | `reading⇥word⇥freq` — Hangul word → Hanja, frequency being the row's rank under its reading | ~303k · 7.4 MB | [libhangul](https://github.com/libhangul/libhangul) `data/hanja/hanja.txt`, via `tools/build_hanja.py` | BSD-3-Clause (`LICENSE_hanja.txt`) |
| `kiwi/kiwi-model-0.24.1.zip` | Kiwi's base model, the release's `kiwi_model_v0.24.1_base.tgz` repacked flat as a zip, for Korean spacing correction | 9 files · 88 MB | [bab2min/Kiwi](https://github.com/bab2min/Kiwi) | Apache-2.0 (`kiwi/LICENSE`, `kiwi/NOTICE`) |
| `louis/louis-tables-3.39.0.zip` | The translation tables of [liblouis 3.39.0](https://github.com/liblouis/liblouis), every table file in the release flat as a zip, for contracted braille. Not a reading table | 3.6 MB | LGPL-2.1-or-later, `LICENSE_louis.txt` |
| `tashkeel/catt-eo-v2.int8.onnx` | [CATT](https://github.com/abjadai/catt)'s encoder-only checkpoint `best_eo_mlm_ns_epoch_193.pt` (release v2), exported to one ONNX graph and quantized to int8, for adding tashkeel. Not a reading table | 21 MB | Apache-2.0, `LICENSE_catt.txt` |
| `hunspell/hunspell-tr-1.1.1.zip` | [hunspell-tr](https://github.com/tdd-ai/hunspell-tr)'s `tr_TR.aff` and `tr_TR.dic`, unchanged, for checking Turkish. Not a reading table | 14.5 MB | MPL-2.0, `LICENSE_hunspell_tr.txt` |
| `furigana/ja_furigana.tsv` | `word⇥reading⇥freq` sorted by bytes: `ja_kana.tsv`'s words holding kanji, each with its commonest reading, for adding furigana. Not a conversion table | ~656k · 24 MB | [Google Mozc](https://github.com/google/mozc), BSD-3-Clause, `LICENSE_mozc.txt` |
| `yo/ru_yo_safe.txt` | [eyo-kernel](https://github.com/e2yo/eyo-kernel)'s `dictionary/safe.txt`, unchanged, for restoring ё in Russian. Not a reading table | 14.6k lines · 865 KB | MIT, `LICENSE_eyo.txt` |
| `zinnia/*.model` | zinnia handwriting models, not reading tables: Japanese, Simplified and Traditional Chinese. See [`zinnia/README.md`](zinnia/README.md) | 26–52 MB each | [Tegaki](https://github.com/tegaki/tegaki) 0.3, trained on Tomoe | LGPL 2.1 |

Stroke classes: `1`=一 (héng), `2`=丨 (shù), `3`=丿 (piě), `4`=丶 (diǎn), `5`=乙 (zhé).

### Checksums

The app pins these (see `CjkDictCatalog.kt`); recompute with `shasum -a 256 <file>` after a rebuild.

A pinned file is never overwritten: every app version already installed checks
it against the checksum it shipped with, so changed bytes under the same name
break the download for all of them. A rebuild that changes a pack goes out
under a new name (`pinyin.tsv` → `pinyin_v2.tsv`), the old file stays, and the
app's catalog moves to the new name in the same release.

```
pinyin_v2.tsv 2586937  0c572b5f5699378beb0eab5ec81cf79bb277e0f100d3c944d8969b7445b1a0c9
pinyin_ngrams.tsv 11036820  30c0c614ac0576379407b0e519615653a4be5939590a795dae7074ce960e30bf
pinyin_ngrams_v2.tsv 19166702  542fde43028bfead594e4f30f317bb2f8d6f581454a4a802c626bcf0dc93f918
pinyin.tsv    2489699  8baab4c758499272e36dba4bda4253317a4f93bb88bcf386ea86196c50d73715
ja_kana.tsv  41531397  189214b81968c857d7cb020c52fc087ee44918ab28534194f79ea66f45c17a70
stroke.tsv     445573  87d790c976b28e54107aef1af4ea3cea6e608500de0bcb3c01af7d8f1f8c52e8
cangjie.tsv    351337  77a5a4c054019e3a3ea875e86a37cb08b71ce29392b6680208bb0c5749feb25d
jyutping.tsv  3416241  cc0666179df615846328ed1e86b621919553d8ff30905f30d0b6ff45315bcfba
s2t_phrases.txt 1021797  a8c1ff12191edfc8dc435d23736e2bf097357650ea195f51767d397c5b70908c
```

## Rebuilding

The `tools/` scripts fetch each upstream source and regenerate its table (no
arguments needed; each downloads what it needs):

```bash
python3 tools/build_cedict_pinyin.py   # → pinyin_v2.tsv (from CC-CEDICT; reads data/zh_cn for frequencies)
python3 tools/build_mozc_ja_kana.py    # → ja_kana.tsv  (from Mozc)
python3 tools/build_stroke_dict.py     # → stroke.tsv   (needs pinyin.tsv for freq)
python3 tools/build_cangjie_dict.py    # → cangjie.tsv  (from Unihan)
python3 tools/build_jyutping_dict.py   # → jyutping.tsv (from rime-cantonese & CC-Canto; reads data/zh_tw for frequencies)
```

`pinyin_ngrams.tsv` needs its text downloaded first — neither source is
fetched by the script, since the files are large (170 MB and 550 MB packed):

```bash
curl -O https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/mono/zh_cn.txt.gz
curl -O https://downloads.wortschatz-leipzig.de/corpora/zho-cn_web_2015_1M.tar.gz   # then untar
curl -O https://downloads.wortschatz-leipzig.de/corpora/zho_news_2020_300K.tar.gz   # then untar
python3 tools/build_pinyin_ngrams.py --corpus zh_cn.txt.gz \
    --corpus zho-cn_web_2015_1M/zho-cn_web_2015_1M-sentences.txt \
    --corpus zho_news_2020_300K/zho_news_2020_300K-sentences.txt   # → pinyin_ngrams.tsv, ~6 min on 8 cores
```

It splits each run of Hanzi into words with `pinyin_v2.tsv`'s own vocabulary,
so rebuild it after a new pinyin pack (and publish it under a new name too).

`pinyin_ngrams_v2.tsv` adds the [万象 grammar model](https://github.com/amzxyz/RIME-LMDG)
(a RIME octagram `.gram` file) to `pinyin_ngrams.tsv`. A small C program lists
the model's 61M keys; the Python tool splits each with `pinyin_v2.tsv`'s
vocabulary, keeps the keys that are one word or two, and rescales their values
onto the v1 counts per class of word lengths:

```bash
curl -LO https://github.com/amzxyz/RIME-LMDG/releases/download/LTS/wanxiang-lts-zh-hans.gram   # 398 MB
clang -O2 -o /tmp/dump_rime_gram tools/dump_rime_gram.c -lpthread
mkdir -p /tmp/gram && /tmp/dump_rime_gram wanxiang-lts-zh-hans.gram /tmp/gram/part 8 && cat /tmp/gram/part.* > /tmp/gram.tsv   # 2.6 GB, ~20 s
python3 tools/build_pinyin_ngrams_v2.py --gram-tsv /tmp/gram.tsv --work /tmp/gram-work   # → pinyin_ngrams_v2.tsv, ~10 min on 8 cores
```

The model's values are not counts: they grow ~4.2 (×65) per key character,
keys of five or more characters mostly sit at its ceiling, and within a class
they agree with v1 only loosely (Spearman ≈ 0.3 for pairs, 0.76 for
two-character words). Only classes that agree at all are used — pairs of one-
and two-character words, two- and three-character words — and the tool prints
each class's offset and correlation. The release tag is `LTS` and moves; the
build above used sha256 `d26da3d6…0adc12bd0` (see `LICENSE_wanxiang.txt`).

`eval/pinyin_eval.tsv` is a test set, not a pack: each row is a Simplified
clause, the toneless reading that should decode to it, its initials (zh/ch/sh
as z/c/s) and where it came from. Its text is held out on purpose, so a score
on it says how well the decoder ranks, not how much of its own training text it
remembers. Clauses are 2–14 Hanzi, cut at punctuation, kept only when
`pinyin_v2.tsv`'s vocabulary covers every character, read with each word's
commonest reading; sentences with any Traditional-only character (by the app's
OpenCC `s2t.txt`) are dropped. Sampling is seeded (580), so a rebuild from the
same downloads is byte-identical:

```bash
curl -O https://downloads.tatoeba.org/exports/per_language/cmn/cmn_sentences.tsv.bz2
curl -O https://downloads.wortschatz-leipzig.de/corpora/zho_wikipedia_2018_10K.tar.gz   # then untar
python3 tools/build_pinyin_eval.py --tatoeba cmn_sentences.tsv.bz2 \
    --leipzig zho_wikipedia_2018_10K/zho_wikipedia_2018_10K-sentences.txt   # → eval/pinyin_eval.tsv
```

It reads `s2t.txt` and `pinyin_syllables.txt` from the app checkout beside this
one (`--app` or `$WMKB_APP` to point elsewhere). Tatoeba's export grows daily,
so a later download samples different sentences.

`s2t_phrases.txt` is built from the app repository instead, by
`scripts/update-opencc.py`, because the same run refreshes the small OpenCC
tables the APK bundles next to it. It writes here when this checkout sits
beside the app's (or at `$WMKB_DATA`) and prints the size and checksum to pin.

`build_cedict_pinyin.py` reads `data/zh_cn/zh_cn_full.txt.gz` the same way,
since CC-CEDICT has no frequencies either. Single characters are scored per
reading from the corpus words that contain them, so 议 and 际 — rare alone,
everywhere inside words — rank where they belong. Before 2026-10-12 the script
reseeded from its own previous output and otherwise ranked by line position in
CC-CEDICT, which left 齐 113th under `qi` (issue #633); that output is the
frozen `pinyin.tsv`. `stroke.tsv` still carries frequencies copied from it
until it is rebuilt.

`build_jyutping_dict.py` also needs a local file as well as
its downloads: neither Cantonese source ships frequencies, so it reads
`data/zh_tw/zh_tw_full.txt.gz` for them. Pass `--corpus` to point it elsewhere,
or `--no-coverage` to build from the Cantonese sources alone — the result is
usable but candidate order is close to arbitrary, which is what the pack looked
like before 2026-07-27.

## Attribution

- **`pinyin_v2.tsv`, `pinyin.tsv`**: CC-CEDICT data is redistributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) with attribution to the CC-CEDICT project. Frequencies derive from the `zh_cn` frequency list in [`data/`](../data) ([hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords), OpenSubtitles 2018, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).
- **`ja_kana.tsv`**: Google Mozc dictionary data (`dictionary_oss`) is redistributed under the [BSD 3-Clause License](LICENSE_mozc.txt).
- **`stroke.tsv`**: Derived from [yefeijiang/Chinese-characters-code-table](https://github.com/yefeijiang/Chinese-characters-code-table) by FeiJiang Ye, licensed under the [BSD 2-Clause License](LICENSE_stroke.txt).
- **`cangjie.tsv`**: Derived from the [Unicode Unihan Database](https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip), licensed under the [Unicode License V3](LICENSE_cangjie.txt).
- **`jyutping.tsv`**: Derived from [rime-cantonese](https://github.com/rime/rime-cantonese) (by CanCLID, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)) and [CC-Canto](https://cantonese.org/) (by Pleco Inc., licensed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)). See [LICENSE_jyutping.txt](LICENSE_jyutping.txt). Frequencies, and the generated rows covering standard vocabulary neither Cantonese source lists, additionally derive from the `zh_tw` frequency list in [`data/`](../data) ([hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords), OpenSubtitles 2018, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).
- **`pinyin_ngrams_v2.tsv`**: Everything in `pinyin_ngrams.tsv` (above), plus counts derived from RIME-LMDG / 万象语法模型 by amzxyz, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), https://github.com/amzxyz/RIME-LMDG. See [LICENSE_wanxiang.txt](LICENSE_wanxiang.txt).
- **`eval/pinyin_eval.tsv`**: Sentences from [Tatoeba](https://tatoeba.org) (Mandarin, `cmn`), by Tatoeba contributors, licensed under [CC BY 2.0 FR](https://creativecommons.org/licenses/by/2.0/fr/), and from the [Leipzig Corpora Collection](https://wortschatz.uni-leipzig.de/en/download/Chinese) `zho_wikipedia_2018_10K` (D. Goldhahn, T. Eckart & U. Quasthoff: Building Large Monolingual Dictionaries at the Leipzig Corpora Collection: From 100 to 200 Languages. LREC 2012), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Cut into clauses and annotated with readings from `pinyin_v2.tsv`.
- **`s2t_phrases.txt`**: Copied from the dictionaries of [OpenCC](https://github.com/BYVoid/OpenCC) (Open Chinese Convert) 1.4.2, Copyright Carbo Kuo and OpenCC contributors, licensed under the [Apache License 2.0](LICENSE_opencc.txt). The rows from `STPhrases_GeneratedFromRegionalPhrases` are regenerated the way OpenCC's build does it, from the keys of its `TWPhrases` and `HKPhrases`.
- **`jyutping_syllables.txt`**: Derived from [lshk-org/jyutping-table](https://github.com/lshk-org/jyutping-table) by the Linguistic Society of Hong Kong (LSHK), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).




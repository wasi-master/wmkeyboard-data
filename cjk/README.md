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
| `pinyin.tsv` | `reading⇥word⇥freq` — toneless concatenated Pinyin (lowercase ASCII) → Simplified Hanzi | ~120k · 2.4 MB | [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict) | CC BY-SA 4.0 |
| `ja_kana.tsv` | `reading⇥word⇥freq` — hiragana reading → kanji/kana surface | ~1.08M · 40 MB | [Google Mozc](https://github.com/google/mozc) OSS dictionary (`dictionary_oss`) | BSD 3-Clause |
| `stroke.tsv` | `strokeCode⇥hanzi⇥freq` — 1–5 stroke-class sequence → Simplified Hanzi | ~20.9k · 445 KB | [yefeijiang/Chinese-characters-code-table](https://github.com/yefeijiang/Chinese-characters-code-table); frequencies from CC-CEDICT ordering | BSD 2-Clause |
| `cangjie.tsv` | `code⇥hanzi⇥freq` — 1–5 Cangjie radical code (lowercase ASCII a–y) → Hanzi | ~29.2k · 351 KB | [Unicode Unihan Database](https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip) (`kCangjie` field) | Unicode License V3 |
| `jyutping.tsv` | `reading⇥word⇥freq` — toneless concatenated Jyutping (lowercase ASCII) → Traditional Hanzi | ~144.1k · 3.0 MB | [rime-cantonese](https://github.com/rime/rime-cantonese) & [CC-Canto](https://cantonese.org/) | CC BY 4.0 / CC BY-SA 3.0 |
| `jyutping_syllables.txt` | `syllable` — valid toneless Cantonese Jyutping syllable inventory (lowercase ASCII) | 701 rows · ~3.1 KB | [lshk-org/jyutping-table](https://github.com/lshk-org/jyutping-table) | CC BY 4.0 |

Stroke classes: `1`=一 (héng), `2`=丨 (shù), `3`=丿 (piě), `4`=丶 (diǎn), `5`=乙 (zhé).

### Checksums

The app pins these (see `CjkDictCatalog.kt`); recompute with `shasum -a 256 <file>` after a rebuild.

```
pinyin.tsv    2489699  8baab4c758499272e36dba4bda4253317a4f93bb88bcf386ea86196c50d73715
ja_kana.tsv  41531397  189214b81968c857d7cb020c52fc087ee44918ab28534194f79ea66f45c17a70
stroke.tsv     445573  87d790c976b28e54107aef1af4ea3cea6e608500de0bcb3c01af7d8f1f8c52e8
cangjie.tsv    351337  77a5a4c054019e3a3ea875e86a37cb08b71ce29392b6680208bb0c5749feb25d
jyutping.tsv  2993536  955764a4bbff61b62de9fb55d4f1fd78c25e995b00ee2afdfdc0a005ae06ea3c
```

## Rebuilding

The `tools/` scripts fetch each upstream source and regenerate its table (no
arguments needed; each downloads what it needs):

```bash
python3 tools/build_cedict_pinyin.py   # → pinyin.tsv   (from CC-CEDICT)
python3 tools/build_mozc_ja_kana.py    # → ja_kana.tsv  (from Mozc)
python3 tools/build_stroke_dict.py     # → stroke.tsv   (needs pinyin.tsv for freq)
python3 tools/build_cangjie_dict.py    # → cangjie.tsv  (from Unihan)
python3 tools/build_jyutping_dict.py   # → jyutping.tsv (from rime-cantonese & CC-Canto)
```

## Attribution

- **`pinyin.tsv`**: CC-CEDICT data is redistributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) with attribution to the CC-CEDICT project.
- **`ja_kana.tsv`**: Google Mozc dictionary data (`dictionary_oss`) is redistributed under the [BSD 3-Clause License](LICENSE_mozc.txt).
- **`stroke.tsv`**: Derived from [yefeijiang/Chinese-characters-code-table](https://github.com/yefeijiang/Chinese-characters-code-table) by FeiJiang Ye, licensed under the [BSD 2-Clause License](LICENSE_stroke.txt).
- **`cangjie.tsv`**: Derived from the [Unicode Unihan Database](https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip), licensed under the [Unicode License V3](LICENSE_cangjie.txt).
- **`jyutping.tsv`**: Derived from [rime-cantonese](https://github.com/rime/rime-cantonese) (by CanCLID, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)) and [CC-Canto](https://cantonese.org/) (by Pleco Inc., licensed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)). See [LICENSE_jyutping.txt](LICENSE_jyutping.txt).
- **`jyutping_syllables.txt`**: Derived from [lshk-org/jyutping-table](https://github.com/lshk-org/jyutping-table) by the Linguistic Society of Hong Kong (LSHK), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).




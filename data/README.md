# Frequency Word Lists

A collection of frequency word lists for 215+ languages.

## Format

Dictionary files are stored as gzip-compressed text files:

```
<lang>/<lang>_full.txt.gz
```

23 languages also have AOSP LatinIME's curated list beside the counted one,
in the same `word frequency` form but with AOSP's own 0..255 log-scale
frequency (see [AOSP word lists](#aosp-word-lists)):

```
<lang>/<stem>_aosp.txt.gz
```

Some languages also include an optional offensive word list:

```
<lang>/<lang>_offensive.txt.gz
```

Emoji dictionaries are stored as gzip-compressed JSON files:

```
<lang>/<lang>_emoji.json.gz
```

After decompression, each frequency list contains one entry per line:

```text
word frequency
```

After decompression, each emoji dictionary contains a JSON array of objects:

```json
[
  {
    "emoji": "😀",
    "name": "grinning face",
    "keywords": ["cheerful", "cheery", "face", "grin", "grinning", "happy", "laugh", "nice", "smile", "smiling", "teeth"],
    "category": "Smileys & Emotion"
  }
]
```



## Sources

### Word lists

This repository redistributes and packages data from the following open-source projects:

| Source | Languages |
|--------|-----------|
| [hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords) (OpenSubtitles 2018) | All languages except those listed below. |
| [rspeer/wordfreq](https://github.com/rspeer/wordfreq) | `bn`, `ca`, `hi`, `ja`, `ta`, `uk` |
| [urduhack/urdu-words](https://github.com/urduhack/urdu-words) | `ur` |
| [ebukva/bs_BA](https://github.com/ebukva/bs_BA) (Hunspell, expanded by [`scripts/import_bs_hunspell.py`](../scripts/import_bs_hunspell.py)) over the OpenSubtitles counts | `bs` |
| [kasunw22/sinhala-para-dict](https://github.com/kasunw22/sinhala-para-dict) | `si` |
| [vigneshwaran-chandrasekaran/tamil-language-words-list](https://github.com/vigneshwaran-chandrasekaran/tamil-language-words-list) | `ta` |
| [tahmid02016/bangla-wordlist](https://github.com/tahmid02016/bangla-wordlist) | `bn` (the words; `bn_full_v2`'s counts are from the Leipzig corpora, see [Bangla word frequencies](#bangla-word-frequencies)) |
| [Leipzig Corpora Collection](https://wortschatz.uni-leipzig.de/de) | `aa`, `af`, `ak`, `am`, `an`, `as`, `az`, `ba`, `be`, `bm`, `bo`, `br`, `ce`, `co`, `cv`, `cy`, `div`, `ee`, `eo`, `eu`, `ff`, `fo`, `fy`, `gl`, `gn`, `gu`, `gv`, `ha`, `hi`, `ht`, `hy`, `ia`, `ie`, `ig`, `ina`, `io`, `jv`, `ka`, `kg`, `ki`, `kk`, `kl`, `km`, `kn`, `koi`, `kok`, `ky`, `lg`, `li`, `ln`, `lo`, `lv`, `mn`, `mr`, `ms`, `mt`, `my`, `myv`, `nd`, `ne`, `nn`, `nr`, `nv`, `ny`, `oc`, `om`, `os`, `pa`, `ps`, `qu`, `rm`, `sco`, `se`, `sh`, `sna`, `so`, `ssw`, `st`, `sun`, `sw`, `te`, `tg`, `ti`, `tk`, `tl`, `tn`, `ts`, `tt`, `ug`, `uz`, `ve`, `vi`, `vo`, `wa`, `wo`, `xh`, `yi`, `yo`, `za`, `zu` |
| [Tatoeba sentence corpus](https://tatoeba.org/), counted by [`scripts/import_tatoeba_words.py`](../scripts/import_tatoeba_words.py) | `arq`, `ber`, `bzt`, `ckt`, `dar`, `enm`, `fkv`, `gcf`, `gos`, `grc`, `hbo`, `hoc` (`hoc_latn`), `hrx`, `isv` (`isv_latn`), `kha`, `kzj`, `mus`, `nnb`, `nus`, `orv`, `ota` (`ota_full` and `ota_latn`), `pau`, `prg`, `rif`, `rn`, `rom`, `sdh`, `swc`, `swg`, `thv`, `ttq` |
| [eBible corpus](https://github.com/BibleNLP/ebible) and [Glot500](https://huggingface.co/datasets/cis-lmu/Glot500), counted by [`scripts/import_corpus_words.py`](../scripts/import_corpus_words.py) | `acm`, `afb`, `ajp`, `aln`, `apc`, `arn`, `bba`, `bem`, `dgr`, `emp`, `kaa` (`kaa_latn`), `kac`, `kam`, `kek`, `kjh`, `knf`, `nch`, `ngu`, `nop`, `tgo`, `umb`, `uz` (`uz_cyrl`) |
| Transliterated from the language's list in its other script by [`scripts/transliterate_wordlist.py`](../scripts/transliterate_wordlist.py) | `be_latn`, `bs_cyrl`, `kk_latn`, `sr_latn`, `zgh_latn` |
| [Wikimedia data dumps](https://dumps.wikimedia.org/) | `ab`, `ace`, `ady`, `alt`, `ami`, `ang`, `ann`, `anp`, `arc`, `arz`, `atj`, `av`, `avk`, `awa`, `ay`, `azb`, `bar`, `bbc`, `bdr`, `be-tarask`, `bew`, `bh`, `bi`, `bik`, `bjn`, `blk`, `bol`, `bpy`, `btm`, `bxr`, `cbk`, `cbk-zam`, `cdo`, `ch`, `chr`, `chy`, `cr`, `crh`, `csb`, `cu`, `dag`, `dga`, `din`, `diq`, `dsb`, `dtp`, `dty`, `dv`, `dz`, `eml`, `ext`, `fat`, `fj`, `fon`, `frp`, `frr`, `fur`, `gag`, `gan`, `gcr`, `gd`, `glk`, `gom`, `gor`, `got`, `gpe`, `guc`, `gur`, `guw`, `hak`, `haw`, `hif`, `hsb`, `hyw`, `iba`, `igl`, `ik`, `inh`, `isv`, `iu`, `jam`, `kaa`, `kai`, `kaj`, `kbd`, `kbp`, `kcg`, `kge`, `knc`, `koi`, `krc`, `ksh`, `ku`, `kus`, `kv`, `kw`, `lad`, `lbe`, `lez`, `lfn`, `lij`, `lld`, `lmo`, `loz`, `ltg`, `lub`, `lzh`, `mag`, `map-bms`, `mdf`, `mg`, `mhr`, `mi`, `mni`, `mnw`, `mos`, `mrj`, `myv`, `mzn`, `nah`, `nan`, `nds`, `nds-nl`, `new`, `nia`, `nov`, `nqo`, `nrm`, `nso`, `nup`, `olo`, `or`, `pag`, `pam`, `pap`, `pcd`, `pcm`, `pdc`, `pfl`, `pi`, `pnb`, `pnt`, `ppl`, `pwn`, `rif`, `rki`, `rmy`, `roa-tara`, `rsk`, `rue`, `rup`, `rw`, `sah`, `sat`, `scn`, `sg`, `sgs`, `shi`, `shn`, `skr`, `sm`, `smn`, `sn`, `srn`, `ss`, `stq`, `su`, `syl`, `szl`, `szy`, `tay`, `tdd`, `tet`, `tig`, `tly`, `to`, `tpi`, `trv`, `tum`, `tw`, `ty`, `tyv`, `udm`, `vec`, `vep`, `vls`, `vro`, `wuu`, `xal`, `xmf`, `yue`, `zea`, `zgh`, `zh` |
| [Official Lojban Dictionary](https://www.lojban.org) | `jbo` |
| [Klingon Dictionary](http://klingonska.org/dict/dict.zdb) | `tlh` |
| [Ardalambion Quenya Wordlist](https://ardalambion.net/quen-eng.htm) | `qya` |
| [lipu Linku Toki Pona Dictionary](https://linku.la) | `tok` |
| [motaitalic/devanagari-documentation](https://github.com/motaitalic/devanagari-documentation) | `bho`, `brx`, `doi`, `ks`, `mai`, `raj` |
| [Zaanthai/balochi-dictionary](https://huggingface.co/datasets/Zaanthai/balochi-dictionary) & [mainkilora/Balochi-Multilingual-dataset](https://huggingface.co/datasets/mainkilora/Balochi-Multilingual-dataset) | `bgn` |
| [Unicode CLDR](https://github.com/unicode-org/cldr) | `blo` |
| [amlan107/chakma-nmt-complete-dataset](https://huggingface.co/datasets/amlan107/chakma-nmt-complete-dataset) & [dipongkar01/chakma-language](https://huggingface.co/datasets/dipongkar01/chakma-language) | `ccp` |
| [Tagalog Wikipedia Dump & Hermit Dave FrequencyWords](https://dumps.wikimedia.org/tlwiki/) | `fil` |
| [eBible Corpus](https://huggingface.co/datasets/DavidCBaines/ebible_corpus) & [Glot500](https://huggingface.co/datasets/cis-lmu/Glot500) | `quc` |
| [eBible Corpus](https://huggingface.co/datasets/DavidCBaines/ebible_corpus), [arndri/rohingya-tweet-id](https://huggingface.co/datasets/arndri/rohingya-tweet-id) & [freococo/rohingya_asr_audio](https://huggingface.co/datasets/freococo/rohingya_asr_audio) | `rhg` |
| [Glot500 Corpus](https://huggingface.co/datasets/cis-lmu/Glot500) | `ace`, `ak`, `an`, `arz`, `ast`, `ban`, `bar`, `bik`, `bjn`, `bxr`, `ceb`, `crh`, `cv`, `diq`, `dsb`, `dv`, `frr`, `gag`, `hil`, `hsb`, `ilo`, `jbo`, `kaa`, `kg`, `ksh`, `ln`, `mhr`, `min`, `myv`, `nap`, `nr`, `ny`, `pag`, `pam`, `pms`, `quc`, `sah`, `se`, `sg`, `stq`, `tlh`, `tok`, `udm`, `vec`, `vro`, `wa`, `war`, `xal` |
| [ETCBC Peshitta Syriac Corpus](https://github.com/ETCBC/peshitta) | `syr` |
| [Cantonese Wikipedia Dump (`zh_yuewiki`)](https://dumps.wikimedia.org/zh_yuewiki/) & [OpenCC](https://github.com/BYVoid/OpenCC) | `yue`, `yue_Hans` |
| [KDE/kemoji](https://github.com/KDE/kemoji) (Unicode CLDR & Unicode Emoji Data) | Emoji dictionaries (`<lang>_emoji.json.gz`) for 141 languages, plus Banglish (`bn_rom`) transliterated from the Bengali one |



Some datasets have been reformatted, compressed, or reorganized for consistency. Original attribution and licensing remain unchanged.


### AOSP word lists

`<stem>_aosp.txt.gz` files are the word lists of Android's own keyboard, AOSP
LatinIME ([`dictionaries/*_wordlist.combined.gz`](https://android.googlesource.com/platform/packages/inputmethods/LatinIME/+/refs/heads/main/dictionaries/)),
Copyright (C) The Android Open Source Project, licensed under the
[Apache License 2.0](LICENSE-AOSP-APACHE-2.0.txt). They are generated by
[`scripts/import_aosp.py`](../scripts/import_aosp.py), which states the changes
made: `not_a_word` records and shortcut records are removed, only the word and
its `f` value are kept, and lines are sorted by frequency.

| File | AOSP list |
|---|---|
| `cs`, `da`, `de`, `el`, `es`, `fi`, `fr`, `hr`, `it`, `lt`, `lv`, `nb`, `nl`, `pl`, `ro`, `ru`, `sl`, `sr`, `sv`, `tr` | same code |
| `en/en_aosp` | `en_US` |
| `en/en_gb_aosp` | `en_GB` |
| `en/en_ca_aosp` | `en_US`, respelled Canadian (below) |
| `en/en_au_aosp` | LineageOS's `en_AU`, respelled Australian (below) |
| `he/he_aosp` | `iw` |
| `pt/pt_aosp` | `pt_PT` |
| `pt_br/pt_br_aosp` | `pt_BR` |

AOSP has no Canadian or Australian list, so
[`scripts/import_aosp_regional_en.py`](../scripts/import_aosp_regional_en.py)
makes them from the nearest one, keeping its frequencies and changing only the
spelling, with the regional spelling codes of the
[English Speller Database](https://github.com/en-wl/wordlist) (ESDB, formerly
SCOWL; Copyright 2000-2026 Kevin Atkinson, Australian data Copyright 2016
Benjamin Titze, permissive notice in [`NOTICE`](../NOTICE)):

- `en/en_ca_aosp` is AOSP's `en_US` with American spellings Canada does not use
  swapped for Canadian ones (`center` to `centre`, `traveled` to `travelled`;
  about 730 words). `-ize` stays, as in Canada.
- `en/en_au_aosp` is the `en_AU` list of
  [LineageOS LatinIME](https://github.com/LineageOS/android_packages_inputmethods_LatinIME/tree/lineage-21.0/dictionaries)
  (Apache 2.0; LineageOS made it from AOSP's `en_GB` in 2015), with a dozen
  British spellings Australia does not use swapped (`programme` to `program`).

The script's docstring has the exact rule and the few words it leaves alone.

### Desktop Avro dictionary

`bn/bn_avro_dictionary.txt.gz` is the word list of desktop Avro Phonetic,
ibus-avro's `avrodict.js` ([omicronlab/ibus-avro](https://github.com/omicronlab/ibus-avro)),
Copyright (C) OmicronLab, licensed under the
[Mozilla Public License 1.1](LICENSE-AVRO-MPL-1.1.txt). WM Keyboard downloads it
for its Avro candidate list. Only the encoding changed: one word per line, each
of Avro's tables opened by an `@name` line, and the source's eleven `\u0200c`
typos written as the `\u200c` (ZWNJ) they were meant to be.

### Khipro glide spellings

`bn/bn_khipro_glide.txt.gz` holds the Khipro spellings of every word of
`bn/bn_full.txt.gz`, one word per line followed by its spellings, tab
separated. WM Keyboard reads it to glide on its Khipro layout instead of
working the spellings out on the phone, which takes minutes of every core.
It is generated, not edited: `scripts/build_bn_khipro_glide.sh` compiles WM
Keyboard's own Khipro interpreter (running the Khipro team's MIT-licensed
`bn-khipro.mim`) backwards over the list. Rerun it whenever `bn_full.txt.gz`
changes.

### Khipro layout rules

`bn/khipro/` is the Khipro team's current layout definition, which WM Keyboard
installs over the copy its engine was built with, so a layout fix reaches
phones without an app release: four m17n specs (`bn-khipro.mim` and
`bn-khipro-dark.mim` for hardware keyboards, the `-touchscreen` ones for the
keys on screen), the conformance table each spec's repository keeps beside it,
and `bn_khipro_specs.json`, which names the set's revision and every file's
size and SHA-256. The specs are unchanged copies from
[rank-coder/khipro-m17n](https://github.com/rank-coder/khipro-m17n),
[KhiproTeam/khipro-mim-touchscreen](https://github.com/KhiproTeam/khipro-mim-touchscreen),
[KhiproTeam/khipro-dark-m17n](https://github.com/KhiproTeam/khipro-dark-m17n) and
[KhiproTeam/khipro-dark-mim-touchscreen](https://github.com/KhiproTeam/khipro-dark-mim-touchscreen),
Copyright (c) 2024 rank_coder, under the [MIT License](LICENSE-KHIPRO-MIT.txt);
the manifest records the upstream commit of each.

The app takes a set only when every file matches the manifest, the set is newer
than the specs it types with, and every spec types every case of its table
(less the stale cases the manifest lists). `scripts/build_bn_khipro_specs.sh`
fetches the upstream files, runs the same check with the app's interpreter and
writes the manifest. Rerun it after any upstream change; never edit a file by
hand, since the hashes would no longer match.

### Offensive Word Lists

The `<lang>_offensive.txt.gz` files contain offensive, profane, and sensitive words to be used for content filtering. They are aggregated from various permissive open-source repositories:
- [LDNOOBWV2](https://github.com/LDNOOBWV2/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words_V2) (CC0 1.0 Universal)
- [profanity-list](https://github.com/okineadev/profanity-list) (The Unlicense)
- [profanity.csv](https://github.com/4troDev/profanity.csv) (MIT License)
- [vietnamese-offensive-words](https://github.com/blue-eyes-vn/vietnamese-offensive-words) (MIT License)
- [indonesian-badwords](https://github.com/drizki/indonesian-badwords) (MIT License)
- [obscene-ukr](https://github.com/kateryna-bobrovnyk/obscene-ukr) (MIT License)
- [washyourmouthoutwithsoap](https://github.com/thisandagain/washyourmouthoutwithsoap) (MIT License)

These lists are provided under their respective public domain and MIT licenses.

### Romanized Word Lists

Malayalam is made by running [ml2en](https://github.com/knadh/ml2en) on the Malayalam frequency list from [hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords).

Urdu is made from [Khubaib01/RomanUrdu-NLP-Sentiment-Corpus](https://huggingface.co/datasets/Khubaib01/RomanUrdu-NLP-Sentiment-Corpus) which is
[Apache 2.0](https://huggingface.co/datasets/choosealicense/licenses/blob/main/markdown/apache-2.0.md) licensed.

Bangla is taken from [istiaqfuad/bangla-english-banglish-pairs](https://huggingface.co/datasets/istiaqfuad/bangla-english-banglish-pairs) which is [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/) licensed.

The following languages are taken from the [Aksharantar Corpus](https://huggingface.co/datasets/ai4bharat/Aksharantar) which is under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/): Hindi, Urdu, Tamil, Telugu, Malayalam, Punjabi, Marathi, Gujarati, Kannada


The `<lang>_rom_v2.txt.gz` lists of Bangla, Gujarati, Hindi, Kannada, Malayalam, Marathi, Punjabi, Sinhala, Tamil, Telugu and Urdu add the [Dakshina dataset](https://github.com/google-research-datasets/dakshina) to the list named `<lang>_rom.txt.gz`, and are under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) as Dakshina is. Dakshina supplies romanizations native speakers wrote for Wikipedia's words, and word counts from 10,000 romanized sentences per language. `scripts/merge_dakshina_rom.py` builds them. Roark, Wolf-Sonkin, Kirov, Mielke, Johny, Demirsahin and Hall, "Processing South Asian Languages Written in the Latin Script: the Dakshina Dataset", LREC 2020.

Arabic was taken from (HadjerHaninebgt7878/ELNER-DZ)[https://huggingface.co/datasets/HadjerHaninebgt7878/ELNER-DZ/] which is under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Nepali was taken from [Boredoom17/Nepali-Corpus](https://huggingface.co/datasets/Boredoom17/Nepali-Corpus) specifically the romanized subset which is under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Sinhala was made using [deshanksuman/Augmented_SinhalatoRomanizedSinhala_Dataset](https://huggingface.co/datasets/deshanksuman/Augmented_SinhalatoRomanizedSinhala_Dataset) which is under [Apache 2.0](https://huggingface.co/datasets/choosealicense/licenses/blob/main/markdown/apache-2.0.md)


### N-gram Lists

Some languages include word bigram/trigram frequency lists
(`<lang>/<prefix>_bigrams.txt.gz`, `<lang>/<prefix>_trigrams.txt.gz`) used for
next-word prediction. Each line is `<word1> <word2> [<word3>] <count>`, sorted
by count descending.

The English lists (`en/en_bigrams.txt.gz`, `en/en_trigrams.txt.gz`) are built
with [`scripts/import_leipzig_ngrams.py`](../scripts/import_leipzig_ngrams.py)
from the [Leipzig Corpora Collection](https://wortschatz.uni-leipzig.de/en)
sentence corpora `eng_news_2024_1M` and `eng-com_web-public_2018_1M`
([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); D. Goldhahn, T. Eckart & U. Quasthoff:
Building Large Monolingual Dictionaries at the Leipzig Corpora Collection: From 100 to 200 Languages.
LREC 2012).

The Bengali lists (`bn/bn_bigrams.txt.gz`, `bn/bn_trigrams.txt.gz`) come from
the same script and the same collection, over 4.8 million sentences and 58.5
million words:

| Corpus | Sentences | Weight |
|---|---|---|
| `ben-bd_web_2017_1M` | 1,000,000 | 3 |
| `ben-bd_web_2014_100K` | 100,000 | 3 |
| `ben_newscrawl_2017_1M` | 1,000,000 | 1 |
| `ben_newscrawl_2015_1M` | 1,000,000 | 1 |
| `ben_wikipedia_2021_1M` | 1,000,000 | 1 |
| `ben_news_2020_300K` | 300,000 | 1 |
| `ben_news_2019_300K` | 300,000 | 1 |
| `ben_newscrawl_2011_100K` | 100,000 | 1 |

The two web corpora count triple. A keyboard has to predict what someone is
writing to a friend, and news and encyclopedia prose is not that, so the
register closest to real typing gets to outrank the ones that are mainly there
for vocabulary breadth. It changes what survives: the app reads only the head
of these files, so the weighting decides which pairs reach the phone at all.

Two things about the Bengali spelling are worth knowing before regenerating
these:

- **Every word is one that `bn_full.txt.gz` already knows.** The build gates
  its tokens on that word list, and an unknown word ends the n-gram rather
  than joining it. 97% of the corpus passes; nearly all of the rest is
  Bijoy-era font mojibake (`সংক্রামত্ম` for `সংক্রান্ত`) or a conjunct that got
  split. Since the keyboard can only offer a word its dictionary holds, a pair
  naming a word outside it would be a row that can never fire.
- **The nukta is decomposed**: য় is stored as য + U+09BC, not as U+09DF. That
  is plain NFC, because U+09DC, U+09DD and U+09DF are Unicode composition
  exclusions, so NFC takes them apart and never puts them back. It is also
  what `bn_full.txt.gz` uses and what the Probhat and Jatiya layouts type.
  Avro is the exception: it commits the precomposed form.

Rebuild them with:

```sh
python3 scripts/import_leipzig_ngrams.py --lang bn --script bengali \
    --counter memory --vocab data/bn/bn_full.txt.gz \
    --max-bigrams 400000 --max-trigrams 200000 \
    https://downloads.wortschatz-leipzig.de/corpora/ben-bd_web_2017_1M.tar.gz#3 \
    https://downloads.wortschatz-leipzig.de/corpora/ben-bd_web_2014_100K.tar.gz#3 \
    https://downloads.wortschatz-leipzig.de/corpora/ben_newscrawl_2017_1M.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_newscrawl_2015_1M.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_wikipedia_2021_1M.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_news_2020_300K.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_news_2019_300K.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_newscrawl_2011_100K.tar.gz
```

#### Bangla word frequencies

`bn/bn_full.txt.gz` is a bare word list: every one of its 451,348 words says
`1`. `bn/bn_full_v2.txt.gz` is the same words with real counts, made by
[`scripts/import_leipzig_unigrams.py`](../scripts/import_leipzig_unigrams.py)
over the eight corpora and weights above, with the n-gram build's tokenizer, so
a word is counted exactly where a pair would have been. 248,000 of the words
occur in the 58.5 million tokens; every count has 2 added, so the 203,000 that
never occur stay in the list at 2, above the app's noise cut. Sorted by count,
ties in code-point order. `bn_full.txt.gz` stays unchanged for the app versions
that fetch it.

Measured by leaving one corpus out of the counts and asking, for each word of
it, romanized the app's way, which word the space bar would commit:

| Held out | Today (flat list, bundled ranking) | `bn_full_v2` with the bundled frequencies added ×4 |
|---|---:|---:|
| `ben_news_2020_300K` (3.6M tokens) | 77.8% | 80.8% |
| `ben-bd_web_2014_100K` (1.4M tokens) | 79.0% | 81.3% |

Those inputs are written by the app's own romanizer, so they measure ranking and
flatter it: nobody's real spelling is in them. On real romanized typing, with
the app's spelling map on, the same change moves little:

| Real typing | Before | `bn_full_v2` |
|---|---:|---:|
| [Dakshina](https://github.com/google-research-datasets/dakshina) sentences (114k words, romanized by hand) | 64.0% | 65.2% |
| [BanglaTLit](https://github.com/farhanishmam/BanglaTLit) val + test (20k words, social media posts) | 66.5% | 66.5% |

Rebuild with:

```sh
python3 scripts/import_leipzig_unigrams.py --script bengali \
    --vocab data/bn/bn_full.txt.gz --out data/bn/bn_full_v2.txt.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben-bd_web_2017_1M.tar.gz#3 \
    https://downloads.wortschatz-leipzig.de/corpora/ben-bd_web_2014_100K.tar.gz#3 \
    https://downloads.wortschatz-leipzig.de/corpora/ben_newscrawl_2017_1M.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_newscrawl_2015_1M.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_wikipedia_2021_1M.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_news_2020_300K.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_news_2019_300K.tar.gz \
    https://downloads.wortschatz-leipzig.de/corpora/ben_newscrawl_2011_100K.tar.gz
```

then `scripts/build_phonetic_indexes.sh ../WMKeyboard bn`, since the Bangla
index is filed over this list.

#### Bangla spellings for the app's map

The app's own `bn_rom.tsv` and `en_bn.tsv` gained about 1,700 spellings from
[BanglaTLit](https://github.com/farhanishmam/BanglaTLit) (MIT), by
[`scripts/mine_bn_spellings.py`](../scripts/mine_bn_spellings.py): romanized
comments from TrickBD that people annotated with the Bangla they mean. Each pair
is in 2+ posts with at least half of a spelling's posts, and every result was read
by hand; the script lists what that review took out. BanglaTLit's train file also
holds Dakshina's Wikipedia sentences, which are excluded so Dakshina stays a fair
test. Thresholds were set on BanglaTLit's validation split, and neither test below
informed them.

| Real typing, Space commits the word | Before | After | In first 4 chips, after |
|---|---:|---:|---:|
| BanglaTLit test (14.7k words) | 68.3% | 74.3% | 80.0% |
| Dakshina sentences (114k words) | 65.3% | 66.5% | 71.3% |

[`scripts/phonetic_index/RealTyping.kt`](../scripts/phonetic_index/RealTyping.kt)
replays the app's commit path to measure this, and its output over the script's
list is what `--apply` reads.

Every other language with a pair list is built the same way, from the same
collection, by
[`scripts/import_leipzig_ngrams.py`](../scripts/import_leipzig_ngrams.py) in
its `generic` mode. Per language it takes at most two corpora: the most recent
conversational one (a `web` or `community` corpus, weighted ×3, for the same
reason the Bengali web corpora are) and the most recent news one (×1), with
Wikipedia standing in when either is missing. A language the collection has no
1M-sentence corpus for gets up to four smaller ones instead, and a lower count
floor (2 rather than 5). The lists stop at 150,000 bigrams and 75,000
trigrams, which is as much as the app reads.

`generic` normalizes the corpus and the word list alike (NFKC, NFC,
lowercase; the app lowercases and NFCs what it looks up), keeps the zero-width
non-joiner where the word list uses it (Persian می‌کنم), and admits a token
only if the language's `<lang>_full.txt.gz` already has it, so an unknown word
ends the n-gram instead of joining it.

| Language | Code | Corpora (weight) | Bigrams | Trigrams |
|---|---|---|---:|---:|
| Hindi | `hi` | `hin-in_web_2015_1M` ×3, `hin_news_2022_1M` ×1 | 150,000 | 75,000 |
| Urdu | `ur` | `urd-in_web_2015_100K` ×3, `urd_newscrawl_2016_1M` ×1 | 150,000 | 75,000 |
| Marathi | `mr` | `mar-in_web_2015_300K` ×3, `mar_newscrawl_2016_1M` ×1 + Tatoeba `mar` ×3 | 150,000 | 75,000 |
| Gujarati | `gu` | `guj_newscrawl_2016_300K` ×1, `guj_newscrawl_2011_300K` ×1 | 150,000 | 75,000 |
| Punjabi | `pa` | `pan-in_web_2015_100K` ×3, `pan_wikipedia_2021_300K` ×1 | 150,000 | 75,000 |
| Odia | `or` | `ori_wikipedia_2021_100K` ×1 | 93,108 | 32,141 |
| Assamese | `as` | `asm_wikipedia_2021_100K` ×1 + Tatoeba `asm` ×3 | 126,142 | 57,626 |
| Tamil | `ta` | `tam-lk_web_2020_1M` ×3, `tam_newscrawl_2011_1M` ×1 | 150,000 | 75,000 |
| Telugu | `te` | `tel_newscrawl_2011_300K` ×1, `tel_wikipedia_2021_300K` ×1, `tel_wikipedia_2016_300K` ×1, `tel_wikipedia_2014_300K` ×1 | 150,000 | 75,000 |
| Kannada | `kn` | `kan_wikipedia_2021_300K` ×1, `kan_wikipedia_2016_300K` ×1, `kan_wikipedia_2011_300K` ×1 | 150,000 | 75,000 |
| Malayalam | `ml` | `mal_wikipedia_2021_300K` ×1, `mal_wikipedia_2016_300K` ×1 | 150,000 | 75,000 |
| Persian | `fa` | `pes-ir_web_2019_1M` ×3, `fas_news_2024_1M` ×1 | 150,000 | 75,000 |
| Arabic | `ar` | `ara-eg_web_2015_300K` ×3, `ara_news_2022_1M` ×1 | 150,000 | 75,000 |
| Spanish | `es` | `spa_web_2016_1M` ×3, `spa_news_2024_1M` ×1 | 150,000 | 75,000 |
| French | `fr` | `fra-ca_web_2020_1M` ×3, `fra_news_2024_1M` ×1 | 150,000 | 75,000 |
| German | `de` | `deu-com_web_2021_1M` ×3, `deu_news_2024_1M` ×1 | 150,000 | 75,000 |
| Portuguese | `pt` | `por-pt_web_2015_1M` ×3, `por_news_2024_1M` ×1 | 150,000 | 75,000 |
| Russian | `ru` | `rus_web_2002_1M` ×3, `rus_news_2024_1M` ×1 | 150,000 | 75,000 |
| Italian | `it` | `ita_web_2011_1M` ×3, `ita_news_2024_1M` ×1 | 150,000 | 75,000 |
| Turkish | `tr` | `tur-tr_web_2019_1M` ×3, `tur_news_2024_1M` ×1 | 150,000 | 75,000 |
| Indonesian | `id` | `ind-com_web_2018_1M` ×3, `ind_news_2024_1M` ×1 | 150,000 | 75,000 |
| Vietnamese | `vi` | `vie-vn_web_2015_1M` ×3, `vie_news_2022_1M` ×1 | 150,000 | 75,000 |
| Polish | `pl` | `pol-com_web_2018_1M` ×3, `pol_news_2024_1M` ×1 | 150,000 | 75,000 |
| Dutch | `nl` | `nld_news_2024_1M` ×1, `nld_wikipedia_2021_1M` ×1 | 150,000 | 75,000 |
| Ukrainian | `uk` | `ukr-ua_web_2019_1M` ×3, `ukr_news_2024_1M` ×1 | 150,000 | 75,000 |
| Korean | `ko` | `kor-kr_web_2020_1M` ×3, `kor_news_2022_1M` ×1 | 150,000 | 75,000 |
| Romanian | `ro` | `ron-ro_web_2015_1M` ×3, `ron_news_2024_1M` ×1 | 150,000 | 75,000 |
| Greek | `el` | `ell-gr_web_2015_1M` ×3, `ell_news_2024_1M` ×1 | 150,000 | 75,000 |
| Czech | `cs` | `ces_web_2012_1M` ×3, `ces_news_2024_1M` ×1 | 150,000 | 75,000 |
| Hungarian | `hu` | `hun-hu_web_2019_1M` ×3, `hun_news_2024_1M` ×1 | 150,000 | 75,000 |
| Swedish | `sv` | `swe-se_web_2020_1M` ×3, `swe_news_2023_1M` ×1 | 150,000 | 75,000 |
| Hebrew | `he` | `heb_news_2020_1M` ×1, `heb_wikipedia_2021_1M` ×1 | 150,000 | 75,000 |
| Malay | `ms` | `msa-my_web_2013_1M` ×3, `msa_newscrawl_2016_300K` ×1 | 150,000 | 75,000 |
| Swahili | `sw` | `swa_wikipedia_2021_100K` ×1, `swa_wikipedia_2016_100K` ×1 | 150,000 | 75,000 |
| Tagalog | `tl` | `tgl_wikipedia_2021/2016/2014_100K` ×1 + Tatoeba `tgl` ×3 | 150,000 | 75,000 |
| Nepali | `ne` | `nep-np_web_2015_1M` ×3, `nep_news_2020_300K` ×1 | 150,000 | 75,000 |
| Sinhala | `si` | `sin_wikipedia_2021_100K` ×1, `sin_wikipedia_2016_100K` ×1, `sin_wikipedia_2014_100K` ×1, `sin_wikipedia_2011_100K` ×1 | 150,000 | 75,000 |
| Azerbaijani | `az` | `aze_newscrawl_2013_1M` ×1, `aze_wikipedia_2021_1M` ×1 | 150,000 | 75,000 |
| Uzbek | `uz` | `uzb_newscrawl_2011_100K` ×1, `uzb_wikipedia_2021_100K` ×1, `uzb_wikipedia_2016_100K` ×1, `uzb_wikipedia_2014_100K` ×1 | 150,000 | 75,000 |
| Kazakh | `kk` | `kaz_newscrawl_2016_1M` ×1 | 150,000 | 63,794 |
| Danish | `da` | `dan-dk_web_2019_1M` ×3, `dan_newscrawl_2023_1M` ×1 | 150,000 | 75,000 |
| Finnish | `fi` | `fin_web_2002_1M` ×3, `fin_news_2022_1M` ×1 | 150,000 | 75,000 |
| Norwegian Bokmål | `nb` | `nob-no_web_2020_1M` ×3, `nob_newscrawl_2019_1M` ×1 | 150,000 | 75,000 |
| Slovak | `sk` | `slk-sk_web_2016_1M` ×3, `slk_newscrawl_2016_1M` ×1 | 150,000 | 75,000 |
| Bulgarian | `bg` | `bul_news_2022_1M` ×1, `bul_wikipedia_2021_1M` ×1 | 150,000 | 75,000 |
| Serbian | `sr` | `srp-rs_web_2016_1M` ×3, `srp_wikipedia_2021_1M` ×1 | 150,000 | 75,000 |
| Croatian | `hr` | `hrv-hr_web_2015_1M` ×3, `hrv_news_2020_1M` ×1 | 150,000 | 75,000 |
| Bosnian | `bs` | `bos_news_2020_300K` ×1, `bos_newscrawl_2015_300K` ×1, `bos_newscrawl_2011_300K` ×1, `bos_wikipedia_2021_300K` ×1 | 150,000 | 75,000 |
| Catalan | `ca` | `cat_newscrawl_2016_1M` ×1, `cat_wikipedia_2021_1M` ×1 | 150,000 | 75,000 |

The Leipzig corpus names change from release to release and the listing at
`api.wortschatz-leipzig.de` is not reliably reachable, so the corpora above were
found by asking the download server for names in the collection's own pattern
(`{iso639-3}[-{country}|-com]_{genre}_{year}_{size}`). To rebuild one, pass the
corpora from its row with their weights:

```sh
python3 scripts/import_leipzig_ngrams.py --lang fa --script generic \
    --counter memory --vocab data/fa/fa_full.txt.gz \
    --max-bigrams 150000 --max-trigrams 75000 \
    https://downloads.wortschatz-leipzig.de/corpora/pes-ir_web_2019_1M.tar.gz#3 \
    https://downloads.wortschatz-leipzig.de/corpora/fas_news_2024_1M.tar.gz
```

The memory counter packs a trigram into one 64-bit number, so it uses only the
2,097,151 commonest words of a longer list (Hungarian, Finnish, Arabic and
Turkish have more). The words it leaves out are each seen about once.

### eBible and Glot500 Word Lists

22 lists come from the redistributable Bible translations of the
[eBible corpus](https://github.com/BibleNLP/ebible) and from
[Glot500](https://huggingface.co/datasets/cis-lmu/Glot500), merged into one
count by [`scripts/import_corpus_words.py`](../scripts/import_corpus_words.py).
They cover keyboard languages no other source here has: four spoken Arabics
(Mesopotamian, Gulf, South and North Levantine), Gheg Albanian, Mapudungun,
Bemba, Kamba, Q'eqchi', Khakas, Umbundu, two Nahuatls, Jingpho, and a few
languages of Papua New Guinea, Benin, Senegal, Panama and Canada. Karakalpak
gets a Latin list beside its Cyrillic one, and Uzbek a Cyrillic one beside its
Latin one. Only words in the text's main script are kept, and a list under
1,000 words is not written. Glot500 shards were read only up to their first
60 MB.

Three candidates were built and thrown away after a look at their top words:
Glot500's Hausa in Arabic script is Classical Arabic, its Latin Sanskrit is
English web text, and its Cyrillic Turkmen is Russian download-page spam.

### Transliterated Word Lists

Five lists are another list carried into the language's other script by
[`scripts/transliterate_wordlist.py`](../scripts/transliterate_wordlist.py),
counts and all: Serbian in Latin (`sr_latn`, Gaj's alphabet), Bosnian in
Cyrillic (`bs_cyrl`), Kazakh in the 2021 Latin alphabet (`kk_latn`),
Belarusian in classical Łacinka (`be_latn`), and Standard Moroccan Tamazight
in IRCAM Latin (`zgh_latn`). A word with a letter the scheme has no mapping for
(a Russian word in the Belarusian list, say) is dropped.

```sh
python3 scripts/transliterate_wordlist.py sr bs kk be zgh
python3 scripts/import_corpus_words.py --folder kjh --glot500 kjh_Cyrl.arrow --script-name CYRILLIC
```

### Tatoeba Word Lists

31 languages that no larger corpus covers have word lists counted from the
[Tatoeba sentence corpus](https://tatoeba.org/) ([CC BY 2.0
FR](https://creativecommons.org/licenses/by/2.0/fr/)) by
[`scripts/import_tatoeba_words.py`](../scripts/import_tatoeba_words.py). Only
languages whose sentences give at least 1,000 distinct words are built, from
Tamazight's 81,160 (Tatoeba's `ber`, nearly 700,000 sentences) down to Romani's
1,029; the many languages Tatoeba holds a few dozen sentences for are left out.

Each list counts only the sentences written in its own script. Ottoman Turkish
has two, `ota_full` for the Arabic-script sentences and `ota_latn` for the
transliterated ones; Interslavic's list is `isv_latn` (Tatoeba's Cyrillic
Interslavic is too small) and Ho's is `hoc_latn` (its Warang Citi sentences are
left for a future list). Words are NFKC+NFC normalised and lower-cased; Greek
epsilon and gamma written for `ɛ` and `ɣ` are folded into the Latin letters, as
are Nuer's stray line-below marks into U+0331, and Arabic- and Hebrew-script
lists drop the vowel points. Kirundi's `rn_full` was replaced by its Tatoeba
list: the old one was an unsorted list with a count of 5 on every word.

```sh
curl -LO https://downloads.tatoeba.org/exports/per_language/swc/swc_sentences.tsv.bz2
python3 scripts/import_tatoeba_words.py --sentences swc_sentences.tsv.bz2 --folder swc --script latin
python3 scripts/import_tatoeba_words.py --sentences ota_sentences.tsv.bz2 --folder ota --stem ota_latn --script latin
```

### Tatoeba Sentence Corpus Word Pairs

For 196 additional languages — including constructed languages (Esperanto, Toki
Pona, Klingon, Lojban, Ido, Interlingua, Interlingue, Lingua Franca Nova, Volapük,
Novial, Kotava, Quenya), classical languages (Latin, Gothic, Old English, Sanskrit),
AOSP keyboard languages (Lithuanian, Latvian, Slovenian, Basque, Galician, etc.),
and regional and indigenous languages across Europe, Africa, Asia, and the Americas —
word bigram and trigram lists are built from the [Tatoeba sentence corpus](https://tatoeba.org/)
([CC BY 2.0 FR](https://creativecommons.org/licenses/by/2.0/fr/) / CC0) using
[`scripts/import_tatoeba_ngrams.py`](../scripts/import_tatoeba_ngrams.py).

Tatoeba consists of short, human-translated conversational sentences, the exact
register needed for phone keyboard prediction. Klingon (`tlh`) preserves
phonemic casing and glottal stops (`tlhIngan`, 'e', 'ej'); Bengali/Assamese
script handles NFC nukta decomposition; zero-width space (`\u200b`) in scripts like
Khmer is treated as a word boundary; and all lists gate strictly against the
repository's `<lang>_full.txt.gz` and `<lang>_aosp.txt.gz` vocabularies, so
unknown words break the n-gram window and never produce phantom entries.

In addition, all 50 existing language pair lists (including English, Russian,
German, French, Spanish, Italian, Portuguese, Turkish, Dutch, Polish, Arabic,
Hebrew, Hindi, Bengali, Assamese, Marathi, Tagalog, etc.) have been improved by
blending Tatoeba conversational sentences (weighted ×3) into their corpus lists.

| Language | Code | Tatoeba Code | Bigrams | Trigrams |
|---|---|---|---:|---:|
| Esperanto | `eo` | `epo` | 150,000 | 75,000 |
| Tamazight (Latin) | `ber` | `ber` | 150,000 | 75,000 |
| Lithuanian | `lt` | `lit` | 67,725 | 44,525 |
| Kabyle | `kab` | `kab` | 66,130 | 68,844 |
| Filipino | `fil` | `tgl` | 45,846 | 56,424 |
| Macedonian | `mk` | `mkd` | 29,745 | 25,084 |
| Interlingua | `ia` | `ina` | 27,230 | 21,349 |
| Tatar | `tt` | `tat` | 25,853 | 10,257 |
| Latin | `la` | `lat` | 23,317 | 9,145 |
| Eastern Armenian | `hy` | `hye` | 19,691 | 12,421 |
| Congo Swahili | `swc` | `swc` | 17,503 | 6,289 |
| Hausa | `ha` | `hau` | 17,142 | 9,745 |
| Lingua Franca Nova | `lfn` | `lfn` | 16,828 | 15,364 |
| Tigre | `tig` | `tig` | 14,255 | 5,448 |
| Occitan | `oc` | `oci` | 12,007 | 6,502 |
| Norwegian Bokmål | `no` | `nob` | 11,760 | 8,023 |
| Lojban | `jbo` | `jbo` | 10,949 | 9,213 |
| Low German (Low Saxon) | `nds` | `nds` | 10,729 | 6,977 |
| Yiddish | `yi` | `yid` | 9,604 | 7,589 |
| Toki Pona | `tok` | `tok` | 8,438 | 35,332 |
| Icelandic | `is` | `isl` | 8,361 | 5,510 |
| Latvian | `lv` | `lvs` | 8,036 | 3,568 |
| Standard Moroccan Tamazight | `zgh` | `zgh` | 7,530 | 3,829 |
| Klingon | `tlh` | `tlh` | 7,271 | 2,257 |
| Low Saxon (Netherlands) | `nds_nl` | `nds` | 7,091 | 4,804 |
| Gronings | `gos` | `gos` | 6,663 | 2,719 |
| Norwegian Nynorsk | `nn` | `nno` | 6,557 | 4,176 |
| Ido | `io` | `ido` | 6,322 | 3,512 |
| Belarusian (Taraškievica) | `be_x_old` | `bel` | 6,205 | 1,980 |
| Belarusian | `be` | `bel` | 6,136 | 1,946 |
| Galician | `gl` | `glg` | 6,089 | 2,355 |
| Lingala | `ln` | `lin` | 5,312 | 2,143 |
| Central Kurdish (Soranî) | `ckb` | `ckb` | 5,104 | 1,690 |
| Interlingue | `ie` | `ile` | 4,824 | 3,594 |
| Northern Kurdish (Kurmancî) | `ku` | `kmr` | 4,562 | 2,017 |
| Breton | `br` | `bre` | 4,201 | 2,949 |
| Coastal Kadazan | `kzj` | `kzj` | 3,986 | 1,773 |
| Nande | `nnb` | `nnb` | 3,073 | 337 |
| Santali | `sat` | `sat` | 2,920 | 1,474 |
| Uyghur | `ug` | `uig` | 2,892 | 809 |
| Afrikaans | `af` | `afr` | 2,840 | 1,569 |
| Old Prussian | `prg` | `prg` | 2,451 | 835 |
| Basque | `eu` | `eus` | 2,448 | 823 |
| Estonian | `et` | `est` | 2,205 | 882 |
| Turkmen | `tk` | `tuk` | 2,126 | 674 |
| North Frisian | `frr` | `frr` | 1,858 | 671 |
| Tarifit | `rif` | `rif` | 1,844 | 716 |
| Georgian | `ka` | `kat` | 1,817 | 425 |
| Khasi | `kha` | `kha` | 1,734 | 1,311 |
| Central Kanuri | `knc` | `knc` | 1,712 | 185 |
| Irish | `ga` | `gle` | 1,686 | 916 |
| Chavacano | `cbk` | `cbk` | 1,671 | 1,057 |
| Central Dusun | `dtp` | `dtp` | 1,568 | 508 |
| Cornish | `kw` | `cor` | 1,542 | 1,151 |
| Slovenian | `sl` | `slv` | 1,532 | 489 |
| Albanian | `sq` | `sqi` | 1,526 | 614 |
| Nuer | `nus` | `nus` | 1,358 | 517 |
| Hunsrik | `hrx` | `hrx` | 1,303 | 611 |
| Ilocano | `ilo` | `ilo` | 1,275 | 537 |
| Kirundi | `rn` | `run` | 1,259 | 352 |
| Meadow Mari | `mhr` | `mhr` | 1,216 | 186 |
| Mongolian | `mn` | `mon` | 1,192 | 332 |
| Swabian | `swg` | `swg` | 1,143 | 300 |
| Udmurt | `udm` | `udm` | 1,092 | 223 |
| Kotava | `avk` | `avk` | 1,037 | 262 |
| Ossetian | `os` | `oss` | 1,002 | 89 |
| Welsh | `cy` | `cym` | 994 | 501 |
| Guadeloupean Creole | `gcf` | `gcf` | 938 | 639 |
| Volapük | `vo` | `vol` | 855 | 225 |
| Ligurian | `lij` | `lij` | 846 | 327 |
| Cebuano | `ceb` | `ceb` | 839 | 275 |
| Scottish Gaelic | `gd` | `gla` | 794 | 471 |
| Tigrinya | `ti` | `tir` | 779 | 83 |
| Ladino | `lad` | `lad` | 721 | 320 |
| Ottoman Turkish (Latin) | `ota_latn` | `ota` | 716 | 97 |
| Ancient Greek | `grc` | `grc` | 698 | 246 |
| Ho (Latin) | `hoc_latn` | `hoc` | 673 | 211 |
| Guarani | `gn` | `grn` | 670 | 151 |
| Brithenig | `bzt` | `bzt` | 666 | 355 |
| Middle English | `enm` | `enm` | 654 | 379 |
| Palauan | `pau` | `pau` | 622 | 423 |
| Romani | `rom` | `rom` | 572 | 419 |
| Interslavic (Latin) | `isv_latn` | `isv` | 502 | 202 |
| Luxembourgish | `lb` | `ltz` | 501 | 264 |
| Avar | `av` | `ava` | 497 | 106 |
| Algerian Arabic | `arq` | `arq` | 483 | 119 |
| Piedmontese | `pms` | `pms` | 470 | 211 |
| Maori | `mi` | `mri` | 435 | 263 |
| Kapampangan | `pam` | `pam` | 428 | 160 |
| Lower Sorbian | `dsb` | `dsb` | 421 | 129 |
| Upper Sorbian | `hsb` | `hsb` | 392 | 95 |
| Dargwa | `dar` | `dar` | 387 | 95 |
| Novial | `nov` | `nov` | 374 | 141 |
| Waray | `war` | `war` | 370 | 112 |
| Chuvash | `cv` | `chv` | 368 | 73 |
| Egyptian Arabic | `arz` | `arz` | 360 | 91 |
| Old East Slavic | `orv` | `orv` | 349 | 79 |
| Javanese | `jv` | `jav` | 332 | 91 |
| Tamajaq (Latin) | `ttq` | `ttq` | 293 | 110 |
| Asturian | `ast` | `ast` | 289 | 70 |
| Sundanese | `su` | `sun` | 273 | 56 |
| Frisian | `fy` | `fry` | 258 | 69 |
| Old English | `ang` | `ang` | 253 | 79 |
| Picard | `pcd` | `pcd` | 248 | 75 |
| Ottoman Turkish | `ota` | `ota` | 213 | 44 |
| Sundanese | `sun` | `sun` | 210 | 38 |
| Silesian | `szl` | `szl` | 199 | 48 |
| Kashubian | `csb` | `csb` | 197 | 60 |
| Southern Kurdish | `sdh` | `sdh` | 180 | 18 |
| Venetian | `vec` | `vec` | 178 | 88 |
| Chukchi | `ckt` | `ckt` | 173 | 28 |
| Rohingya | `rhg` | `rhg` | 160 | 7 |
| Faroese | `fo` | `fao` | 154 | 35 |
| Sranan Tongo | `srn` | `srn` | 153 | 40 |
| Swiss German | `gsw` | `gsw` | 149 | 30 |
| Southern Altai | `alt` | `alt` | 144 | 19 |
| Buryat | `bxr` | `bua` | 141 | 17 |
| Kyrgyz | `ky` | `kir` | 132 | 35 |
| Khmer | `km` | `khm` | 124 | 35 |
| Crimean Tatar | `crh` | `crh` | 118 | 29 |
| Veps | `vep` | `vep` | 118 | 27 |
| Maltese | `mt` | `mlt` | 114 | 23 |
| Tamahaq (Latin) | `thv` | `thv` | 112 | 17 |
| Gothic | `got` | `got` | 102 | 45 |
| Bavarian | `bar` | `bar` | 101 | 29 |
| Kalmyk | `xal` | `xal` | 101 | 6 |
| Kven | `fkv` | `fkv` | 99 | 21 |
| Awadhi | `awa` | `awa` | 88 | 48 |
| Latgalian | `ltg` | `ltg` | 83 | 9 |
| Hawaiian | `haw` | `haw` | 80 | 49 |
| Tetum | `tet` | `tet` | 77 | 52 |
| Wayuu | `guc` | `guc` | 74 | 4 |
| Yakut | `sah` | `sah` | 73 | 8 |
| Bashkir | `ba` | `bak` | 67 | 20 |
| Muscogee | `mus` | `mus` | 65 | 12 |
| Tok Pisin | `tpi` | `tpi` | 64 | 39 |
| Luganda | `lg` | `lug` | 62 | 7 |
| Mirandese | `mwl` | `mwl` | 60 | 17 |
| Haitian Creole | `ht` | `hat` | 56 | 20 |
| Erzya | `myv` | `myv` | 52 | 11 |
| Iban | `iba` | `iba` | 51 | 13 |
| Quenya | `qya` | `qya` | 50 | 23 |
| Saraiki | `skr` | `skr` | 49 | 21 |
| Saterland Frisian | `stq` | `stq` | 45 | 16 |
| Amharic | `am` | `amh` | 44 | 11 |
| Chamorro | `ch` | `cha` | 44 | 4 |
| Emilian | `eml` | `egl` | 44 | 17 |
| Northern Sami | `se` | `sme` | 42 | 7 |
| Lezgi | `lez` | `lez` | 40 | 9 |
| Colognian | `ksh` | `ksh` | 39 | 10 |
| Banjar | `bjn` | `bjn` | 38 | 5 |
| Ladin | `lld` | `lld` | 38 | 10 |
| Papiamento | `pap` | `pap` | 31 | 11 |
| Somali | `so` | `som` | 31 | 5 |
| Yoruba | `yo` | `yor` | 31 | 5 |
| Bambara | `bm` | `bam` | 30 | 3 |
| Samoan | `sm` | `smo` | 28 | 11 |
| Scots | `sco` | `sco` | 27 | 3 |
| Aragonese | `an` | `arg` | 26 | 10 |
| Quechua | `qu` | `que` | 26 | 7 |
| Nahuatl | `nah` | `nah` | 25 | 2 |
| Rusyn | `rue` | `rue` | 22 | 4 |
| Tuvinian | `tyv` | `tyv` | 22 | 10 |
| Extremaduran | `ext` | `ext` | 21 | 7 |
| Pennsylvania German | `pdc` | `pdc` | 21 | 9 |
| Biblical Hebrew | `hbo` | `hbo` | 19 | 5 |
| Bhojpuri | `bho` | `bho` | 18 | 5 |
| Tumbuka | `tum` | `tum` | 18 | 3 |
| Xhosa | `xh` | `xho` | 16 | 1 |
| Pangasinan | `pag` | `pag` | 15 | 5 |
| Sanskrit | `sa` | `san` | 15 | 0 |
| Neapolitan | `nap` | `nap` | 14 | 2 |
| Mingrelian | `xmf` | `xmf` | 13 | 3 |
| Western Armenian | `hyw` | `hyw` | 12 | 2 |
| Minangkabau | `min` | `min` | 12 | 1 |
| Pashto | `ps` | `pus` | 12 | 5 |
| Wolof | `wo` | `wol` | 12 | 5 |
| Malagasy | `mg` | `mlg` | 11 | 2 |
| Western Punjabi | `pnb` | `pnb` | 10 | 3 |
| Tajik | `tg` | `tgk` | 10 | 0 |
| Dhivehi | `div` | `div` | 9 | 2 |
| Dhivehi | `dv` | `div` | 8 | 1 |
| Kabardian | `kbd` | `kbd` | 8 | 1 |
| Moroccan Arabic | `ary` | `ary` | 7 | 2 |
| Corsican | `co` | `cos` | 7 | 3 |
| Karakalpak | `kaa` | `kaa` | 7 | 3 |
| Hill Mari | `mrj` | `mrj` | 7 | 1 |
| Pipil | `ppl` | `ppl` | 6 | 1 |
| Walloon | `wa` | `wln` | 5 | 0 |
| Karachay-Balkar | `krc` | `krc` | 4 | 0 |
| Zulu | `zu` | `zul` | 4 | 0 |
| Gagauz | `gag` | `gag` | 3 | 0 |
| Tashelhit | `shi` | `shi` | 3 | 1 |
| Talysh | `tly` | `tly` | 3 | 0 |
| Greenlandic | `kl` | `kal` | 2 | 0 |
| Min Nan Chinese | `nan` | `nan` | 1 | 0 |

To generate or blend word pairs from Tatoeba sentences:

```sh
# Generate standalone pairs:
python3 scripts/import_tatoeba_ngrams.py --lang eo tok tlh la --tatoeba sentences.csv

# Blend into existing pair lists with conversational weight 3:
python3 scripts/import_tatoeba_ngrams.py --lang en es fr de hi bn as mr tl --blend --weight 3 --tatoeba sentences.csv
```

The romanized Bengali lists (`bn/bn_rom_*`) are a different thing entirely, and
personal rather than corpus-built: see
[`scripts/import_facebook_chats.py`](../scripts/import_facebook_chats.py).

The Banglish emoji dictionary (`bn/bn_rom_emoji.json.gz`) is built, not
imported: the Bengali pack's keywords and names transliterated into the Latin
spellings people chat in, ranked by the `bn_rom` word list, with the English
pack's keywords alongside. See
[`scripts/build_bn_rom_emoji.py`](../scripts/build_bn_rom_emoji.py).


## Licensing

Each dictionary retains the license of its original source.

| Dataset | License |
|---------|---------|
| Most frequency lists | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| `*_bigrams`, `*_trigrams` built from the Leipzig Corpora Collection | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `*_bigrams`, `*_trigrams` built or improved from Tatoeba | [CC BY 2.0 FR](https://creativecommons.org/licenses/by/2.0/fr/) / CC0 ([Tatoeba](https://tatoeba.org/)) |
| Word lists counted from Tatoeba (see [Tatoeba Word Lists](#tatoeba-word-lists)) | [CC BY 2.0 FR](https://creativecommons.org/licenses/by/2.0/fr/) ([Tatoeba](https://tatoeba.org/)) |
| Word lists counted from eBible and Glot500 (see [eBible and Glot500 Word Lists](#ebible-and-glot500-word-lists)) | Word counts only. Each eBible translation keeps its own licence (see the corpus's `metadata/translations.csv`); Glot500 is a collection of openly licensed sources (see its dataset card) |
| `ur` | [MIT](https://github.com/urduhack/urdu-words/blob/master/LICENSE) |
| `bs` | Counts: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Spelling forms: [LGPL-3.0](https://github.com/ebukva/bs_BA/blob/master/license.txt), ebukva/bs_BA |
| `si` | [MIT](https://github.com/kasunw22/sinhala-para-dict/blob/main/LICENSE) |
| `tlh` | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| `qya` | [Ardalambion](https://ardalambion.net) |
| `tok` | [CC0 1.0 Universal](https://github.com/lipu-linku/sona) / [lipu Linku](https://linku.la) |
| `bho`, `brx`, `doi`, `ks`, `mai`, `raj` | [MIT](https://github.com/motaitalic/devanagari-documentation/blob/main/LICENSE) |
| `ab`, `ace`, `ady`, `alt`, `ami`, `ang`, `ann`, `anp`, `arc`, `arz`, `atj`, `av`, `avk`, `awa`, `ay`, `azb`, `bar`, `bbc`, `bdr`, `be-tarask`, `bew`, `bh`, `bi`, `bik`, `bjn`, `blk`, `bol`, `bpy`, `btm`, `bxr`, `cbk`, `cbk-zam`, `cdo`, `ch`, `chr`, `chy`, `cr`, `crh`, `csb`, `cu`, `dag`, `dga`, `din`, `diq`, `dsb`, `dtp`, `dty`, `dv`, `dz`, `eml`, `ext`, `fat`, `fj`, `fon`, `frp`, `frr`, `fur`, `gag`, `gan`, `gcr`, `gd`, `glk`, `gom`, `gor`, `got`, `gpe`, `guc`, `gur`, `guw`, `hak`, `haw`, `hif`, `hsb`, `hyw`, `iba`, `igl`, `ik`, `inh`, `isv`, `iu`, `jam`, `kaa`, `kai`, `kaj`, `kbd`, `kbp`, `kcg`, `kge`, `knc`, `koi`, `krc`, `ksh`, `ku`, `kus`, `kv`, `kw`, `lad`, `lbe`, `lez`, `lfn`, `lij`, `lld`, `lmo`, `loz`, `ltg`, `lub`, `lzh`, `mag`, `map-bms`, `mdf`, `mg`, `mhr`, `mi`, `mni`, `mnw`, `mos`, `mrj`, `myv`, `mzn`, `nah`, `nan`, `nds`, `nds-nl`, `new`, `nia`, `nov`, `nqo`, `nrm`, `nso`, `nup`, `olo`, `or`, `pag`, `pam`, `pap`, `pcd`, `pcm`, `pdc`, `pfl`, `pi`, `pnb`, `pnt`, `ppl`, `pwn`, `rif`, `rki`, `rmy`, `roa-tara`, `rsk`, `rue`, `rup`, `rw`, `sah`, `sat`, `scn`, `sg`, `sgs`, `shi`, `shn`, `skr`, `sm`, `smn`, `sn`, `srn`, `ss`, `stq`, `su`, `syl`, `szl`, `szy`, `tay`, `tdd`, `tet`, `tig`, `tly`, `to`, `tpi`, `trv`, `tum`, `tw`, `ty`, `tyv`, `udm`, `vec`, `vep`, `vls`, `vro`, `wuu`, `xal`, `xmf`, `yue`, `zea`, `zgh`, `zh` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (Wikimedia Data Dumps) |
| `aa`, `af`, `ak`, `am`, `an`, `as`, `az`, `ba`, `be`, `bm`, `bo`, `br`, `ce`, `co`, `cv`, `cy`, `div`, `ee`, `eo`, `eu`, `ff`, `fo`, `fy`, `gl`, `gn`, `gu`, `gv`, `ha`, `hi`, `ht`, `hy`, `ia`, `ie`, `ig`, `ina`, `io`, `jv`, `ka`, `kg`, `ki`, `kk`, `kl`, `km`, `kn`, `koi`, `kok`, `ky`, `lg`, `li`, `ln`, `lo`, `lv`, `mn`, `mr`, `ms`, `mt`, `my`, `myv`, `nd`, `ne`, `nn`, `nr`, `nv`, `ny`, `oc`, `om`, `os`, `pa`, `ps`, `qu`, `rm`, `sco`, `se`, `sh`, `sna`, `so`, `ssw`, `st`, `sun`, `sw`, `te`, `tg`, `ti`, `tk`, `tl`, `tn`, `ts`, `tt`, `ug`, `uz`, `ve`, `vi`, `vo`, `wa`, `wo`, `xh`, `yi`, `yo`, `za`, `zu` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `ta` | [MIT](https://github.com/vigneshwaran-chandrasekaran/tamil-language-words-list/blob/master/LICENSE) |
| `bgn` | [Apache 2.0](https://huggingface.co/datasets/choosealicense/licenses/blob/main/markdown/apache-2.0.md) / [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| `blo` | [Unicode License Agreement](https://www.unicode.org/license.txt) / [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) |
| `ccp` | [MIT](https://huggingface.co/datasets/choosealicense/licenses/blob/main/markdown/mit.md) |
| `fil` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| `quc` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `rhg` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) / Public Domain |
| `syr` | [MIT](https://github.com/ETCBC/peshitta/blob/master/LICENSE) |
| `yue`, `yue_Hans` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| `jbo` | Public Domain |
| `bn` word list | Public Domain (from [tahmid02016/bangla-wordlist](https://github.com/tahmid02016/bangla-wordlist)) |
| `bn` n-gram lists (`bn_bigrams`, `bn_trigrams`) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (Leipzig Corpora Collection) |
| Spellings mined by `mine_bn_spellings.py` | [MIT](https://github.com/farhanishmam/BanglaTLit/blob/main/LICENSE) (BanglaTLit) |
| `bn_full_v2` word counts | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (Leipzig Corpora Collection); the words themselves as `bn` word list |
| AOSP word lists (`<stem>_aosp.txt.gz`) | [Apache 2.0](LICENSE-AOSP-APACHE-2.0.txt), Copyright (C) The Android Open Source Project (`en_au_aosp`: also The LineageOS Project); `en_ca_aosp` and `en_au_aosp` respelled with ESDB data under its own notice (see [`NOTICE`](../NOTICE)) |
| Emoji dictionaries (`<lang>_emoji.json.gz`) | [Unicode License Agreement (v3)](https://www.unicode.org/license.txt) / [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) (derived from Unicode CLDR annotations & Unicode Emoji Data via [KDE/kemoji](https://github.com/KDE/kemoji)) |

| Repository code | MIT |


Please preserve the required attribution when redistributing or creating derivative works from these datasets.

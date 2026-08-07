# Frequency Word Lists

A collection of frequency word lists for 215+ languages.

## Format

Dictionary files are stored as gzip-compressed text files:

```
<lang>/<lang>_full.txt.gz
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
| [kasunw22/sinhala-para-dict](https://github.com/kasunw22/sinhala-para-dict) | `si` |
| [vigneshwaran-chandrasekaran/tamil-language-words-list](https://github.com/vigneshwaran-chandrasekaran/tamil-language-words-list) | `ta` |
| [tahmid02016/bangla-wordlist](https://github.com/tahmid02016/bangla-wordlist) | `bn` |
| [Leipzig Corpora Collection](https://wortschatz.uni-leipzig.de/de) | `aa`, `af`, `ak`, `am`, `an`, `as`, `az`, `ba`, `be`, `bm`, `bo`, `br`, `ce`, `co`, `cv`, `cy`, `div`, `ee`, `eo`, `eu`, `ff`, `fo`, `fy`, `gl`, `gn`, `gu`, `gv`, `ha`, `hi`, `ht`, `hy`, `ia`, `ie`, `ig`, `ina`, `io`, `jv`, `ka`, `kg`, `ki`, `kk`, `kl`, `km`, `kn`, `koi`, `ky`, `lg`, `li`, `ln`, `lo`, `lv`, `mn`, `mr`, `ms`, `mt`, `my`, `myv`, `nd`, `ne`, `nn`, `nr`, `nv`, `ny`, `oc`, `om`, `os`, `pa`, `ps`, `qu`, `rm`, `rn`, `sco`, `se`, `sh`, `sna`, `so`, `ssw`, `st`, `sun`, `sw`, `te`, `tg`, `ti`, `tk`, `tl`, `tn`, `ts`, `tt`, `ug`, `uz`, `ve`, `vi`, `vo`, `wa`, `wo`, `xh`, `yi`, `yo`, `za`, `zu` |
| [Wikimedia data dumps](https://dumps.wikimedia.org/) | `ab`, `ace`, `ady`, `alt`, `ami`, `ang`, `ann`, `anp`, `arc`, `arz`, `atj`, `av`, `avk`, `awa`, `ay`, `azb`, `bar`, `bbc`, `bdr`, `be-tarask`, `bew`, `bh`, `bi`, `bik`, `bjn`, `blk`, `bol`, `bpy`, `btm`, `bxr`, `cbk`, `cbk-zam`, `cdo`, `ch`, `chr`, `chy`, `cr`, `crh`, `csb`, `cu`, `dag`, `dga`, `din`, `diq`, `dsb`, `dtp`, `dty`, `dv`, `dz`, `eml`, `ext`, `fat`, `fj`, `fon`, `frp`, `frr`, `fur`, `gag`, `gan`, `gcr`, `gd`, `glk`, `gom`, `gor`, `got`, `gpe`, `guc`, `gur`, `guw`, `hak`, `haw`, `hif`, `hsb`, `hyw`, `iba`, `igl`, `ik`, `inh`, `isv`, `iu`, `jam`, `kaa`, `kai`, `kaj`, `kbd`, `kbp`, `kcg`, `kge`, `knc`, `koi`, `krc`, `ksh`, `kus`, `kv`, `kw`, `lad`, `lbe`, `lez`, `lfn`, `lij`, `lld`, `lmo`, `loz`, `ltg`, `lub`, `lzh`, `mag`, `map-bms`, `mdf`, `mg`, `mhr`, `mi`, `mni`, `mnw`, `mos`, `mrj`, `myv`, `mzn`, `nah`, `nan`, `nds`, `nds-nl`, `new`, `nia`, `nov`, `nqo`, `nrm`, `nso`, `nup`, `olo`, `or`, `pag`, `pam`, `pap`, `pcd`, `pcm`, `pdc`, `pfl`, `pi`, `pnb`, `pnt`, `ppl`, `pwn`, `rif`, `rki`, `rmy`, `roa-tara`, `rsk`, `rue`, `rup`, `rw`, `sah`, `sat`, `scn`, `sg`, `sgs`, `shi`, `shn`, `skr`, `sm`, `smn`, `sn`, `srn`, `ss`, `stq`, `su`, `syl`, `szl`, `szy`, `tay`, `tdd`, `tet`, `tig`, `tly`, `to`, `tpi`, `trv`, `tum`, `tw`, `ty`, `tyv`, `udm`, `vec`, `vep`, `vls`, `vro`, `wuu`, `xal`, `xmf`, `yue`, `zea`, `zgh`, `zh` |
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
| [KDE/kemoji](https://github.com/KDE/kemoji) (Unicode CLDR & Unicode Emoji Data) | Emoji dictionaries (`<lang>_emoji.json.gz`) for 141 languages |



Some datasets have been reformatted, compressed, or reorganized for consistency. Original attribution and licensing remain unchanged.


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

The romanized Bengali lists (`bn/bn_rom_*`) are a different thing entirely, and
personal rather than corpus-built: see
[`scripts/import_facebook_chats.py`](../scripts/import_facebook_chats.py).


## Licensing

Each dictionary retains the license of its original source.

| Dataset | License |
|---------|---------|
| Most frequency lists | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| `ur` | [MIT](https://github.com/urduhack/urdu-words/blob/master/LICENSE) |
| `si` | [MIT](https://github.com/kasunw22/sinhala-para-dict/blob/main/LICENSE) |
| `tlh` | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| `qya` | [Ardalambion](https://ardalambion.net) |
| `tok` | [CC0 1.0 Universal](https://github.com/lipu-linku/sona) / [lipu Linku](https://linku.la) |
| `bho`, `brx`, `doi`, `ks`, `mai`, `raj` | [MIT](https://github.com/motaitalic/devanagari-documentation/blob/main/LICENSE) |
| `ab`, `ace`, `ady`, `alt`, `ami`, `ang`, `ann`, `anp`, `arc`, `arz`, `atj`, `av`, `avk`, `awa`, `ay`, `azb`, `bar`, `bbc`, `bdr`, `be-tarask`, `bew`, `bh`, `bi`, `bik`, `bjn`, `blk`, `bol`, `bpy`, `btm`, `bxr`, `cbk`, `cbk-zam`, `cdo`, `ch`, `chr`, `chy`, `cr`, `crh`, `csb`, `cu`, `dag`, `dga`, `din`, `diq`, `dsb`, `dtp`, `dty`, `dv`, `dz`, `eml`, `ext`, `fat`, `fj`, `fon`, `frp`, `frr`, `fur`, `gag`, `gan`, `gcr`, `gd`, `glk`, `gom`, `gor`, `got`, `gpe`, `guc`, `gur`, `guw`, `hak`, `haw`, `hif`, `hsb`, `hyw`, `iba`, `igl`, `ik`, `inh`, `isv`, `iu`, `jam`, `kaa`, `kai`, `kaj`, `kbd`, `kbp`, `kcg`, `kge`, `knc`, `koi`, `krc`, `ksh`, `kus`, `kv`, `kw`, `lad`, `lbe`, `lez`, `lfn`, `lij`, `lld`, `lmo`, `loz`, `ltg`, `lub`, `lzh`, `mag`, `map-bms`, `mdf`, `mg`, `mhr`, `mi`, `mni`, `mnw`, `mos`, `mrj`, `myv`, `mzn`, `nah`, `nan`, `nds`, `nds-nl`, `new`, `nia`, `nov`, `nqo`, `nrm`, `nso`, `nup`, `olo`, `or`, `pag`, `pam`, `pap`, `pcd`, `pcm`, `pdc`, `pfl`, `pi`, `pnb`, `pnt`, `ppl`, `pwn`, `rif`, `rki`, `rmy`, `roa-tara`, `rsk`, `rue`, `rup`, `rw`, `sah`, `sat`, `scn`, `sg`, `sgs`, `shi`, `shn`, `skr`, `sm`, `smn`, `sn`, `srn`, `ss`, `stq`, `su`, `syl`, `szl`, `szy`, `tay`, `tdd`, `tet`, `tig`, `tly`, `to`, `tpi`, `trv`, `tum`, `tw`, `ty`, `tyv`, `udm`, `vec`, `vep`, `vls`, `vro`, `wuu`, `xal`, `xmf`, `yue`, `zea`, `zgh`, `zh` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (Wikimedia Data Dumps) |
| `aa`, `af`, `ak`, `am`, `an`, `as`, `az`, `ba`, `be`, `bm`, `bo`, `br`, `ce`, `co`, `cv`, `cy`, `div`, `ee`, `eo`, `eu`, `ff`, `fo`, `fy`, `gl`, `gn`, `gu`, `gv`, `ha`, `hi`, `ht`, `hy`, `ia`, `ie`, `ig`, `ina`, `io`, `jv`, `ka`, `kg`, `ki`, `kk`, `kl`, `km`, `kn`, `koi`, `ky`, `lg`, `li`, `ln`, `lo`, `lv`, `mn`, `mr`, `ms`, `mt`, `my`, `myv`, `nd`, `ne`, `nn`, `nr`, `nv`, `ny`, `oc`, `om`, `os`, `pa`, `ps`, `qu`, `rm`, `rn`, `sco`, `se`, `sh`, `sna`, `so`, `ssw`, `st`, `sun`, `sw`, `te`, `tg`, `ti`, `tk`, `tl`, `tn`, `ts`, `tt`, `ug`, `uz`, `ve`, `vi`, `vo`, `wa`, `wo`, `xh`, `yi`, `yo`, `za`, `zu` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by/4.0/) |
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
| Emoji dictionaries (`<lang>_emoji.json.gz`) | [Unicode License Agreement (v3)](https://www.unicode.org/license.txt) / [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) (derived from Unicode CLDR annotations & Unicode Emoji Data via [KDE/kemoji](https://github.com/KDE/kemoji)) |

| Repository code | MIT |


Please preserve the required attribution when redistributing or creating derivative works from these datasets.

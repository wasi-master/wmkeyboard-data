# Frequency Word Lists

A collection of frequency word lists for 64 languages.

## Format

Dictionary files are stored as gzip-compressed text files:

```
<lang>/<lang>_full.txt.gz
```

Some languages also include an optional offensive word list:

```
<lang>/<lang>_offensive.txt.gz
```

After decompression, each frequency list contains one entry per line:

```text
word frequency
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
| [Leipzig Corpora Collection](https://wortschatz.uni-leipzig.de/de) | `af`, `am`, `as`, `az`, `be`, `br`, `eo`, `eu`, `gl`, `gu`, `ha`, `hi`, `hy`, `ig`, `ka`, `kk`, `km`, `kn`, `lo`, `lv`, `mn`, `mr`, `ms`, `my`, `ne`, `pa`, `sw`, `tg`, `te`, `tl`, `uz`, `vi`, `yo`, `zu` |
| [Wikimedia data dump of Odia-language](https://dumps.wikimedia.org/orwiki/)| `or` |
| [Official Lojban Dictionary](https://www.lojban.org) | `jbo` |
| [Klingon Dictionary](http://klingonska.org/dict/dict.zdb) | `tlh` |

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


## Licensing

Each dictionary retains the license of its original source.

| Dataset | License |
|---------|---------|
| Most frequency lists | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| `ur` | [MIT](https://github.com/urduhack/urdu-words/blob/master/LICENSE) |
| `si` | [MIT](https://github.com/kasunw22/sinhala-para-dict/blob/main/LICENSE) |
| `tlh` | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| `af`, `am`, `as`, `az`, `be`, `br`, `eo`, `eu`, `gl`, `gu`, `ha`, `hi`, `hy`, `ig`, `ka`, `kk`, `km`, `kn`, `lo`, `lv`, `mn`, `mr`, `ms`, `my`, `ne`, `pa`, `sw`, `tg`, `te`, `tl`, `uz`, `vi`, `yo`, `zu`, `or` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `ta` | [MIT](https://github.com/vigneshwaran-chandrasekaran/tamil-language-words-list/blob/master/LICENSE) |
| `jbo` | Public Domain |
| `bn` | Public Domain (from [tahmid02016/bangla-wordlist](https://github.com/tahmid02016/bangla-wordlist)) |
| Repository code | MIT |

Please preserve the required attribution when redistributing or creating derivative works from these datasets.

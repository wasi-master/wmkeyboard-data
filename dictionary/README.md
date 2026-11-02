# Offline dictionaries

Whole English dictionaries for WM Keyboard's **Dictionary** tool, so it can
define ordinary words on a phone with no connection, and in the build that has
no internet permission at all. The vocabulary packs under [`../vocab/`](../vocab/)
know only their study lists' words; these know the language.

| File | Source | Headwords | Licence |
|---|---|---:|---|
| `en/oewn.wmdict.gz` | [Open English WordNet 2024](https://en-word.net/) | 78,928 | CC BY 4.0 |
| `en/wiktionary.wmdict.gz` | English Wiktionary via [kaikki.org](https://kaikki.org/dictionary/English/) | 64,778 | CC BY-SA 4.0 and GFDL |

Both hold single words only: no phrases ("ice cream"), no hyphenated
compounds. WordNet's pack keeps every single-word lemma and every sense; the
Wiktionary pack keeps the words the repo's English frequency list counts at
least 300 times or WordNet also has, three senses per part of speech and six
in all, and drops proper nouns and the senses Wiktionary tags obsolete,
archaic, rare or dated. Each pack is about 5 MB gzipped, 14 MB on the phone.

`<lang>/<lang>_wiktionary.wmdict.gz` holds another language's words with English
meanings, from English Wiktionary's entries for it through kaikki.org, under CC
BY-SA 4.0 and GFDL: 31 languages, from Basque (3,925 words) to Finnish (153,557).
`bn/bn_wiktionary.wmdict.gz` is the Bengali one. Forms from declension tables stay
out; a form Wiktionary gives its own entry is a redirect.

## Format

UTF-8 text, gzipped. The app inflates it once on install and then reads the
file in place: lines are sorted by key, so a look-up is a binary search over
byte offsets that touches a few kilobytes.

```
#wmdict	1
#id	oewn
#name	Open English WordNet
#lang	en
#license	CC-BY-4.0
#attribution	…
#source	english-wordnet-2024.xml.gz sha256:…
house	house	haʊs	noun␟a dwelling that serves as living quarters…␟he has a house on Cape Cod␟	verb␟…
mice	@mouse
```

A data line is `key TAB headword TAB ipa TAB sense TAB sense …`; the key is the
headword in lower case, and lines are sorted by the key's UTF-8 bytes, then the
headword (so "May" and "may" sit together). A sense is part of speech,
definition, example and `|`-separated synonyms, joined by U+001F, with a fifth
field of antonyms when there are some. A line `key TAB @lemma|lemma` is an
irregular form pointing at its headwords; the app undoes regular inflection
("houses", "running") with English rules of its own.

## Building

```
python3 scripts/build_dictionary_packs.py            # both
python3 scripts/build_dictionary_packs.py --check    # rebuild, fail if bytes differ
```

The sources live in `dictionary/cache/` (gitignored). Open English WordNet is
its release file, `english-wordnet-2024.xml.gz`. Kaikki's English extract is
520 MB gzipped and 3 GB inflated, so it is cut on the way in, to the words and
fields the pack can use, and only the cut is kept:

```
curl -sL https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz \
  | python3 scripts/build_dictionary_packs.py --prefilter
```

The language packs read kaikki.org directly and keep no copy, since the extracts
run to gigabytes and move with Wiktionary, so they have no `--check`:

```
python3 scripts/build_dictionary_packs.py --languages all     # or de,fr,...
```

Each pack's header records its source file's SHA-256, never a date, and gzip
is written with a zero mtime and no name, so the same source rebuilds the same
bytes.

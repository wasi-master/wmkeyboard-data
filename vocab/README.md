# Vocabulary packs

Downloadable vocabulary packs for **WM Keyboard**'s Vocabulary tool: GRE-level
word lists turned into small offline dictionaries. Each pack carries, per word,
the part of speech, IPA for US and UK accents, a stress respelling, up to three
senses per part of speech with an example and dated quotations, synonyms,
antonyms, the word family, hypernyms and hyponyms, etymology with the origin
chain and root, first attestation, inflected forms, hyphenation, rhymes, a
mnemonic, the lists the word appears in, and its **triggers** — plainer
synonyms that make the keyboard offer the harder word while you type
("hate" → *abhor*).

## Files

```
vocab/<lang>/<packId>.wmvocab.json.gz        the pack
vocab/<lang>/<packId>.tr.<code>.json.gz      translations into one language
vocab/sources/lists.json                     the word lists that become packs
vocab/sources/lists/*.json                   one plain JSON array per list
vocab/sources/word_details.json              mnemonics and stress respellings
vocab/translations/<code>.json               hand-written glosses (Bengali)
vocab/build-report.txt                       what the last build could not find
```

`packId` is the list id from `sources/lists.json` (`ws1`, `ws2`, `b333`, …).
A pack is gzip-compressed JSON in the app's own `.wmvocab.json` format — the
same file the app exports when you share a list you made yourself — so a pack
can also be dropped into an [addon repository](https://github.com/wasi-master/wmkeyboard-addon-repository)
as a `vocabulary` entry, or opened from a file manager.

### Pack format

```json
{
  "format": "wmkeyboard-vocab",
  "version": 1,
  "pack": {
    "id": "ws1", "name": "Word Smart 1", "langId": "en",
    "sourceId": "ws1", "built": "2026-09-07",
    "sources": [{"id": "ws1", "name": "Word Smart 1", "short": "WS1"}, "…"],
    "attribution": [{"name": "Wiktionary (via kaikki.org)", "license": "CC-BY-SA-3.0", "url": "…"}, "…"]
  },
  "words": [
    {
      "word": "abhor",
      "pos": ["verb"],
      "ipa": {"us": "/əbˈhɔɹ/", "uk": "/əbˈhɔː/"},
      "respelling": "ab-HOR",
      "audio": {"us": "https://upload.wikimedia.org/…/En-us-abhor.ogg.mp3"},
      "senses": [
        {"pos": "verb", "definition": "To regard (someone or something) as horrifying or detestable…",
         "example": "I absolutely abhor being stuck in traffic jams.",
         "quotations": [{"text": "…", "ref": "1975 March 21, Judy Klemesrud, “Vegetarianism…”"}],
         "synonyms": ["detest", "disdain", "loathe"], "tags": ["transitive"]}
      ],
      "synonyms": ["hate", "detest", "loathe"], "antonyms": ["love"],
      "family": {"derived": ["abhorrable"], "related": ["abhorrence", "abhorrent"]},
      "forms": ["abhors", "abhorring", "abhorred"],
      "etymology": "From Middle English abhorren, borrowed from Middle French abhorrer, from Latin abhorreō…",
      "origin": [{"lang": "Middle English", "word": "abhorren"}, {"lang": "Latin", "word": "abhorreō"}],
      "root": "Proto-Indo-European *ǵʰers-",
      "attested": "1449",
      "rhymes": "-ɔː(ɹ)",
      "mnemonic": "Ab + horror: to have absolute horror toward something.",
      "sources": ["ws1", "b1100", "sn1000"],
      "triggers": [{"w": "hate", "forms": ["hated", "hates", "hating"], "gap": 2.7}]
    }
  ]
}
```

Every field but `word` is optional and omitted when empty. `triggers[].gap`
is the Zipf-frequency gap between the trigger and the word; the app's
"nudge sensitivity" setting is a threshold on it.

A translation sidecar maps each word to up to three glosses, with
romanisations when Wiktionary gives them:

```json
{"abhor": {"w": ["ატել"], "r": ["atel"]}, "abase": {"w": ["…"]}}
```

## Rebuilding

```bash
pip install -r vocab/requirements.txt
python3 -c "import nltk; [nltk.download(p) for p in ('wordnet', 'cmudict', 'stopwords')]"
python3 scripts/build_vocab_packs.py --lists ws1,ws2,b333
python3 scripts/build_vocab_packs.py --check      # verify without writing
python3 -m pytest scripts/tests
```

Wiktionary entries are fetched one word at a time from
[kaikki.org](https://kaikki.org/dictionary/English/) and cached under
`vocab/cache/` (gitignored), so a rerun costs no network. Read
`vocab/build-report.txt` after a build: it lists the words Wiktionary did not
have (WordNet fills their definitions), the words with no IPA, and the triggers
that pointed at more words than the fan-out cap allows.

Trigger rule: a synonym qualifies when it is one alphabetic token of three or
more letters, not a stopword, not itself in any of the lists, and its Zipf
frequency is at least 3.5, at least 1.0 above the word's, and at most 6.0 (so
"get" and "good" never nudge). Inflected forms come from Wiktionary's own
tables, or from plain English rules when the trigger has no entry.

## Sources and licences

| Source | Used for | Licence |
|---|---|---|
| [Wiktionary](https://en.wiktionary.org/) via [kaikki.org](https://kaikki.org/) | definitions, IPA, examples, quotations, synonyms, antonyms, family, etymology, forms, translations, audio links | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| [WordNet 3.0](https://wordnet.princeton.edu/) | definitions and synonyms where Wiktionary has none | [WordNet License](https://wordnet.princeton.edu/license-and-commercial-use) |
| [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict) | IPA where Wiktionary has none | BSD 2-Clause |
| [FrequencyWords](https://github.com/hermitdave/FrequencyWords) via `data/en/en_full.txt.gz` | Zipf-scale word frequencies for the trigger rule | CC BY-SA 4.0 |
| [wordcheck](https://github.com/wasi-master/wordcheck) | the word lists, mnemonics and respellings | MIT |

The word lists name the study guides they were compiled from (Word Smart,
Barron's, Magoosh, …). Only the words themselves are taken; no definition or
other text from those books is reproduced. The packs' definitions are
Wiktionary's and are therefore share-alike: keep the `attribution` block when
you redistribute a pack.

"""Unit tests for the pure helpers in build_vocab_packs.py.

Run from the repository root:
    python3 -m pytest scripts/tests
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_vocab_packs as b  # noqa: E402

ABHOR = [
    {
        "word": "abhor",
        "pos": "verb",
        "lang_code": "en",
        "forms": [
            {"form": "abhors", "tags": ["present", "singular", "third-person"]},
            {"form": "abhorring", "tags": ["participle", "present"]},
            {"form": "abhorred", "tags": ["participle", "past"]},
            {"form": "abhorred", "tags": ["past"]},
            {"form": "en-verb", "tags": ["table-tags"]},
        ],
        "sounds": [
            {"tags": ["Received-Pronunciation"], "ipa": "/əbˈhɔː/"},
            {"tags": ["Received-Pronunciation"], "ipa": "/əbˈɔː/"},
            {"audio": "en-uk-abhor.ogg", "tags": ["UK"], "mp3_url": "https://x/En-uk-abhor.ogg.mp3"},
            {"tags": ["General-American"], "ipa": "/əbˈhɔɹ/"},
            {"audio": "en-us-abhor.ogg", "tags": ["US"], "mp3_url": "https://x/En-us-abhor.ogg.mp3"},
            {"rhymes": "-ɔː(ɹ)"},
        ],
        "synonyms": [{"sense": "to regard as horrifying", "word": "hate"}],
        "derived": [{"word": "abhorrable"}, {"word": "abhorration"}],
        "related": [{"word": "abhorred"}, {"word": "abhorrence"}, {"word": "abhorrent"}],
        "etymology_text": "First attested in 1449, from Middle English abhorren, borrowed from Middle French abhorrer, from Latin abhorreō (“shrink away from in horror”), from ab- (“from”) + horreō (“stand aghast, bristle with fear”).",
        "etymology_templates": [
            {"name": "root", "args": {"1": "en", "2": "ine-pro", "3": "*ǵʰers-"}, "expansion": ""},
            {"name": "inh", "args": {"1": "en", "2": "enm", "3": "abhorren"}, "expansion": "Middle English abhorren"},
            {"name": "der", "args": {"1": "en", "2": "frm", "3": "abhorrer"}, "expansion": "Middle French abhorrer"},
            {"name": "der", "args": {"1": "en", "2": "la", "3": "abhorreō"}, "expansion": "Latin abhorreō (“shrink away from in horror”)"},
            {"name": "prefix", "args": {"1": "en", "2": "ab", "3": "horreō"}, "expansion": "ab- + horreō"},
        ],
        "translations": [
            {"lang": "Hindi", "code": "hi", "sense": "to regard with horror", "word": "घृणा करना"},
            {"lang": "Armenian", "code": "hy", "sense": "to regard with horror", "roman": "atel", "word": "ատել"},
            {"lang": "Spanish", "code": "es", "sense": "to regard with horror", "word": "aborrecer"},
            {"lang": "Spanish", "code": "es", "sense": "to regard with horror", "word": "detestar"},
            {"lang": "Spanish", "code": "es", "sense": "to regard with horror", "word": "abominar"},
            {"lang": "Spanish", "code": "es", "sense": "to regard with horror", "word": "aborrir"},
        ],
        "senses": [
            {
                "glosses": ["To regard (someone or something) as horrifying or detestable; to feel great repugnance toward."],
                "tags": ["transitive"],
                "synonyms": [{"word": "detest"}, {"word": "disdain"}, {"word": "loathe"}],
                "examples": [
                    {"text": "I absolutely abhor being stuck in traffic jams.", "type": "example"},
                    {
                        "text": "Let loue bee without dissimulation: abhorre that which is euill.",
                        "ref": "1611, The Holy Bible, […] (King James Version), London: […] Robert Barker, […], →OCLC, Romans 12:9:",
                        "type": "quotation",
                    },
                    {
                        "text": "Many vegetarians abhor the thought of killing animals.",
                        "ref": "1975 March 21, Judy Klemesrud, “Vegetarianism: Growing Way of Life, Especially Among the Young”, in The New York Times, →ISSN, archived from the original on 02 Nov 2025:",
                        "type": "quotation",
                    },
                ],
                "attestations": [{"date": "First attested from around (1350 to 1470).", "references": []}],
            },
            {
                "glosses": ["To fill with horror or disgust."],
                "tags": ["impersonal", "obsolete", "transitive"],
            },
            {"glosses": ["To turn aside or avoid; to keep away from; to reject."], "tags": ["transitive"]},
            {"glosses": ["To protest against; to reject solemnly."], "tags": ["transitive"]},
            {"glosses": ["To feel horror, disgust, or dislike (towards); to be contrary or averse (to)."], "tags": ["intransitive"]},
        ],
    }
]


def test_normalize_word():
    assert b.normalize_word("Abase") == "abase"
    assert b.normalize_word("  Bona Fide ") == "bona fide"
    assert b.normalize_word("Ad-lib") == "ad-lib"
    assert b.normalize_word("cat's paw") == "cat's paw"
    assert b.normalize_word("buff (n)") is None
    assert b.normalize_word("12") is None
    assert b.normalize_word("a") is None


def test_normalize_pos():
    assert b.normalize_pos("adj") == "adjective"
    assert b.normalize_pos("verb") == "verb"
    assert b.normalize_pos("name") is None
    assert b.normalize_pos(None) is None


def test_truncate_and_sentence_cut():
    assert b.truncate("short", 10) == "short"
    long = "word " * 60
    cut = b.truncate(long, 40)
    assert len(cut) <= 40 and cut.endswith("…")
    text = "One sentence here that is long enough. Second sentence follows. Third one."
    assert b.sentence_cut(text, 10, 45) == "One sentence here that is long enough."
    assert b.sentence_cut("tiny.", 10, 45) == "tiny."


def test_clean_etymology_strips_attestation_prefix():
    out = b.clean_etymology(ABHOR[0]["etymology_text"])
    assert out.startswith("From Middle English abhorren")
    assert len(out) <= b.MAX_ETYMOLOGY


def test_attested_year():
    assert b.attested_year(ABHOR[0]["etymology_text"], []) == "1449"
    assert b.attested_year("", ABHOR[0]["senses"]) == "c. 1350–1470"
    assert b.attested_year("", []) is None


def test_clean_ref():
    ref = "1975 March 21, Judy Klemesrud, “Vegetarianism: Growing Way of Life, Especially Among the Young”, in The New York Times, →ISSN, archived"
    out = b.clean_ref(ref)
    assert out.startswith("1975 March 21, Judy Klemesrud, “Vegetarianism")
    assert "→ISSN" not in out and "archived" not in out
    assert len(out) <= b.MAX_REF


def test_arpabet_to_ipa():
    assert b.arpabet_to_ipa(["AE0", "B", "HH", "AO1", "R"]) == "/æbˈhɔɹ/"
    assert b.arpabet_to_ipa(["AH0", "L", "AE1", "K", "R", "AH0", "T", "IY0"]) == "/əˈlækɹəti/"


def test_inflect():
    assert b.inflect("hate") == ["hates", "hated", "hating"]
    assert b.inflect("carry") == ["carries", "carried", "carrying"]
    assert b.inflect("wish") == ["wishes", "wished", "wishing"]
    assert b.inflect("agree") == ["agrees", "agreed", "agreeing"]


def test_is_trigger():
    union = {"abhor", "loathe"}
    stop = {"the", "very"}
    assert b.is_trigger("hate", "abhor", 5.3, 2.6, union, stop, set())
    assert not b.is_trigger("loathe", "abhor", 3.6, 2.6, union, stop, set())  # in a list
    assert not b.is_trigger("detest", "abhor", 3.2, 2.6, union, stop, set())  # under the floor
    assert not b.is_trigger("get", "obtain", 6.4, 4.5, union, stop, set())   # over the ceiling
    assert not b.is_trigger("the", "abhor", 7.0, 2.6, union, stop, set())    # stopword
    assert not b.is_trigger("abhorred", "abhor", 5.0, 2.6, union, stop, {"abhorred"})
    assert not b.is_trigger("give up", "abandon", 5.0, 3.0, union, stop, set())


def test_kaikki_forms_skips_tables_and_dupes():
    assert b.kaikki_forms(ABHOR, "abhor") == ["abhors", "abhorring", "abhorred"]


def test_kaikki_sounds_by_accent():
    ipa, audio, enpr, rhyme = b.kaikki_sounds(ABHOR)
    assert ipa == {"uk": "/əbˈhɔː/", "us": "/əbˈhɔɹ/"}
    assert audio == {"uk": "https://x/En-uk-abhor.ogg.mp3", "us": "https://x/En-us-abhor.ogg.mp3"}
    assert enpr is None
    assert rhyme == "-ɔː(ɹ)"


def test_kaikki_sounds_untagged_ipa_counts_as_us():
    ipa, _, _, _ = b.kaikki_sounds([{"sounds": [{"ipa": "/əˈlæk.rə.ti/"}, {"ipa": "/x/", "tags": ["UK"]}]}])
    assert ipa == {"us": "/əˈlæk.rə.ti/", "uk": "/x/"}


def test_kaikki_senses_prunes_and_caps():
    pos, senses = b.kaikki_senses(ABHOR)
    assert pos == ["verb"]
    assert len(senses) == b.MAX_SENSES_PER_POS
    first = senses[0]
    assert first["definition"].startswith("To regard (someone or something)")
    assert first["example"] == "I absolutely abhor being stuck in traffic jams."
    assert [q["ref"][:4] for q in first["quotations"]] == ["1975", "1611"]
    assert first["synonyms"] == ["detest", "disdain", "loathe"]
    assert first["tags"] == ["transitive"]
    assert all("obsolete" not in s.get("tags", []) for s in senses)
    assert "To fill with horror or disgust." not in [s["definition"] for s in senses]


def test_kaikki_origin_and_root():
    origin, root = b.kaikki_origin(ABHOR)
    assert origin == [
        {"lang": "Middle English", "word": "abhorren"},
        {"lang": "Middle French", "word": "abhorrer"},
        {"lang": "Latin", "word": "abhorreō"},
    ]
    assert root == "Proto-Indo-European *ǵʰers-"


def test_kaikki_translations_groups_and_caps():
    tr = b.kaikki_translations(ABHOR)
    assert tr["hi"] == {"w": ["घृणा करना"]}
    assert tr["hy"] == {"w": ["ատել"], "r": ["atel"]}
    assert tr["es"] == {"w": ["aborrecer", "detestar", "abominar"]}


def test_kaikki_relations():
    assert b.kaikki_relations(ABHOR, "derived") == ["abhorrable", "abhorration"]
    assert b.kaikki_relations(ABHOR, "hyponyms") == []


def test_fanout_cap_keeps_largest_gaps():
    words = [
        {"word": f"w{i}", "triggers": [{"w": "big", "forms": [], "gap": float(i)}]}
        for i in range(b.TRIGGER_FANOUT + 3)
    ]
    report: list[str] = []
    b.apply_fanout_cap(words, report)
    kept = [w["word"] for w in words if "triggers" in w]
    assert len(kept) == b.TRIGGER_FANOUT
    assert "w0" not in kept and f"w{b.TRIGGER_FANOUT + 2}" in kept
    assert report and report[0].startswith("    big:")


def test_gzip_is_deterministic():
    payload = b.encode_json({"a": 1, "b": [1, 2]})
    assert b.gzip_bytes(payload) == b.gzip_bytes(payload)
    assert json.loads(payload) == {"a": 1, "b": [1, 2]}


def test_strip_built():
    data = b.gzip_bytes(b.encode_json({"pack": {"built": "2026-09-07"}}))
    assert b'"built":""' in b.strip_built(data)


def test_thesaurus_imports_are_dropped_from_senses():
    sense = {
        "glosses": ["To punish or reprimand someone severely."],
        "synonyms": [{"word": "rebuke"}, {"word": "rate", "source": "Thesaurus:criticize"}],
        "antonyms": [{"word": "praise"}, {"word": "flatter", "source": "Thesaurus:praise"}],
    }
    parsed = b.parse_sense(sense, "verb")
    assert parsed["synonyms"] == ["rebuke"]
    assert parsed["antonyms"] == ["praise"]

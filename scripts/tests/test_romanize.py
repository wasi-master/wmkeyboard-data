"""Romanisation tests; run from the repository root with python3 -m pytest scripts/tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import romanize as r  # noqa: E402


def test_bengali_is_spelt_the_avro_way():
    assert r.romanize_bengali("ঘৃণা") == "ghrina"
    assert r.romanize_bengali("ভালো") == "bhalo"
    assert r.romanize_bengali("শব্দ") == "shobdo"
    assert r.romanize_bengali("মন") == "mon"
    assert r.romanize_bengali("দুঃখ") == "dukkho"
    assert r.romanize_bengali("ব্যক্তি") == "byokti"
    assert r.romanize_bengali("সিংহাসন ত্যাগ করা") == "singhason tyag kora"
    assert r.romanize_bengali("রং") == "rong"
    # Decomposed nukta forms read the same as precomposed ones.
    assert r.romanize_bengali("হেয়") == r.romanize_bengali("হেয়") == "hey"
    assert r.romanize_bengali("১২") == "12"


def test_cyrillic_table():
    assert r.romanize_cyrillic("ненавидеть") == "nenavidet"
    assert r.romanize_cyrillic("Ђорђе") == "Djordje"
    assert r.romanize_cyrillic("Київ") == "Kiyiv"


def test_dispatch_leaves_latin_alone():
    assert r.romanize("abhor") == ""
    assert r.romanize("Việt Nam") == ""
    assert r.romanize("ঘৃণা") == "ghrina"
    assert r.romanize("ненавидеть") == "nenavidet"


def test_fill_keeps_lists_aligned():
    table = {
        "abase": {"w": ["হেয় করা", "অপমানিত করা"]},
        "hate": {"w": ["ненавидеть", "hate"], "r": ["", ""]},
        "plain": {"w": ["odiar"]},
    }
    assert r.fill_romanizations(table) == 3
    assert table["abase"]["r"] == ["hey kora", "opomanit kora"]
    assert table["hate"]["r"] == ["nenavidet", ""]
    assert "r" not in table["plain"]
    # A second pass changes nothing.
    assert r.fill_romanizations(table) == 0

"""Tests for Persian script normalization in normalize_data.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import normalize_data as nd


def test_arabic_yeh_to_persian_yeh():
    # U+064A (ي) -> U+06CC (ی)
    assert nd.normalize_persian_script("ميکني") == "میکنی"
    assert nd.normalize_persian_script("اين") == "این"
    assert nd.normalize_persian_script("چيزي") == "چیزی"


def test_arabic_kaf_to_persian_keheh():
    # U+0643 (ك) -> U+06A9 (ک)
    assert nd.normalize_persian_script("كتاب") == "کتاب"
    assert nd.normalize_persian_script("كص") == "کص"


def test_alef_maksura_to_persian_yeh():
    # U+0649 (ى) -> U+06CC (ی)
    assert nd.normalize_persian_script("حتى") == "حتی"
    assert nd.normalize_persian_script("موسى") == "موسی"


def test_tatweel_stripped():
    # U+0640 (ـ) stripped
    assert nd.normalize_persian_script("افـتـخـار") == "افتخار"
    assert nd.normalize_persian_script("تـقـديـم") == "تقدیم"
    assert nd.normalize_persian_script("کنـه") == "کنه"
    assert nd.normalize_persian_script("ـ") == ""


def test_persian_already_correct_unchanged():
    assert nd.normalize_persian_script("سلام") == "سلام"
    assert nd.normalize_persian_script("کتاب") == "کتاب"
    assert nd.normalize_persian_script("یک") == "یک"
    assert nd.normalize_persian_script("میکنی") == "میکنی"

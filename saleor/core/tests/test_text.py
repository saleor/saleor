from ..text import strip_accents


def test_strip_accents_removes_diacritics():
    assert strip_accents("Magnésium") == "Magnesium"


def test_strip_accents_removes_multiple_diacritics():
    assert strip_accents("café") == "cafe"


def test_strip_accents_removes_diaeresis():
    assert strip_accents("naïve") == "naive"


def test_strip_accents_preserves_ascii():
    assert strip_accents("hello world") == "hello world"


def test_strip_accents_empty_string():
    assert strip_accents("") == ""

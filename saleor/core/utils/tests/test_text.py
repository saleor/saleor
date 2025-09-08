from ..text import safe_truncate


def test_safe_truncate():
    assert safe_truncate("Hello, world!", 5) == "Hell…"
    assert safe_truncate("Hello, world!", 20) == "Hello, world!"
    assert safe_truncate("Hello, 世界!", 9) == "Hello, 世…"
    assert safe_truncate("Hello, 世界!", 15) == "Hello, 世界!"
    assert safe_truncate("Hello, world!", 1) == "…"


def test_safe_truncate_with_combining_characters():
    # characters at positions 6 and 7 are combining marks for character at position 5
    # so we want to either preserve all three or skip all three
    assert len(safe_truncate("مُـحمَّـد", 7)) == 7
    assert len(safe_truncate("مُـحمَّـد", 6)) == 4

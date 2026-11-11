from ..text import safe_truncate


def test_safe_truncate():
    assert safe_truncate("Hello, world!", 5) == "Hell…"
    assert safe_truncate("Hello, world!", 20) == "Hello, world!"
    assert safe_truncate("Hello, 世界!", 15) == "Hello, 世界!"
    assert safe_truncate("Hello, world!", 1) == "…"


def test_safe_truncate_with_combining_characters():
    # characters at positions 6 and 7 are combining marks for character at position 5
    # so we want to either preserve all three or skip all three
    # keeping all three needs 7 characters plus the ellipsis, so all three are cut
    assert safe_truncate("مُـحمَّـد", 7) == "مُـح…"
    assert safe_truncate("مُـحمَّـد", 6) == "مُـح…"


def test_safe_truncate_keeps_combining_mark_with_its_base():
    # "q\u0303" has no precomposed form, so NFC keeps the tilde as a separate mark
    assert safe_truncate("abq\u0303zz", 4) == "ab…"
    assert safe_truncate("abq\u0303zz", 5) == "abq\u0303…"
    assert safe_truncate("abq\u0303zz", 3) == "ab…"

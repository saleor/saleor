from pytest import raises

from ..quoted_or_list import quoted_or_list


def test_does_not_accept_an_empty_list():
    with raises(StopIteration):
        quoted_or_list([])


def test_returns_single_quoted_item():
    assert quoted_or_list(["A"]) == '"A"'


def test_returns_two_item_list():
    assert quoted_or_list(["A", "B"]) == '"A" or "B"'


def test_returns_comma_separated_many_item_list():
    assert quoted_or_list(["A", "B", "C"]) == '"A", "B" or "C"'


def test_limits_to_five_items():
    assert quoted_or_list(["A", "B", "C", "D", "E", "F"]) == '"A", "B", "C", "D" or "E"'

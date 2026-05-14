import pytest
from graphql.language.ast import IntValue, ObjectValue, StringValue

from ..fields import JSONString


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('{"a": 1}', {"a": 1}),
        ("[1, 2, 3]", [1, 2, 3]),
        ('"text"', "text"),
        ("null", None),
    ],
)
def test_parse_value_valid_string(value, expected):
    assert JSONString.parse_value(value) == expected


@pytest.mark.parametrize(
    "invalid_value",
    [
        {"a": 1},
        [1, 2, 3],
        123,
        None,
        "{not json}",
    ],
)
def test_parse_value_invalid_returns_none(invalid_value):
    assert JSONString.parse_value(invalid_value) is None


def test_parse_literal_valid_string():
    node = StringValue(value='{"a": 1}')
    assert JSONString.parse_literal(node) == {"a": 1}


@pytest.mark.parametrize(
    "invalid_node",
    [
        StringValue(value="{not json}"),
        IntValue(value="1"),
        ObjectValue(fields=[]),
    ],
)
def test_parse_literal_invalid_returns_none(invalid_node):
    assert JSONString.parse_literal(invalid_node) is None

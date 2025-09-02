import decimal

import pytest
from graphql.language.ast import FloatValue, IntValue, ObjectValue, StringValue

from ..scalars import Decimal, PositiveDecimal, PositiveInt

# Decimals


@pytest.mark.parametrize("invalid_value", ["NaN", "-Infinity", "1e-9999999", "-", "x"])
def test_decimal_scalar_invalid_value(invalid_value):
    result = Decimal.parse_value(invalid_value)
    assert result is None


@pytest.mark.parametrize(
    ("valid_node", "expect"),
    [
        (FloatValue(value="1.0"), 1),
        (IntValue(value="1"), 1),
        (IntValue(value="0"), 0),
        (IntValue(value="-5"), -5),
    ],
)
def test_decimal_scalar_valid_literal(valid_node, expect):
    result = Decimal.parse_literal(valid_node)
    assert result == decimal.Decimal(expect)


@pytest.mark.parametrize(
    "invalid_node",
    [
        StringValue(value="1.0"),
        ObjectValue(fields=[]),
    ],
)
def test_decimal_scalar_invalid_literal(invalid_node):
    result = Decimal.parse_literal(invalid_node)
    assert result is None


# PositiveDecimal


@pytest.mark.parametrize(
    "node",
    [
        FloatValue(value="1.0"),
        IntValue(value="1"),
    ],
)
def test_positive_decimal_scalar_valid_literal(node):
    result = PositiveDecimal.parse_literal(node)

    assert result == decimal.Decimal(1)


@pytest.mark.parametrize(
    "node",
    [
        FloatValue(value="0.0"),
        IntValue(value="0"),
    ],
)
def test_positive_decimal_scalar_valid_literal_zero(node):
    result = PositiveDecimal.parse_literal(node)

    assert result == decimal.Decimal(0)


@pytest.mark.parametrize("invalid_value", ["NaN", "-Infinity", "1e-9999999", "-1"])
def test_positive_decimal_scalar_invalid_value(invalid_value):
    result = PositiveDecimal.parse_value(invalid_value)
    assert result is None


def test_positive_decimal_scalar_valid_value_zero():
    result = PositiveDecimal.parse_value("0")

    assert result == decimal.Decimal(0)


@pytest.mark.parametrize(
    "node",
    [
        FloatValue(value="-1.0"),
        IntValue(value="-1"),
    ],
)
def test_positive_decimal_scalar_invalid_literal(node):
    result = PositiveDecimal.parse_literal(node)

    assert result is None


# PositiveInt


@pytest.mark.parametrize(
    "valid_node",
    [
        IntValue(value="1"),
        IntValue(value="10"),
        IntValue(value="999"),
    ],
)
def test_positive_int_scalar_valid_literal(valid_node):
    result = PositiveInt.parse_literal(valid_node)
    assert result == int(valid_node.value)


@pytest.mark.parametrize(
    "invalid_node",
    [
        IntValue(value="0"),
        IntValue(value="-1"),
        FloatValue(value="1.0"),
        StringValue(value="10"),
        ObjectValue(fields=[]),
    ],
)
def test_positive_int_scalar_invalid_literal(invalid_node):
    result = PositiveInt.parse_literal(invalid_node)
    assert result is None


@pytest.mark.parametrize(
    "valid_value",
    ["1", "10", "999"],
)
def test_positive_int_scalar_valid_value(valid_value):
    result = PositiveInt.parse_value(valid_value)
    assert result == int(valid_value)


@pytest.mark.parametrize(
    "invalid_value",
    ["0", "-1", "NaN", "abc"],
)
def test_positive_int_scalar_invalid_value(invalid_value):
    result = PositiveInt.parse_value(invalid_value)
    assert result is None

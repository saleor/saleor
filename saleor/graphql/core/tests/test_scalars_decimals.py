import decimal

import pytest
from graphql import FloatValueNode, IntValueNode, ObjectValueNode, StringValueNode

from ..scalars import Decimal, PositiveDecimal

# Decimals


@pytest.mark.parametrize("invalid_value", ["NaN", "-Infinity", "1e-9999999", "-", "x"])
def test_decimal_scalar_invalid_value(invalid_value):
    result = Decimal.parse_value(invalid_value)
    assert result is None


@pytest.mark.parametrize(
    ("valid_node", "expect"),
    [
        (FloatValueNode(value="1.0"), 1),
        (IntValueNode(value="1"), 1),
        (IntValueNode(value="0"), 0),
        (IntValueNode(value="-5"), -5),
    ],
)
def test_decimal_scalar_valid_literal(valid_node, expect):
    result = Decimal.parse_literal(valid_node)
    assert result == decimal.Decimal(expect)


@pytest.mark.parametrize(
    "invalid_node",
    [
        StringValueNode(value="1.0"),
        ObjectValueNode(fields=[]),
    ],
)
def test_decimal_scalar_invalid_literal(invalid_node):
    result = Decimal.parse_literal(invalid_node)
    assert result is None


# PositiveDecimal


@pytest.mark.parametrize(
    "node",
    [
        FloatValueNode(value="1.0"),
        IntValueNode(value="1"),
    ],
)
def test_positive_decimal_scalar_valid_literal(node):
    result = PositiveDecimal.parse_literal(node)

    assert result == decimal.Decimal(1)


@pytest.mark.parametrize(
    "node",
    [
        FloatValueNode(value="0.0"),
        IntValueNode(value="0"),
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
        FloatValueNode(value="-1.0"),
        IntValueNode(value="-1"),
    ],
)
def test_positive_decimal_scalar_invalid_literal(node):
    result = PositiveDecimal.parse_literal(node)

    assert result is None

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from ..manifest_validations import DecimalTest, FloatTest, Manifest


def test_pydantic():
    with pytest.raises(ValidationError):
        Manifest(id="test.id", value="to nie bool")


def test_pydantic_v2():
    with pytest.raises(ValidationError):
        Manifest.parse_raw('{"id": "test.id", "value": "to nie bool"}')


def test_decimal():
    price = Decimal("0." + "3" * 250)
    json_str = f'{{ "price": {price}}}'
    d = DecimalTest.parse_raw(json_str)
    assert d.price == price


def test_float():
    price = Decimal("0." + "3" * 250)
    json_str = f'{{ "price": {price}}}'
    d = FloatTest.parse_raw(json_str)
    assert d.price == float(price)

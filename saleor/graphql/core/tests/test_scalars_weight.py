import pytest

from ..scalars import WeightScalar


@pytest.mark.parametrize(
    "value",
    [
        {"unit": "kg", "value": None},
        {"unit": "g", "value": None},
        {"unit": "lb", "value": None},
        {"unit": "oz", "value": None},
    ],
)
def test_weight_scalar_parse_value_with_none_value(value):
    result = WeightScalar.parse_value(value)
    assert result is None

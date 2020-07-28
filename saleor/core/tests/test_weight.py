import pytest
from measurement.measures import Weight

from ..weight import (
    WeightUnits,
    convert_weight,
    convert_weight_to_default_weight_unit,
    get_default_weight_unit,
)


def test_convert_weight():
    # given
    weight = Weight(kg=1)
    expected_result = Weight(g=1000)

    # when
    result = convert_weight(weight, WeightUnits.GRAM)

    # then
    assert result == expected_result


def test_get_default_weight_unit(site_settings):
    # when
    result = get_default_weight_unit()

    # then
    assert result == site_settings.default_weight_unit


@pytest.mark.parametrize(
    "default_weight_unit, expected_value",
    [
        (WeightUnits.KILOGRAM, Weight(kg=1)),
        (WeightUnits.GRAM, Weight(g=1000)),
        (WeightUnits.POUND, Weight(lb=2.205)),
        (WeightUnits.OUNCE, Weight(oz=35.274)),
    ],
)
def test_convert_weight_to_default_weight_unit(
    default_weight_unit, expected_value, site_settings
):
    # given
    site_settings.default_weight_unit = default_weight_unit
    site_settings.save(update_fields=["default_weight_unit"])

    # when
    result = convert_weight_to_default_weight_unit(Weight(kg=1))

    # then
    assert result == expected_value

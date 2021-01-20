import pytest
from measurement.measures import Weight

from ..units import WeightUnits
from ..weight import (
    convert_weight,
    convert_weight_to_default_weight_unit,
    get_default_weight_unit,
)


def test_convert_weight():
    # given
    weight = Weight(kg=1)
    expected_result = Weight(g=1000)

    # when
    result = convert_weight(weight, WeightUnits.G)

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
        (WeightUnits.KG, Weight(kg=1)),
        (WeightUnits.G, Weight(g=1000)),
        (WeightUnits.LB, Weight(lb=2.205)),
        (WeightUnits.OZ, Weight(oz=35.274)),
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

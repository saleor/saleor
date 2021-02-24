from unittest.mock import Mock, patch

import pytest

from .. import PostalCodeRuleInclusionType
from ..postal_codes import (
    check_postal_code_in_range,
    is_shipping_method_applicable_for_postal_code,
)


@pytest.mark.parametrize(
    "code, start, end, in_range",
    [
        ["BH3 2BC", "BH2 1AA", "BH4 9ZZ", True],
        ["BH20 2BC", "BH2 1AA", "BH4 9ZZ", False],
        ["BH16 7HF", "BH16 7HA", "BH16 7HG", True],
        ["BH16 7HA", "BH16 7HA", "BH16 7HB", True],
        ["BH17 7HF", "BH16 7HA", "BH17 7HG", True],
        ["BH15 7HF", "BH10 7HA", "BH20 7HG", True],
        ["BH16 7HF", "BH16 7HA", None, True],
        ["BH16 7HA", "BH16 7HA", None, True],
        ["BH16 7HZ", "BH16 7HA", "BH16 7HG", False],
        ["BH16 7HB", "BH16 7HC", "BH16 7HD", False],
        ["BH16 7HB", "BH16 7HC", None, False],
    ],
)
def test_check_postal_code_for_uk(code, start, end, in_range):
    assert check_postal_code_in_range("GB", code, start, end) is in_range


@pytest.mark.parametrize(
    "code, start, end, in_range",
    [
        ["IM16 7HF", "IM16 7HA", "IM16 7HG", True],  # Isle of Man
        ["IM16 7HZ", "IM16 7HA", "IM16 7HG", False],
        ["GY16 7HF", "GY16 7HA", "GY16 7HG", True],  # Jersey
        ["GY16 7HZ", "GY16 7HA", "GY16 7HG", False],
        ["GG16 7HF", "GG16 7HA", "GG16 7HG", True],  # Guernsey
        ["GG16 7HZ", "GG16 7HA", "GG16 7HG", False],
    ],
)
def test_check_postal_code_for_uk_fallbacks(code, start, end, in_range):
    assert check_postal_code_in_range("GB", code, start, end) is in_range


@pytest.mark.parametrize(
    "code, start, end, in_range",
    [
        ["A65 2F0A", "A65 2F0A", "A65 2F0A", True],
        ["A65 2F0B", "A65 2F0A", "A65 2F0C", True],
        ["A65 2F0B", "A65 2F0C", "A65 2F0D", False],
    ],
)
def test_check_postal_code_for_ireland(code, start, end, in_range):
    assert check_postal_code_in_range("IE", code, start, end) is in_range


@pytest.mark.parametrize(
    "code, start, end, in_range",
    [
        ["64-620", "50-000", "65-000", True],
        ["64-620", "64-200", "64-650", True],
        ["64-620", "63-200", "63-650", False],
    ],
)
def test_check_postal_code_for_other_countries(code, start, end, in_range):
    assert check_postal_code_in_range("PL", code, start, end) is in_range


@pytest.mark.parametrize(
    "country, code, start, end",
    [
        ["IM", "IM16 7HF", "IM16 7HA", "IM16 7HG"],
        ["GG", "GG16 7HF", "GG16 7HA", "GG16 7HG"],
        ["JE", "GY16 7HZ", "GY16 7HA", "GY16 7HG"],
    ],
)
@patch("saleor.shipping.postal_codes.check_uk_postal_code")
def test_check_uk_islands_follow_uk_check(check_uk_mock, country, code, start, end):
    """Check if Isle of Man, Guernsey, Jersey triggers check_uk_postal_code method."""
    assert check_postal_code_in_range(country, code, start, end)
    check_uk_mock.assert_called_once_with(code, start, end)


@pytest.mark.parametrize(
    "rules_result, is_applicable",
    [
        [{}, True],
        [{Mock(inclusion_type=PostalCodeRuleInclusionType.INCLUDE): True}, True],
        [{Mock(inclusion_type=PostalCodeRuleInclusionType.INCLUDE): False}, False],
        [{Mock(inclusion_type=PostalCodeRuleInclusionType.EXCLUDE): True}, False],
        [{Mock(inclusion_type=PostalCodeRuleInclusionType.EXCLUDE): False}, True],
        [
            {
                Mock(inclusion_type=PostalCodeRuleInclusionType.INCLUDE): True,
                Mock(inclusion_type=PostalCodeRuleInclusionType.INCLUDE): False,
            },
            True,
        ],
        [
            {
                Mock(inclusion_type=PostalCodeRuleInclusionType.EXCLUDE): True,
                Mock(inclusion_type=PostalCodeRuleInclusionType.EXCLUDE): False,
            },
            False,
        ],
        [
            {
                Mock(inclusion_type=PostalCodeRuleInclusionType.EXCLUDE): True,
                Mock(inclusion_type=PostalCodeRuleInclusionType.INCLUDE): True,
            },
            False,
        ],
    ],
)
@patch("saleor.shipping.postal_codes.check_shipping_method_for_postal_code")
def test_is_shipping_method_applicable_for_postal_code(
    check_shipping_method_mock, rules_result, is_applicable
):
    check_shipping_method_mock.return_value = rules_result
    assert (
        is_shipping_method_applicable_for_postal_code(Mock(), Mock()) is is_applicable
    )

from unittest.mock import patch

import pytest

from ...checkout.fetch import CollectionPointInfo
from ..utils import (
    _get_country_code_for_checkout_for_tax_calculation,
    get_charge_taxes,
    get_display_gross_prices,
    get_tax_country,
)


def test_get_display_gross_prices(channel_USD):
    # given
    tax_configuration = channel_USD.tax_configuration
    tax_configuration.display_gross_prices = True
    tax_configuration.save(update_fields=["charge_taxes"])
    country_exception = tax_configuration.country_exceptions.first()
    country_exception.display_gross_prices = False
    country_exception.save(update_fields=["charge_taxes"])

    # then
    assert (
        get_display_gross_prices(tax_configuration, None)
        == tax_configuration.display_gross_prices
    )
    assert (
        get_display_gross_prices(tax_configuration, country_exception)
        == country_exception.display_gross_prices
    )


def test_get_charge_taxes(channel_USD):
    # given
    tax_configuration = channel_USD.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes"])
    country_exception = tax_configuration.country_exceptions.first()
    country_exception.charge_taxes = False
    country_exception.save(update_fields=["charge_taxes"])

    # then
    assert get_charge_taxes(tax_configuration, None) == tax_configuration.charge_taxes
    assert (
        get_charge_taxes(tax_configuration, country_exception)
        == country_exception.charge_taxes
    )


def test_get_tax_country_use_shipping_address(
    channel_USD, address_usa, address_other_country
):
    # given
    is_shipping_required = True
    shipping_address = address_usa
    billing_address = address_other_country

    # when
    country = get_tax_country(
        channel_USD, is_shipping_required, shipping_address, billing_address
    )

    # then
    assert country == address_usa.country.code


def test_get_tax_country_use_billing_address(
    channel_USD, address_usa, address_other_country
):
    # given
    is_shipping_required = False
    shipping_address = address_usa
    billing_address = address_other_country

    # when
    country = get_tax_country(
        channel_USD, is_shipping_required, shipping_address, billing_address
    )

    # then
    assert country == address_other_country.country.code


def test_get_tax_country_fallbacks_to_channel_country(channel_USD):
    # given
    shipping_address = None
    billing_address = None

    # when
    country = get_tax_country(channel_USD, True, shipping_address, billing_address)

    # then
    assert country == channel_USD.default_country.code


@pytest.mark.parametrize("delivery_method_assigned", (True, False))
def test_get_tax_country_for_tax_calculation_shipping_is_required(
    delivery_method_assigned,
    checkout_info,
    address_usa,
    warehouse_for_cc,
    shipping_method,
    address_other_country,
):
    # given
    if delivery_method_assigned:
        checkout_info.delivery_method_info = CollectionPointInfo(
            warehouse_for_cc, address_other_country
        )
    # when
    with patch.object(
        checkout_info.checkout, "is_shipping_required", return_value=True
    ):
        assert checkout_info.checkout.is_shipping_required() is True
        country_code = _get_country_code_for_checkout_for_tax_calculation(
            checkout_info, address_usa
        )

    # then
    if delivery_method_assigned:
        assert country_code == (
            checkout_info.delivery_method_info.shipping_address.country.code
        )
    else:
        assert country_code == address_usa.country.code


@pytest.mark.parametrize("additional_address_assigned", (True, False))
def test_get_tax_country_for_tax_calculation_shipping_is_not_required(
    additional_address_assigned,
    checkout_info,
    address_usa,
    warehouse_for_cc,
    shipping_method,
    address_other_country,
):
    # given
    address = address_usa if additional_address_assigned else None
    # when
    with patch.object(
        checkout_info.checkout, "is_shipping_required", return_value=False
    ):
        assert checkout_info.checkout.is_shipping_required() is False
        country_code = _get_country_code_for_checkout_for_tax_calculation(
            checkout_info, address
        )

    # then
    if additional_address_assigned:
        assert country_code == address_usa.country.code
    else:
        assert country_code == checkout_info.checkout.channel.default_country.code

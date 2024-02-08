import pytest

from ...core.utils.country import get_active_country
from ..utils import get_charge_taxes, get_display_gross_prices, get_tax_app_id


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


def test_get_tax_app_id(channel_USD):
    # given
    tax_configuration = channel_USD.tax_configuration
    tax_configuration.tax_app_id = "tax-app-1"
    tax_configuration.save(update_fields=["tax_app_id"])

    # then
    assert get_tax_app_id(tax_configuration, None) == tax_configuration.tax_app_id


@pytest.mark.parametrize(
    ("country_tax_app", "expected_tax_app"),
    [(None, "tax-app-1"), ("tax-app-2", "tax-app-2")],
)
def test_get_tax_app_id_country(country_tax_app, expected_tax_app, channel_USD):
    # given
    tax_configuration = channel_USD.tax_configuration
    tax_configuration.tax_app_id = "tax-app-1"
    tax_configuration.save(update_fields=["tax_app_id"])
    country_exception = tax_configuration.country_exceptions.first()
    country_exception.tax_app_id = country_tax_app
    country_exception.save(update_fields=["tax_app_id"])

    # then
    assert get_tax_app_id(tax_configuration, country_exception) == expected_tax_app


def test_get_tax_country_use_shipping_address(
    channel_USD, address_usa, address_other_country
):
    # given
    shipping_address = address_usa
    billing_address = address_other_country

    # when
    country = get_active_country(channel_USD, shipping_address, billing_address)

    # then
    assert country == address_usa.country.code


def test_get_tax_country_use_billing_address(
    channel_USD, address_usa, address_other_country
):
    # given

    shipping_address = None
    billing_address = address_other_country

    # when
    country = get_active_country(channel_USD, shipping_address, billing_address)

    # then
    assert country == address_other_country.country.code


def test_get_tax_country_fallbacks_to_channel_country(channel_USD):
    # given
    shipping_address = None
    billing_address = None

    # when
    country = get_active_country(channel_USD, shipping_address, billing_address)

    # then
    assert country == channel_USD.default_country.code

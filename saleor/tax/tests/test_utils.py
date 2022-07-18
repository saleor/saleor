from ..utils import get_display_gross_prices, get_tax_country


def test_get_display_gross_prices(channel_USD):
    # given
    tax_configuration = channel_USD.tax_configuration
    tax_configuration.display_gross_prices = True
    country_exception = tax_configuration.country_exceptions.first()
    country_exception.display_gross_prices = False

    # then
    assert (
        get_display_gross_prices(tax_configuration, None)
        == tax_configuration.display_gross_prices
    )
    assert (
        get_display_gross_prices(tax_configuration, country_exception)
        == country_exception.display_gross_prices
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

from decimal import Decimal
from unittest.mock import Mock

import pytest

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...core.prices import Money, TaxedMoney
from ...core.utils.country import get_active_country
from ...graphql.tax.enums import TaxCalculationStrategy
from ...order.utils import get_order_country
from ..utils import (
    get_charge_taxes,
    get_display_gross_prices,
    get_shipping_tax_rate_for_checkout,
    get_shipping_tax_rate_for_order,
    get_tax_app_id,
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


def test_get_tax_country_use_address_data(
    channel_USD,
):
    # given
    address_data = Mock()
    address_data.country = "PL"

    # when
    country = get_active_country(channel_USD, address_data=address_data)

    # then
    assert country == "PL"


def test_get_tax_country_fallbacks_to_channel_country_address_data_with_empty_country(
    channel_USD,
):
    # given
    address_data = Mock()
    address_data.country = None

    # when
    country = get_active_country(channel_USD, address_data=address_data)

    # then
    assert country == channel_USD.default_country.code


def test_get_shipping_tax_rate_for_checkout_weighted_tax(
    checkout_with_items, channel_USD, plugins_manager, shipping_method
):
    # given
    checkout = checkout_with_items
    checkout.shipping_method = shipping_method
    checkout.save(update_fields=["shipping_method"])

    tax_configuration = channel_USD.tax_configuration
    tax_configuration.use_weighted_tax_for_shipping = True
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES.value
    tax_configuration.save(
        update_fields=["use_weighted_tax_for_shipping", "tax_calculation_strategy"]
    )

    checkout_lines_info, _ = fetch_checkout_lines(checkout, plugins_manager)
    checkout_info = fetch_checkout_info(checkout, checkout_lines_info, plugins_manager)

    # Set the same tax rate for all lines
    expected_tax_rate = Decimal("0.1")  # 10%
    for line_info in checkout_lines_info:
        line_info.line.tax_rate = expected_tax_rate
        line_info.line.total_price = TaxedMoney(
            net=Money(Decimal(100), checkout.currency),
            gross=Money(Decimal(110), checkout.currency),
        )

    default_tax_rate = Decimal(20)

    # when
    shipping_tax_rate = get_shipping_tax_rate_for_checkout(
        checkout_info, checkout_lines_info, default_tax_rate, "US"
    )

    # then
    # Should use the weighted tax rate (10%) instead of the default (20%)
    assert shipping_tax_rate == expected_tax_rate * 100


def test_get_shipping_tax_rate_for_checkout_weighted_tax_with_multiple_tax_rates(
    checkout_with_items, channel_USD, plugins_manager
):
    # given
    checkout = checkout_with_items
    tax_configuration = channel_USD.tax_configuration
    tax_configuration.use_weighted_tax_for_shipping = True
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES.value
    tax_configuration.save(
        update_fields=["use_weighted_tax_for_shipping", "tax_calculation_strategy"]
    )

    checkout_info = fetch_checkout_info(checkout, [], plugins_manager)
    checkout_lines_info, _ = fetch_checkout_lines(checkout, plugins_manager)

    assert len(checkout_lines_info) == 4

    default_tax_rate = Decimal(20)

    # Set different tax rates for lines
    # First line: 10% tax rate with $10 tax amount
    first_line = checkout_lines_info[0].line
    first_line.tax_rate = Decimal("0.1")  # 10%
    first_line.total_price = TaxedMoney(
        net=Money(Decimal(100), checkout.currency),
        gross=Money(Decimal(110), checkout.currency),
    )

    # Second line: 5% tax rate with $5 tax amount
    second_line = checkout_lines_info[1].line
    second_line.tax_rate = Decimal("0.05")  # 5%
    second_line.total_price = TaxedMoney(
        net=Money(Decimal(100), checkout.currency),
        gross=Money(Decimal(105), checkout.currency),
    )

    # Third line: 0% tax rate with $0 tax amount
    third_line = checkout_lines_info[2].line
    third_line.tax_rate = Decimal(0)  # 0%
    third_line.total_price = TaxedMoney(
        net=Money(Decimal(100), checkout.currency),
        gross=Money(Decimal(100), checkout.currency),
    )

    fourth_line = checkout_lines_info[3].line
    fourth_line.tax_rate = Decimal("0.2")  # 20%
    fourth_line.total_price = TaxedMoney(
        net=Money(Decimal(100), checkout.currency),
        gross=Money(Decimal(120), checkout.currency),
    )

    # when
    shipping_tax_rate = get_shipping_tax_rate_for_checkout(
        checkout_info, checkout_lines_info, default_tax_rate, "US"
    )

    # then
    total_weighted = sum(
        [
            line.line.total_price.net.amount * line.line.tax_rate * 100
            for line in checkout_lines_info
        ]
    )

    # Expected: (110*10 + 105*5 + 1000*0 + 120*20) / (110 + 105 + 100 + 120) = 4025 / 435 = 9.2529
    expected_rate = (
        total_weighted
        / sum([line.line.total_price.net.amount for line in checkout_lines_info])
    ).quantize(Decimal(".0001"))

    assert shipping_tax_rate == expected_rate == Decimal("8.7500")


def test_get_shipping_tax_rate_for_checkout_when_weighted_tax_is_disabled(
    checkout_with_items, channel_USD, shipping_method, plugins_manager
):
    # given
    checkout = checkout_with_items
    tax_configuration = channel_USD.tax_configuration
    tax_configuration.use_weighted_tax_for_shipping = False
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES.value
    tax_configuration.save(
        update_fields=["use_weighted_tax_for_shipping", "tax_calculation_strategy"]
    )

    checkout.shipping_method = shipping_method
    checkout.save(update_fields=["shipping_method"])

    checkout_info = fetch_checkout_info(checkout, [], plugins_manager)
    checkout_lines_info, _ = fetch_checkout_lines(checkout, plugins_manager)

    first_line = checkout_lines_info[0].line
    first_line.tax_rate = Decimal("0.1")  # 10%
    first_line.total_price = TaxedMoney(
        net=Money(Decimal(100), checkout.currency),
        gross=Money(Decimal(110), checkout.currency),
    )
    first_line.save(
        update_fields=["tax_rate", "total_price_net_amount", "total_price_gross_amount"]
    )

    default_tax_rate = Decimal(20)  # 20%

    # when
    shipping_tax_rate = get_shipping_tax_rate_for_checkout(
        checkout_info, checkout_lines_info, default_tax_rate, "US"
    )

    # then
    # Should return the default tax rate since weighted tax is disabled
    assert shipping_tax_rate == default_tax_rate


def test_get_shipping_tax_rate_for_order_weighted_tax(
    order_with_lines, channel_USD, shipping_zone, address_usa
):
    # given
    order = order_with_lines
    order.shipping_address = address_usa
    order.save(update_fields=["shipping_address"])

    tax_configuration = channel_USD.tax_configuration
    tax_configuration.use_weighted_tax_for_shipping = True
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES.value
    tax_configuration.save(
        update_fields=["use_weighted_tax_for_shipping", "tax_calculation_strategy"]
    )

    default_tax_rate = Decimal(20)
    lines = list(order.lines.all())
    country = get_order_country(order)

    # Set the same tax rate for all lines
    expected_tax_rate = Decimal("0.1")  # 10%
    for line in lines:
        line.tax_rate = expected_tax_rate
        line.total_price = TaxedMoney(
            net=Money(Decimal(100), order.currency),
            gross=Money(Decimal(110), order.currency),
        )

    # when
    shipping_tax_rate = get_shipping_tax_rate_for_order(
        order, lines, default_tax_rate, country
    )

    # then
    # Should use the weighted tax rate (10%) instead of the default (20%)
    assert shipping_tax_rate == expected_tax_rate * 100


def test_get_shipping_tax_rate_for_order_weighted_tax_with_multiple_tax_rates(
    order_with_lines, channel_USD, address_usa
):
    # given
    order = order_with_lines
    order.shipping_address = address_usa
    order.save(update_fields=["shipping_address"])

    tax_configuration = channel_USD.tax_configuration
    tax_configuration.use_weighted_tax_for_shipping = True
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES.value
    tax_configuration.save(
        update_fields=["use_weighted_tax_for_shipping", "tax_calculation_strategy"]
    )

    lines = list(order.lines.all())
    assert len(lines) == 2

    default_tax_rate = Decimal(20)
    country = get_order_country(order)

    # Set different tax rates for lines
    # First line: 10% tax rate with $10 tax amount
    first_line = lines[0]
    first_line.tax_rate = Decimal("0.1")  # 10%
    first_line.total_price = TaxedMoney(
        net=Money(Decimal(100), order.currency),
        gross=Money(Decimal(110), order.currency),
    )
    first_line.save(
        update_fields=["tax_rate", "total_price_net_amount", "total_price_gross_amount"]
    )

    # Second line: 5% tax rate with $5 tax amount
    second_line = lines[1]
    second_line.tax_rate = Decimal("0.05")  # 5%
    second_line.total_price = TaxedMoney(
        net=Money(Decimal(100), order.currency),
        gross=Money(Decimal(105), order.currency),
    )
    second_line.save(
        update_fields=["tax_rate", "total_price_net_amount", "total_price_gross_amount"]
    )

    # when
    shipping_tax_rate = get_shipping_tax_rate_for_order(
        order, lines, default_tax_rate, country
    )

    # then
    # Calculate the expected weighted rate
    total_weighted = sum(
        [line.total_price.net.amount * line.tax_rate * 100 for line in lines]
    )
    total_gross = sum([line.total_price.net.amount for line in lines])
    expected_weighted_rate = (total_weighted / total_gross).quantize(Decimal(".0001"))

    # Verify that the weighted rate is correctly calculated and used
    assert shipping_tax_rate == expected_weighted_rate


def test_get_shipping_tax_rate_for_order_when_weighted_tax_is_disabled(
    order_with_lines, channel_USD, default_tax_class
):
    # given
    order = order_with_lines

    tax_configuration = channel_USD.tax_configuration
    tax_configuration.use_weighted_tax_for_shipping = False
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES.value
    tax_configuration.save(
        update_fields=["use_weighted_tax_for_shipping", "tax_calculation_strategy"]
    )

    lines = list(order.lines.all())
    country = get_order_country(order)

    first_line = lines[0]
    first_line.tax_rate = Decimal("0.1")  # 10%
    first_line.total_price = TaxedMoney(
        net=Money(Decimal(100), order.currency),
        gross=Money(Decimal(110), order.currency),
    )
    first_line.save(
        update_fields=["tax_rate", "total_price_net_amount", "total_price_gross_amount"]
    )

    default_tax_rate = Decimal(20)  # 20%
    order.shipping_tax_class = default_tax_class

    # when
    shipping_tax_rate = get_shipping_tax_rate_for_order(
        order, lines, default_tax_rate, country
    )

    # then
    assert shipping_tax_rate == Decimal("23.000")

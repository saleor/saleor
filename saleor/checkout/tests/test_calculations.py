from decimal import Decimal
from typing import Literal, Union
from unittest.mock import Mock, patch

import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from graphene import Node
from prices import Money, TaxedMoney

from ...checkout.utils import add_promo_code_to_checkout, set_external_shipping_id
from ...core.prices import quantize_price
from ...core.taxes import TaxData, TaxLineData, zero_taxed_money
from ...plugins import PLUGIN_IDENTIFIER_PREFIX
from ...plugins.manager import get_plugins_manager
from ...plugins.tests.sample_plugins import PluginSample
from ...tax import TaxCalculationStrategy
from ...tax.calculations.checkout import update_checkout_prices_with_flat_rates
from ..base_calculations import (
    base_checkout_delivery_price,
    calculate_base_line_total_price,
)
from ..calculations import (
    _apply_tax_data,
    _calculate_and_add_tax,
    _set_checkout_base_prices,
    fetch_checkout_data,
)
from ..fetch import CheckoutLineInfo, fetch_checkout_info, fetch_checkout_lines


@pytest.fixture
def checkout_lines(checkout_with_items):
    return checkout_with_items.lines.all()


@pytest.fixture
def tax_data(checkout_with_items, checkout_lines):
    checkout = checkout_with_items
    tax_rate = Decimal("23")
    net = Decimal("10.000")
    gross = Decimal("12.300")
    lines = checkout_lines
    return TaxData(
        shipping_price_net_amount=checkout.shipping_price.net.amount + net,
        shipping_price_gross_amount=checkout.shipping_price.gross.amount + gross,
        shipping_tax_rate=tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=line.total_price.net.amount + net,
                total_gross_amount=line.total_price.gross.amount + gross,
                tax_rate=tax_rate,
            )
            for line in lines
        ],
    )


def test_apply_tax_data(checkout_with_items, checkout_lines, tax_data):
    # given
    checkout = checkout_with_items
    lines = checkout_lines

    # when
    _apply_tax_data(
        checkout,
        [
            Mock(spec=CheckoutLineInfo, line=line, variant=line.variant)
            for line in lines
        ],
        tax_data,
    )

    # then
    assert str(checkout.shipping_price.net.amount) == str(
        quantize_price(tax_data.shipping_price_net_amount, checkout.currency)
    )
    assert str(checkout.shipping_price.gross.amount) == str(
        quantize_price(tax_data.shipping_price_gross_amount, checkout.currency)
    )

    for line, tax_line in zip(lines, tax_data.lines):
        assert str(line.total_price.net.amount) == str(
            quantize_price(tax_line.total_net_amount, checkout.currency)
        )
        assert str(line.total_price.gross.amount) == str(
            quantize_price(tax_line.total_gross_amount, checkout.currency)
        )


@pytest.fixture
def fetch_kwargs(checkout_with_items, plugins_manager):
    lines, _ = fetch_checkout_lines(checkout_with_items)
    return {
        "checkout_info": fetch_checkout_info(
            checkout_with_items, lines, plugins_manager
        ),
        "manager": plugins_manager,
        "lines": lines,
        "address": checkout_with_items.shipping_address
        or checkout_with_items.billing_address,
    }


SALE = Decimal("1.0")
DISCOUNT = Decimal("1.5")


def get_checkout_taxed_prices_data(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["total", "shipping_price"],
    currency: str,
) -> TaxedMoney:
    money = TaxedMoney(
        Money(getattr(obj, f"{attr}_net_amount"), currency),
        Money(getattr(obj, f"{attr}_gross_amount"), currency),
    )
    return money


def get_taxed_money(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["total", "shipping_price"],
    currency: str,
) -> TaxedMoney:
    return TaxedMoney(
        Money(getattr(obj, f"{attr}_net_amount"), currency),
        Money(getattr(obj, f"{attr}_gross_amount"), currency),
    )


@freeze_time("2020-12-12 12:00:00")
@patch("saleor.checkout.calculations._apply_tax_data")
def test_fetch_checkout_data_plugins(
    _mocked_from_app,
    plugins_manager,
    fetch_kwargs,
    checkout_with_items,
    tax_data,
):
    # given
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])
    currency = checkout_with_items.currency
    plugins_manager.get_taxes_for_checkout = Mock(return_value=None)

    totals, tax_rates = zip(
        *[
            (
                get_checkout_taxed_prices_data(line, "total", currency),
                line.tax_rate / 100,
            )
            for line in tax_data.lines
        ]
    )
    plugins_manager.calculate_checkout_line_total = Mock(side_effect=totals * 3)
    plugins_manager.get_checkout_line_tax_rate = Mock(side_effect=tax_rates)

    shipping_price = get_taxed_money(tax_data, "shipping_price", currency)
    plugins_manager.calculate_checkout_shipping = Mock(return_value=shipping_price)

    shipping_tax_rate = tax_data.shipping_tax_rate / 100
    plugins_manager.get_checkout_shipping_tax_rate = Mock(
        return_value=shipping_tax_rate
    )

    subtotal = zero_taxed_money(currency)
    for tax_line in tax_data.lines:
        total_price = get_taxed_money(tax_line, "total", currency)
        subtotal = subtotal + total_price

    plugins_manager.calculate_checkout_subtotal = Mock(return_value=subtotal)
    plugins_manager.calculate_checkout_total = Mock(
        return_value=shipping_price + subtotal
    )

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    checkout_with_items.refresh_from_db()
    for checkout_line, tax_line in zip(checkout_with_items.lines.all(), tax_data.lines):
        total_price = get_taxed_money(tax_line, "total", currency)
        assert checkout_line.total_price == total_price
        assert checkout_line.tax_rate == tax_line.tax_rate / 100

    assert checkout_with_items.subtotal == subtotal
    assert checkout_with_items.shipping_price == shipping_price
    assert checkout_with_items.shipping_tax_rate == shipping_tax_rate
    assert checkout_with_items.total == subtotal + shipping_price


@patch(
    "saleor.checkout.calculations.update_checkout_prices_with_flat_rates",
    wraps=update_checkout_prices_with_flat_rates,
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_fetch_checkout_data_flat_rates(
    mocked_update_checkout_prices_with_flat_rates,
    checkout_with_items_and_shipping,
    fetch_kwargs,
    prices_entered_with_tax,
):
    # given
    checkout = checkout_with_items_and_shipping
    tc = checkout.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

    country_code = checkout.shipping_address.country.code
    for line in checkout.lines.all():
        line.variant.product.tax_class.country_rates.update_or_create(
            country=country_code, rate=23
        )

    checkout.shipping_method.tax_class.country_rates.update_or_create(
        country=country_code, rate=23
    )

    # when
    fetch_checkout_data(**fetch_kwargs)
    checkout.refresh_from_db()
    line = checkout.lines.first()

    # then
    mocked_update_checkout_prices_with_flat_rates.assert_called_once()
    assert line.tax_rate == Decimal("0.2300")
    assert checkout.shipping_tax_rate == Decimal("0.2300")


@patch(
    "saleor.checkout.calculations.update_checkout_prices_with_flat_rates",
    wraps=update_checkout_prices_with_flat_rates,
)
def test_fetch_checkout_data_flat_rates_and_no_tax_calc_strategy(
    mocked_update_checkout_prices_with_flat_rates,
    checkout_with_items_and_shipping,
    fetch_kwargs,
):
    # given
    checkout = checkout_with_items_and_shipping
    tc = checkout.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = True
    tc.tax_calculation_strategy = None
    tc.save(update_fields=["prices_entered_with_tax", "tax_calculation_strategy"])

    country_code = checkout.shipping_address.country.code
    for line in checkout.lines.all():
        line.variant.product.tax_class.country_rates.update_or_create(
            country=country_code, rate=23
        )

    checkout.shipping_method.tax_class.country_rates.update_or_create(
        country=country_code, rate=23
    )

    # when
    fetch_checkout_data(**fetch_kwargs)
    checkout.refresh_from_db()
    line = checkout.lines.first()

    # then
    mocked_update_checkout_prices_with_flat_rates.assert_called_once()
    assert line.tax_rate == Decimal("0.2300")
    assert checkout.shipping_tax_rate == Decimal("0.2300")


def test_set_checkout_base_prices_no_charge_taxes_with_voucher(
    checkout_with_item, voucher_percentage
):
    # given
    checkout = checkout_with_item
    channel = checkout.channel

    line = checkout.lines.first()
    variant = line.variant
    channel_listing = variant.channel_listings.get(channel=channel.pk)
    channel_listing.price_amount = Decimal("9.60")
    channel_listing.discounted_price_amount = Decimal("9.60")
    channel_listing.save()

    line.quantity = 7
    line.save()

    voucher_value = Decimal("3.00")
    voucher_channel_listing = voucher_percentage.channel_listings.get(
        channel=channel.pk
    )
    voucher_channel_listing.discount_value = voucher_value
    voucher_channel_listing.save()

    lines, _ = fetch_checkout_lines(checkout)
    line_info = list(lines)[0]
    variant = line_info.variant
    product_price = variant.get_price(line_info.channel_listing)

    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    add_promo_code_to_checkout(
        manager,
        checkout_info,
        lines,
        voucher_percentage.code,
    )

    checkout.refresh_from_db()
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    _set_checkout_base_prices(checkout, checkout_info, lines)
    checkout.save()
    checkout.lines.bulk_update(
        [line_info.line for line_info in lines],
        [
            "total_price_net_amount",
            "total_price_gross_amount",
            "tax_rate",
        ],
    )
    checkout.refresh_from_db()

    line = checkout.lines.all()[0]

    # then
    assert line.tax_rate == Decimal("0.0")

    expected_unit_price = quantize_price(
        (100 - voucher_value) / 100 * product_price, checkout.currency
    )
    line_unit_price = quantize_price(
        line.total_price / line.quantity, checkout.currency
    )
    assert line_unit_price.gross == expected_unit_price
    assert line.total_price == checkout.total


def test_set_checkout_base_prices_no_charge_taxes_with_order_promotion(
    checkout_with_item_and_order_discount,
):
    # given
    checkout = checkout_with_item_and_order_discount
    discount_amount = checkout.discounts.first().amount_value

    line = checkout.lines.first()
    line.quantity = 7
    line.save()

    lines, _ = fetch_checkout_lines(checkout)
    line_info = list(lines)[0]
    variant = line_info.variant
    product_price = variant.get_price(line_info.channel_listing)

    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    _set_checkout_base_prices(checkout, checkout_info, lines)
    checkout.save()
    checkout.lines.bulk_update(
        [line_info.line for line_info in lines],
        [
            "total_price_net_amount",
            "total_price_gross_amount",
            "tax_rate",
        ],
    )

    # then
    line.refresh_from_db()
    assert line.tax_rate == Decimal("0.0")

    line_total = product_price.amount * line.quantity - discount_amount
    assert line.total_price_gross_amount == line_total
    assert checkout.total_gross_amount == line_total


@freeze_time("2020-12-12 12:00:00")
def test_fetch_checkout_data_webhooks_success(
    plugins_manager,
    fetch_kwargs,
    checkout_with_items,
    tax_data,
):
    # given
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])
    currency = checkout_with_items.currency
    plugins_manager.get_taxes_for_checkout = Mock(return_value=tax_data)

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    checkout_with_items.refresh_from_db()
    assert checkout_with_items.shipping_price == get_taxed_money(
        tax_data, "shipping_price", currency
    )
    assert checkout_with_items.shipping_tax_rate == tax_data.shipping_tax_rate / 100
    for checkout_line, tax_line in zip(checkout_with_items.lines.all(), tax_data.lines):
        assert checkout_line.total_price == get_taxed_money(tax_line, "total", currency)
        assert checkout_line.tax_rate == tax_line.tax_rate / 100


@freeze_time("2020-12-12 12:00:00")
def test_fetch_checkout_prices_when_tax_exemption_and_include_taxes_in_prices(
    checkout_with_items_and_shipping, settings
):
    """Test tax exemption when taxes are included in prices.

    Use PluginSample to test tax exemption.
    PluginSample always return same values of calculated taxes:

    shipping_price_net_amount = 50
    shipping_price_gross_amount = 63.20

    Each line is treated as line with 3 units where unite gross value = 12.30 and net
    value = 10
    """
    # given
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    manager = get_plugins_manager(allow_replica=False)

    checkout = checkout_with_items_and_shipping
    checkout.price_expiration = timezone.now()
    checkout.tax_exemption = True
    checkout.save(update_fields=["price_expiration", "tax_exemption"])

    tc = checkout.channel.tax_configuration
    tc.prices_entered_with_tax = True
    tc.save(update_fields=["prices_entered_with_tax"])

    currency = checkout.currency

    lines_info, _ = fetch_checkout_lines(checkout)

    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
        "address": checkout.shipping_address or checkout.billing_address,
    }

    # when
    fetch_checkout_data(**fetch_kwargs)
    checkout.refresh_from_db()

    # then

    one_line_total_price = TaxedMoney(
        net=Money("30.0", currency), gross=Money("30.0", currency)
    )
    all_lines_total_price = len(lines_info) * one_line_total_price
    shipping_price = TaxedMoney(
        net=Money("50.0", currency), gross=Money("50.0", currency)
    )

    for line in checkout.lines.all():
        assert line.total_price == one_line_total_price
        assert line.tax_rate == 0

    assert checkout.shipping_price == shipping_price
    assert checkout.shipping_tax_rate == 0

    assert checkout.total == shipping_price + all_lines_total_price
    assert checkout.subtotal == all_lines_total_price


@freeze_time("2020-12-12 12:00:00")
def test_fetch_checkout_prices_when_tax_exemption_and_not_include_taxes_in_prices(
    checkout_with_items_and_shipping, settings
):
    """Test tax exemption when taxes are not included in prices.

    When Checkout.tax_exemption = True and SiteSettings.include_taxes_in_prices = False
    tax plugins should be ignored and only net prices should be calculated and returned.
    """
    # given
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    manager = get_plugins_manager(allow_replica=False)

    checkout = checkout_with_items_and_shipping
    checkout.price_expiration = timezone.now()
    checkout.tax_exemption = True
    checkout.save(update_fields=["price_expiration", "tax_exemption"])

    tc = checkout.channel.tax_configuration
    tc.prices_entered_with_tax = False
    tc.save(update_fields=["prices_entered_with_tax"])

    currency = checkout.currency

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines_info, manager)
    fetch_kwargs = {
        "checkout_info": checkout_info,
        "manager": manager,
        "lines": lines_info,
        "address": checkout.shipping_address or checkout.billing_address,
    }

    # when
    fetch_checkout_data(**fetch_kwargs)
    checkout.refresh_from_db()

    # then
    one_line_total_prices = [
        calculate_base_line_total_price(line_info) for line_info in lines_info
    ]
    all_lines_total_price = sum(one_line_total_prices, zero_taxed_money(currency))
    shipping_price = base_checkout_delivery_price(checkout_info, lines_info)
    shipping_price = quantize_price(
        TaxedMoney(shipping_price, shipping_price), currency
    )

    for line in checkout.lines.all():
        assert line.tax_rate == 0

    assert checkout.shipping_price == shipping_price
    assert checkout.shipping_tax_rate == 0

    assert checkout.total == shipping_price + all_lines_total_price
    assert checkout.subtotal == all_lines_total_price


@freeze_time()
@patch("saleor.plugins.manager.PluginsManager.calculate_checkout_total")
@patch("saleor.plugins.manager.PluginsManager.get_taxes_for_checkout")
@override_settings(PLUGINS=["saleor.plugins.tests.sample_plugins.PluginSample"])
def test_fetch_checkout_data_calls_plugin(
    mock_get_taxes,
    mock_calculate_checkout_total,
    checkout_with_items,
):
    # given
    checkout = checkout_with_items
    checkout.price_expiration = timezone.now()
    checkout.save()

    price = Money("10.0", currency=checkout.currency)
    mock_calculate_checkout_total.return_value = TaxedMoney(price, price)

    checkout.channel.tax_configuration.tax_app_id = (
        PLUGIN_IDENTIFIER_PREFIX + PluginSample.PLUGIN_ID
    )
    checkout.channel.tax_configuration.save()

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout)

    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
        "address": checkout.shipping_address or checkout.billing_address,
    }

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    mock_calculate_checkout_total.assert_called_once()
    mock_get_taxes.assert_not_called()


@freeze_time()
@patch("saleor.plugins.manager.PluginsManager.calculate_checkout_total")
@patch("saleor.plugins.manager.PluginsManager.get_taxes_for_checkout")
@patch("saleor.checkout.calculations._apply_tax_data")
@override_settings(PLUGINS=["saleor.plugins.tests.sample_plugins.PluginSample"])
def test_fetch_checkout_data_calls_tax_app(
    mock_apply_tax_data,
    mock_get_taxes,
    mock_calculate_checkout_total,
    fetch_kwargs,
    checkout_with_items,
):
    # given
    checkout = checkout_with_items
    checkout.price_expiration = timezone.now()
    checkout.save()

    checkout.channel.tax_configuration.tax_app_id = "test.app"
    checkout.channel.tax_configuration.save()

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout)

    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
        "address": checkout.shipping_address or checkout.billing_address,
    }

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    mock_get_taxes.assert_called_once()
    mock_apply_tax_data.assert_called_once()
    mock_calculate_checkout_total.assert_not_called()


@freeze_time()
def test_fetch_checkout_data_calls_inactive_plugin(
    fetch_kwargs,
    checkout_with_items,
):
    # given
    checkout = checkout_with_items
    checkout.price_expiration = timezone.now()
    checkout.save()

    checkout.channel.tax_configuration.tax_app_id = "plugin:test"
    checkout.channel.tax_configuration.save()

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout)

    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
        "address": checkout.shipping_address or checkout.billing_address,
    }

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    assert checkout.total.gross.amount > 0
    assert checkout_with_items.tax_error == "Empty tax data."


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_external_shipping_method_called_only_once_during_tax_calculations(
    mock_send_webhook_request_sync,
    checkout_with_single_item,
    settings,
    tax_app_with_subscription_webhooks,
    shipping_app_with_subscription,
    address,
):
    # given
    external_method_id = "method-1-from-shipping-app"
    mock_send_webhook_request_sync.side_effect = (
        [
            {
                "amount": "1337.0",
                "currency": "USD",
                "id": external_method_id,
                "name": "Shipping app method 1",
            }
        ],
        {
            "lines": [
                {"tax_rate": 0, "total_gross_amount": "21.6", "total_net_amount": 20}
            ],
            "shipping_price_gross_amount": "1443.96",
            "shipping_price_net_amount": "1337",
            "shipping_tax_rate": 0,
        },
    )
    external_shipping_method_id = Node.to_global_id(
        "app", f"{shipping_app_with_subscription.id}:{external_method_id}"
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    checkout_with_single_item.shipping_address = address
    set_external_shipping_id(checkout_with_single_item, external_shipping_method_id)
    checkout_with_single_item.save()
    checkout_with_single_item.metadata_storage.save()
    checkout_lines, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_info = fetch_checkout_info(
        checkout_with_single_item, checkout_lines, manager
    )
    assert checkout_with_single_item.shipping_price == TaxedMoney(
        net=Money("0", "USD"), gross=Money("0", "USD")
    )

    # when
    _calculate_and_add_tax(
        TaxCalculationStrategy.TAX_APP,
        None,
        checkout_with_single_item,
        manager,
        checkout_info,
        checkout_lines,
        prices_entered_with_tax=False,
    )

    # then
    assert mock_send_webhook_request_sync.call_count == 2
    assert checkout_with_single_item.shipping_price == TaxedMoney(
        net=Money("1337.00", "USD"), gross=Money("1443.96", "USD")
    )


@pytest.mark.parametrize("tax_app_id", [None, "test.app"])
def test_calculate_and_add_tax_empty_tax_data_logging_address(
    tax_app_id, checkout_with_single_item, address, caplog
):
    # given
    checkout = checkout_with_single_item

    address.validation_skipped = True
    address.postal_code = "invalid postal code"
    address.save(update_fields=["postal_code", "validation_skipped"])

    checkout.shipping_address = address
    checkout.billing_address = address
    checkout.save(update_fields=["billing_address", "shipping_address"])

    checkout.channel.tax_configuration.tax_app_id = tax_app_id
    checkout.channel.tax_configuration.save()

    zero_money = zero_taxed_money(checkout.currency)
    manager_methods = {
        "calculate_checkout_total": Mock(return_value=zero_money),
        "calculate_checkout_subtotal": Mock(return_value=zero_money),
        "calculate_checkout_line_total": Mock(return_value=zero_money),
        "calculate_checkout_shipping": Mock(return_value=zero_money),
        "get_checkout_shipping_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_checkout_line_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_taxes_for_checkout": Mock(return_value=None),
    }
    manager = Mock(**manager_methods)

    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines_info, manager)

    # when
    _calculate_and_add_tax(
        TaxCalculationStrategy.TAX_APP,
        None,
        checkout,
        manager,
        checkout_info,
        checkout_lines_info,
        prices_entered_with_tax=False,
    )

    # then
    assert (
        f"Fetching tax data for checkout with address validation skipped. "
        f"Address ID: {address.pk}" in caplog.text
    )

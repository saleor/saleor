from decimal import Decimal
from typing import Literal
from unittest.mock import Mock, patch

import pytest
from django.db.models import F
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from graphene import Node
from prices import Money, TaxedMoney

from ...checkout.models import CheckoutDelivery
from ...core.prices import quantize_price
from ...core.taxes import (
    TaxData,
    TaxDataError,
    TaxDataErrorMessage,
    TaxLineData,
    zero_money,
    zero_taxed_money,
)
from ...graphql.core.utils import to_global_id_or_none
from ...plugins import PLUGIN_IDENTIFIER_PREFIX
from ...plugins.avatax.plugin import DeprecatedAvataxPlugin
from ...plugins.avatax.tests.conftest import plugin_configuration  # noqa: F401
from ...plugins.manager import get_plugins_manager
from ...plugins.tests.sample_plugins import PluginSample
from ...product.models import ProductVariantChannelListing
from ...tax import TaxCalculationStrategy
from ...tax.calculations.checkout import update_checkout_prices_with_flat_rates
from ...tax.models import TaxClass, TaxClassCountryRate
from ...tests import race_condition
from .. import CheckoutAuthorizeStatus, CheckoutChargeStatus
from ..base_calculations import (
    base_checkout_delivery_price,
    calculate_base_line_total_price,
)
from ..calculations import (
    _apply_tax_data,
    _calculate_and_add_tax,
    _set_checkout_base_prices,
    calculate_checkout_total,
    fetch_checkout_data,
    logger,
)
from ..fetch import CheckoutLineInfo, fetch_checkout_info, fetch_checkout_lines
from ..models import Checkout
from ..utils import (
    add_promo_code_to_checkout,
)


@pytest.fixture
def tax_data(checkout_with_items, checkout_lines):
    checkout = checkout_with_items
    tax_rate = Decimal(23)
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

    for line, tax_line in zip(lines, tax_data.lines, strict=False):
        assert str(line.total_price.net.amount) == str(
            quantize_price(tax_line.total_net_amount, checkout.currency)
        )
        assert str(line.total_price.gross.amount) == str(
            quantize_price(tax_line.total_gross_amount, checkout.currency)
        )


def test_apply_tax_data_tax_rate_matches(checkout_with_items, checkout_lines):
    # given
    net_amount = Decimal("10.000")
    tax_rate = Decimal("8.875")
    expected_tax_rate = Decimal("0.08875")
    gross_amount = net_amount + (net_amount * tax_rate / 100)
    tax_data = TaxData(
        shipping_price_net_amount=net_amount,
        shipping_price_gross_amount=gross_amount,
        shipping_tax_rate=tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=net_amount,
                total_gross_amount=gross_amount,
                tax_rate=tax_rate,
            )
            for _ in checkout_lines
        ],
    )

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
    assert checkout.shipping_tax_rate == expected_tax_rate

    for line in lines:
        assert line.tax_rate == expected_tax_rate


@pytest.fixture
def fetch_kwargs(checkout_with_items, plugins_manager):
    lines, _ = fetch_checkout_lines(checkout_with_items)
    return {
        "checkout_info": fetch_checkout_info(
            checkout_with_items, lines, plugins_manager
        ),
        "manager": plugins_manager,
        "lines": lines,
    }


SALE = Decimal("1.0")
DISCOUNT = Decimal("1.5")


def get_checkout_taxed_prices_data(
    obj: TaxData | TaxLineData,
    attr: Literal["total", "shipping_price"],
    currency: str,
) -> TaxedMoney:
    money = TaxedMoney(
        Money(getattr(obj, f"{attr}_net_amount"), currency),
        Money(getattr(obj, f"{attr}_gross_amount"), currency),
    )
    return money


def get_taxed_money(
    obj: TaxData | TaxLineData,
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
        ],
        strict=False,
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
    fetch_checkout_data(**fetch_kwargs, allow_sync_webhooks=True)

    # then
    checkout_with_items.refresh_from_db()
    for checkout_line, tax_line in zip(
        checkout_with_items.lines.all(), tax_data.lines, strict=False
    ):
        total_price = get_taxed_money(tax_line, "total", currency)
        assert checkout_line.total_price == total_price
        assert checkout_line.tax_rate == tax_line.tax_rate / 100

    assert checkout_with_items.subtotal == subtotal
    assert checkout_with_items.shipping_price == shipping_price
    assert checkout_with_items.shipping_tax_rate == shipping_tax_rate
    assert checkout_with_items.total == subtotal + shipping_price


@freeze_time("2020-12-12 12:00:00")
@patch("saleor.checkout.calculations._apply_tax_data")
def test_fetch_checkout_data_plugins_allow_sync_webhooks_set_to_false(
    _mocked_from_app,
    plugins_manager,
    fetch_kwargs,
    checkout_with_items,
):
    # given
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    currency = checkout_with_items.currency
    plugins_manager.get_taxes_for_checkout = Mock(return_value=None)

    previous_subtotal = checkout_with_items.subtotal
    previous_shipping_price = checkout_with_items.shipping_price
    previous_shipping_tax_rate = checkout_with_items.shipping_tax_rate
    previous_total = checkout_with_items.total

    plugins_manager.calculate_checkout_line_total = Mock(
        return_value=zero_taxed_money(currency)
    )
    plugins_manager.get_checkout_line_tax_rate = Mock(return_value=Decimal("0.23"))

    plugins_manager.calculate_checkout_shipping = Mock(
        return_value=zero_taxed_money(currency)
    )

    plugins_manager.get_checkout_shipping_tax_rate = Mock(return_value=Decimal("0.23"))
    plugins_manager.calculate_checkout_subtotal = Mock(
        return_value=zero_taxed_money(currency)
    )
    plugins_manager.calculate_checkout_total = Mock(
        return_value=zero_taxed_money(currency)
    )

    checkout_info = fetch_kwargs["checkout_info"]
    assert (
        checkout_info.tax_configuration.tax_calculation_strategy
        == TaxCalculationStrategy.TAX_APP
    )

    # when
    fetch_checkout_data(**fetch_kwargs, allow_sync_webhooks=False)

    # then
    assert checkout_with_items.subtotal == previous_subtotal
    assert checkout_with_items.shipping_price == previous_shipping_price
    assert checkout_with_items.shipping_tax_rate == previous_shipping_tax_rate
    assert checkout_with_items.total == previous_total

    plugins_manager.calculate_checkout_line_total.assert_not_called()
    plugins_manager.get_checkout_line_tax_rate.assert_not_called()
    plugins_manager.calculate_checkout_shipping.assert_not_called()
    plugins_manager.get_checkout_shipping_tax_rate.assert_not_called()
    plugins_manager.get_checkout_shipping_tax_rate.assert_not_called()
    plugins_manager.calculate_checkout_subtotal.assert_not_called()
    plugins_manager.calculate_checkout_total.assert_not_called()


@pytest.mark.parametrize("allow_sync_webhooks", [True, False])
@patch(
    "saleor.checkout.calculations.update_checkout_prices_with_flat_rates",
    wraps=update_checkout_prices_with_flat_rates,
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_fetch_checkout_data_flat_rates(
    mocked_update_checkout_prices_with_flat_rates,
    allow_sync_webhooks,
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

    TaxClassCountryRate.objects.update_or_create(
        country=country_code,
        rate=23,
        tax_class_id=checkout.assigned_delivery.tax_class_id,
    )

    # when
    fetch_checkout_data(**fetch_kwargs, allow_sync_webhooks=allow_sync_webhooks)
    checkout.refresh_from_db()
    line = checkout.lines.first()

    # then
    mocked_update_checkout_prices_with_flat_rates.assert_called_once()
    assert line.tax_rate == Decimal("0.2300")
    assert checkout.shipping_tax_rate == Decimal("0.2300")


@pytest.mark.parametrize("allow_sync_webhooks", [True, False])
@patch(
    "saleor.checkout.calculations.update_checkout_prices_with_flat_rates",
    wraps=update_checkout_prices_with_flat_rates,
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_fetch_checkout_data_flat_rates_with_weighted_shipping_tax(
    mocked_update_checkout_prices_with_flat_rates,
    allow_sync_webhooks,
    checkout_with_items_and_shipping,
    address,
    prices_entered_with_tax,
    tax_classes,
    plugins_manager,
):
    # given
    checkout = checkout_with_items_and_shipping

    tc = checkout.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.use_weighted_tax_for_shipping = True
    tc.save()

    country_code = checkout.shipping_address.country.code
    first_line = checkout.lines.first()
    second_line = checkout.lines.last()
    first_tax_class = first_line.variant.product.tax_class
    first_tax_class.country_rates.filter(country=country_code).update(rate=5)
    first_line.variant.product.tax_class = first_tax_class
    first_line.variant.product.save()

    second_tax_class = tax_classes[0]
    second_tax_class.country_rates.filter(country=country_code).update(rate=60)
    second_line.variant.product.tax_class = second_tax_class
    second_line.variant.product.save()

    third_tax_class = tax_classes[1]
    third_tax_class.country_rates.filter(country=country_code).update(rate=223)
    checkout.assigned_delivery.tax_class_id = third_tax_class.id
    checkout.assigned_delivery.save()

    lines, _ = fetch_checkout_lines(checkout_with_items_and_shipping)
    checkout_info = fetch_checkout_info(
        checkout_with_items_and_shipping, lines, plugins_manager
    )

    # when
    fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
        allow_sync_webhooks=allow_sync_webhooks,
    )

    # then
    checkout.refresh_from_db()
    lines = checkout.lines.all()

    mocked_update_checkout_prices_with_flat_rates.assert_called_once()
    total_weighted = sum(line.total_price.net.amount * line.tax_rate for line in lines)

    assert checkout.shipping_tax_rate == (
        total_weighted / sum(line.total_price.net.amount for line in lines)
    ).quantize(Decimal("0.0001"))


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
    TaxClassCountryRate.objects.update_or_create(
        country=country_code,
        rate=23,
        tax_class_id=checkout.assigned_delivery.tax_class_id,
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
    for checkout_line, tax_line in zip(
        checkout_with_items.lines.all(), tax_data.lines, strict=False
    ):
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
    checkout_with_items,
    tax_data_response,
):
    # given

    checkout = checkout_with_items
    checkout.price_expiration = timezone.now()
    checkout.save()

    mock_get_taxes.return_value = tax_data_response

    checkout.channel.tax_configuration.tax_app_id = "test.app"
    checkout.channel.tax_configuration.save()

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout)

    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
        "allow_sync_webhooks": True,
    }

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    mock_get_taxes.assert_called_once()
    mock_apply_tax_data.assert_called_once()
    mock_calculate_checkout_total.assert_not_called()


@freeze_time()
@patch("saleor.plugins.manager.PluginsManager.calculate_checkout_total")
@patch("saleor.plugins.manager.PluginsManager.get_taxes_for_checkout")
@patch("saleor.checkout.calculations._apply_tax_data")
@override_settings(PLUGINS=["saleor.plugins.tests.sample_plugins.PluginSample"])
def test_fetch_checkout_data_calls_tax_app_when_allow_sync_webhooks_set_to_false(
    mock_apply_tax_data,
    mock_get_taxes,
    mock_calculate_checkout_total,
    checkout_with_items,
):
    # given

    checkout = checkout_with_items
    checkout.price_expiration = timezone.now()
    checkout.save()

    previous_subtotal = checkout_with_items.subtotal
    previous_shipping_price = checkout_with_items.shipping_price
    previous_shipping_tax_rate = checkout_with_items.shipping_tax_rate
    previous_total = checkout_with_items.total

    checkout.channel.tax_configuration.tax_app_id = "test.app"
    checkout.channel.tax_configuration.save()

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout)

    checkout_info = fetch_checkout_info(checkout, lines_info, manager)
    fetch_kwargs = {
        "checkout_info": checkout_info,
        "manager": manager,
        "lines": lines_info,
        "allow_sync_webhooks": False,
    }
    assert (
        checkout_info.tax_configuration.tax_calculation_strategy
        == TaxCalculationStrategy.TAX_APP
    )

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    assert checkout_with_items.subtotal == previous_subtotal
    assert checkout_with_items.shipping_price == previous_shipping_price
    assert checkout_with_items.shipping_tax_rate == previous_shipping_tax_rate
    assert checkout_with_items.total == previous_total

    mock_apply_tax_data.assert_not_called()
    mock_get_taxes.assert_not_called()
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
    }

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    assert checkout.total.gross.amount > 0
    assert checkout_with_items.tax_error == "Empty tax data."


def test_fetch_checkout_data_flat_rates_shipping_tax_differs_from_default(
    checkout_with_items,
    address,
    plugins_manager,
):
    # given the checkout with the shipping country and tax different than the channel
    # default country
    checkout = checkout_with_items
    tc = checkout.channel.tax_configuration
    tc.prices_entered_with_tax = True
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.country_exceptions.all().delete()
    tc.save()

    default_country = checkout.channel.default_country
    default_country_rate = 21
    shipping_address_country = "PL"
    shipping_address_rate = 23
    tax_class = TaxClass.objects.create(name="Product")
    tax_class.country_rates.bulk_create(
        [
            TaxClassCountryRate(country=default_country, rate=default_country_rate),
            TaxClassCountryRate(
                country=shipping_address_country, rate=shipping_address_rate
            ),
        ]
    )
    for line in checkout.lines.all():
        product = line.variant.product
        product.tax_class = tax_class
        product.save(update_fields=["tax_class"])

    checkout.shipping_address = address
    checkout.billing_address = address
    checkout.save(update_fields=["shipping_address", "billing_address"])

    lines, _ = fetch_checkout_lines(checkout_with_items)
    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(
            checkout_with_items, lines, plugins_manager
        ),
        "manager": plugins_manager,
        "lines": lines,
    }

    # when
    fetch_checkout_data(**fetch_kwargs, allow_sync_webhooks=False)

    # then
    checkout.refresh_from_db()
    assert round(checkout.total.tax / checkout.total.net * 100) == shipping_address_rate
    for line in checkout.lines.all():
        assert line.tax_rate * 100 == shipping_address_rate


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_external_shipping_webhook_it_not_called_during_tax_calculations(
    mock_send_webhook_request_sync,
    checkout_with_single_item,
    settings,
    tax_app,
    shipping_app_with_subscription,
    address,
):
    # given
    external_method_id = "method-1-from-shipping-app"
    shipping_name = "Shipping app method 1"
    shipping_price = Decimal(10)
    mock_send_webhook_request_sync.return_value = {
        "lines": [
            {"tax_rate": 0, "total_gross_amount": "21.6", "total_net_amount": 20}
        ],
        "shipping_price_gross_amount": "1443.96",
        "shipping_price_net_amount": "1337",
        "shipping_tax_rate": 0,
    }

    external_shipping_method_id = Node.to_global_id(
        "app", f"{shipping_app_with_subscription.id}:{external_method_id}"
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    manager = get_plugins_manager(allow_replica=False)

    checkout_with_single_item.assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout_with_single_item,
        external_shipping_method_id=external_shipping_method_id,
        name=shipping_name,
        price_amount=shipping_price,
        currency="USD",
        maximum_delivery_days=7,
    )

    checkout_with_single_item.shipping_address = address

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
    assert mock_send_webhook_request_sync.call_count == 1
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


@pytest.mark.parametrize(
    ("prices_entered_with_tax", "tax_app_id"),
    [(True, None), (True, "test.app"), (False, None), (False, "test.app")],
)
@patch.object(logger, "warning")
@patch("saleor.checkout.calculations._set_checkout_base_prices")
def test_fetch_checkout_data_tax_data_with_tax_data_error(
    mock_set_base_prices,
    mocked_logger,
    prices_entered_with_tax,
    tax_app_id,
    checkout_with_single_item,
):
    # given
    checkout = checkout_with_single_item

    channel = checkout.channel
    channel.tax_configuration.tax_app_id = tax_app_id
    channel.tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    channel.tax_configuration.save()

    error_msg = "Invalid tax data"
    errors = [{"error1": "Negative tax data"}, {"error2": "Invalid tax data"}]
    returned_tax_error = TaxDataError(message=error_msg, errors=errors)
    zero_money = zero_taxed_money(checkout.currency)
    manager_methods = {
        "calculate_checkout_total": Mock(return_value=zero_money),
        "calculate_checkout_subtotal": Mock(return_value=zero_money),
        "calculate_checkout_line_total": Mock(return_value=zero_money),
        "calculate_checkout_shipping": Mock(return_value=zero_money),
        "get_checkout_shipping_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_checkout_line_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_taxes_for_checkout": Mock(side_effect=returned_tax_error),
    }
    manager = Mock(**manager_methods)

    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines_info, manager)

    # when
    fetch_checkout_data(checkout_info, manager, checkout_lines_info, force_update=True)

    # then
    assert checkout_info.checkout.tax_error == error_msg
    assert mocked_logger.call_count == 1
    assert len(mocked_logger.call_args) == 2
    assert mocked_logger.call_args[0][0] == error_msg
    assert mocked_logger.call_args[1]["extra"]["errors"] == errors
    mock_set_base_prices.assert_called_once()


@pytest.mark.parametrize(
    "prices_entered_with_tax",
    [True, False],
)
@patch.object(logger, "warning")
@patch("saleor.checkout.calculations._set_checkout_base_prices")
def test_fetch_checkout_data_tax_data_missing_tax_id_empty_tax_data(
    mock_set_base_prices,
    mocked_logger,
    prices_entered_with_tax,
    checkout_with_single_item,
):
    # given
    checkout = checkout_with_single_item

    channel = checkout.channel
    channel.tax_configuration.tax_app_id = None
    channel.tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    channel.tax_configuration.save()

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
    fetch_checkout_data(checkout_info, manager, checkout_lines_info, force_update=True)

    # then
    # In case the app identifier is not set, in case of error in tax data, it's skipped.
    assert not checkout_info.checkout.tax_error
    assert mocked_logger.call_count == 0
    mock_set_base_prices.assert_not_called()


@patch("saleor.plugins.avatax.plugin.get_checkout_tax_data")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.DeprecatedAvataxPlugin"])
def test_fetch_order_data_plugin_tax_data_with_negative_values(
    mock_get_tax_data,
    checkout_with_item_and_shipping,
    caplog,
    plugin_configuration,  # noqa: F811
):
    # given
    checkout = checkout_with_item_and_shipping

    channel = checkout.channel
    channel.tax_configuration.tax_app_id = DeprecatedAvataxPlugin.PLUGIN_IDENTIFIER
    channel.tax_configuration.save(update_fields=["tax_app_id"])

    tax_data = {
        "lines": {
            str(checkout.lines.first().id): {
                "lineAmount": 30.0000,
                "quantity": 3.0,
                "itemCode": "SKU_A",
            },
            "Shipping": {
                "lineAmount": -8.1300,
                "quantity": 1.0,
                "itemCode": "Shipping",
            },
        }
    }
    mock_get_tax_data.return_value = tax_data

    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines_info, manager)

    # when
    fetch_checkout_data(checkout_info, manager, checkout_lines_info, force_update=True)

    # then
    assert checkout.tax_error == TaxDataErrorMessage.NEGATIVE_VALUE
    assert TaxDataErrorMessage.NEGATIVE_VALUE in caplog.text
    assert caplog.records[0].checkout_id == to_global_id_or_none(checkout)


@patch("saleor.plugins.avatax.plugin.get_checkout_tax_data")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.DeprecatedAvataxPlugin"])
def test_fetch_order_data_plugin_tax_data_price_overflow(
    mock_get_tax_data,
    checkout_with_item_and_shipping,
    caplog,
    plugin_configuration,  # noqa: F811
):
    # given
    checkout = checkout_with_item_and_shipping

    channel = checkout.channel
    channel.tax_configuration.tax_app_id = DeprecatedAvataxPlugin.PLUGIN_IDENTIFIER
    channel.tax_configuration.save(update_fields=["tax_app_id"])

    tax_data = {
        "lines": {
            str(checkout.lines.first().id): {
                "lineAmount": 3892370265647658029.0000,
                "quantity": 3.0,
                "itemCode": "SKU_A",
            },
            "Shipping": {
                "lineAmount": 8.1300,
                "quantity": 1.0,
                "itemCode": "Shipping",
            },
        }
    }
    mock_get_tax_data.return_value = tax_data

    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines_info, manager)

    # when
    fetch_checkout_data(checkout_info, manager, checkout_lines_info, force_update=True)

    # then
    assert checkout.tax_error == TaxDataErrorMessage.OVERFLOW
    assert TaxDataErrorMessage.OVERFLOW in caplog.text
    assert caplog.records[0].checkout_id == to_global_id_or_none(checkout)


def test_fetch_checkout_with_prior_price_change(
    fetch_kwargs,
    checkout_with_items,
):
    # given
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])
    line = checkout_with_items.lines.first()
    listing = ProductVariantChannelListing.objects.filter(
        variant=line.variant, channel=checkout_with_items.channel
    ).first()
    new_prior_price_amount = Decimal(7)
    assert listing is not None
    assert listing.prior_price_amount != new_prior_price_amount
    listing.prior_price_amount = new_prior_price_amount
    listing.save(update_fields=["prior_price_amount"])

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout_with_items)

    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout_with_items, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
    }

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    line.refresh_from_db()
    assert line.prior_unit_price_amount == new_prior_price_amount


def test_fetch_checkout_with_prior_price_none(
    fetch_kwargs,
    checkout_with_items,
):
    # given
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])
    line = checkout_with_items.lines.first()
    listing = ProductVariantChannelListing.objects.filter(
        variant=line.variant, channel=checkout_with_items.channel
    ).first()
    assert listing is not None
    listing.prior_price_amount = None
    listing.save(update_fields=["prior_price_amount"])

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout_with_items)

    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout_with_items, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
    }

    # when
    fetch_checkout_data(**fetch_kwargs)

    # then
    line.refresh_from_db()
    assert line.prior_unit_price_amount is None
    assert line.currency is not None


def test_fetch_checkout_data_updates_status_for_zero_amount_checkout_with_lines(
    checkout_with_item_total_0,
):
    # given
    lines, _ = fetch_checkout_lines(checkout_with_item_total_0)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_item_total_0, lines, manager)

    assert checkout_with_item_total_0.total.gross == zero_money(
        checkout_with_item_total_0.total.currency
    )
    assert checkout_with_item_total_0.authorize_status == CheckoutAuthorizeStatus.NONE
    assert checkout_with_item_total_0.charge_status == CheckoutChargeStatus.NONE
    assert bool(lines) is True

    # when
    fetch_checkout_data(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
    )

    # then
    checkout_with_item_total_0.refresh_from_db()
    assert checkout_with_item_total_0.authorize_status == CheckoutAuthorizeStatus.FULL
    assert checkout_with_item_total_0.charge_status == CheckoutChargeStatus.FULL


@pytest.mark.parametrize(
    ("gift_card_balance", "expected_authorize_status", "expected_charge_status"),
    [
        (0, CheckoutAuthorizeStatus.PARTIAL, CheckoutChargeStatus.PARTIAL),
        (10, CheckoutAuthorizeStatus.PARTIAL, CheckoutChargeStatus.PARTIAL),
        (20, CheckoutAuthorizeStatus.FULL, CheckoutChargeStatus.FULL),
        (40, CheckoutAuthorizeStatus.FULL, CheckoutChargeStatus.OVERCHARGED),
    ],
)
def test_fetch_checkout_data_considers_gift_cards_balance_when_updating_checkout_payment_status(
    checkout_with_gift_card,
    gift_card_balance,
    expected_authorize_status,
    expected_charge_status,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_gift_card
    gift_card = checkout.gift_cards.first()
    gift_card.initial_balance_amount = Decimal(gift_card_balance)
    gift_card.current_balance_amount = Decimal(gift_card_balance)
    gift_card.save()

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    address = checkout.shipping_address or checkout.billing_address

    assert checkout.authorize_status == CheckoutAuthorizeStatus.NONE
    assert checkout.charge_status == CheckoutChargeStatus.NONE

    transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
    )

    total = calculate_checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    assert total.gross.amount == Decimal(30)

    # when
    fetch_checkout_data(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
    )

    # then
    checkout.refresh_from_db()
    assert checkout.authorize_status == expected_authorize_status
    assert checkout.charge_status == expected_charge_status


def test_fetch_checkout_data_checkout_removed_before_save(
    checkout_with_prices,
):
    # given
    checkout = checkout_with_prices
    currency = checkout.currency
    checkout.price_expiration = timezone.now()
    checkout.save(update_fields=["price_expiration"])
    start_total_price = checkout.total
    lines = list(checkout.lines.all())

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout)
    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
    }

    # when
    def delete_checkout(*args, **kwargs):
        # Simulate checkout deletion. We can't run `delete()` on `checkout_with_prices`, because
        # it's would pass `checkout` without `pk` to `checkout_info`.
        Checkout.objects.filter(pk=checkout.pk).delete()

    with race_condition.RunAfter(
        "saleor.checkout.calculations._calculate_and_add_tax", delete_checkout
    ):
        result_checkout_info, result_lines_info = fetch_checkout_data(**fetch_kwargs)

    # then
    # Check if checkout was deleted.
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    # Check if prices are recalculated and returned in info objects.
    assert start_total_price != result_checkout_info.checkout.total
    assert result_checkout_info.checkout.total is not None
    assert result_checkout_info.checkout.total > zero_taxed_money(currency)

    for line, result_line in zip(lines, result_lines_info, strict=True):
        assert line.total_price != result_line.line.total_price
        assert result_line.line.total_price is not None
        assert result_line.line.total_price > zero_taxed_money(currency)


def test_fetch_checkout_data_checkout_updated_during_price_recalculation(
    checkout_with_prices,
):
    # given
    checkout = checkout_with_prices
    currency = checkout.currency
    checkout.price_expiration = timezone.now()
    checkout.save(update_fields=["price_expiration", "last_change"])
    checkout.refresh_from_db()
    total_price_before_recalculation = checkout.total
    last_change_before_recalculation = checkout.last_change
    lines = list(checkout.lines.all())

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout)
    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
    }
    expected_email = "new_email@example.com"
    freeze_time_str = "2024-01-01T12:00:00+00:00"

    # when
    def modify_checkout(*args, **kwargs):
        with freeze_time(freeze_time_str):
            checkout_to_modify = Checkout.objects.get(pk=checkout.pk)
            checkout_to_modify.lines.update(quantity=F("quantity") + 1)
            checkout_to_modify.email = expected_email
            checkout_to_modify.save(update_fields=["email", "last_change"])

    with race_condition.RunAfter(
        "saleor.checkout.calculations._calculate_and_add_tax", modify_checkout
    ):
        result_checkout_info, result_lines_info = fetch_checkout_data(**fetch_kwargs)

    # then
    # Check if prices are recalculated and returned in info objects.
    assert result_checkout_info.checkout.total != total_price_before_recalculation
    assert result_checkout_info.checkout.total is not None
    assert result_checkout_info.checkout.total > zero_taxed_money(currency)

    for line, result_line in zip(lines, result_lines_info, strict=True):
        assert line.total_price != result_line.line.total_price
        assert result_line.line.total_price is not None
        assert result_line.line.total_price > zero_taxed_money(currency)
        assert result_line.line.quantity == line.quantity

    # Check if database contains updated checkout by other requests.
    checkout.refresh_from_db()
    assert checkout.last_change != last_change_before_recalculation
    assert checkout.last_change.isoformat() == freeze_time_str
    assert checkout.email == expected_email
    for old_line, new_line in zip(lines, checkout.lines.all(), strict=True):
        assert old_line.quantity + 1 == new_line.quantity


def test_fetch_checkout_data_checkout_deleted_during_discount_recalculation(
    checkout_with_item_and_order_discount,
):
    # given
    checkout = checkout_with_item_and_order_discount
    checkout.price_expiration = timezone.now()
    checkout.save(update_fields=["price_expiration"])

    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(checkout)
    fetch_kwargs = {
        "checkout_info": fetch_checkout_info(checkout, lines_info, manager),
        "manager": manager,
        "lines": lines_info,
    }

    # when
    def delete_checkout(*args, **kwargs):
        Checkout.objects.filter(pk=checkout.pk).delete()

    with patch(
        "saleor.checkout.calculations.recalculate_discounts",
        side_effect=delete_checkout,
    ):
        result_checkout_info, result_lines_info = fetch_checkout_data(**fetch_kwargs)

    # then
    # Check if checkout was deleted.
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    assert result_checkout_info.checkout.total is not None
    assert result_lines_info

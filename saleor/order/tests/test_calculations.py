from decimal import Decimal
from typing import Literal, Union
from unittest.mock import Mock, patch, sentinel

import pytest
from django.test import override_settings
from prices import Money, TaxedMoney

from ...core.prices import quantize_price
from ...core.taxes import (
    TaxData,
    TaxDataErrorMessage,
    TaxError,
    TaxLineData,
    zero_taxed_money,
)
from ...discount import DiscountValueType
from ...graphql.core.utils import to_global_id_or_none
from ...plugins import PLUGIN_IDENTIFIER_PREFIX
from ...plugins.avatax.plugin import AvataxPlugin
from ...plugins.avatax.tests.conftest import plugin_configuration  # noqa: F401
from ...plugins.manager import get_plugins_manager
from ...plugins.tests.sample_plugins import PluginSample
from ...tax import TaxCalculationStrategy
from ...tax.calculations.order import update_order_prices_with_flat_rates
from .. import OrderStatus, calculations
from ..interface import OrderTaxedPricesData


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.UNCONFIRMED
    return order_with_lines


@pytest.fixture
def order_lines(order_with_lines):
    return order_with_lines.lines.all()


@pytest.fixture
def tax_data(order_with_lines, order_lines):
    order = order_with_lines
    currency = order.currency
    tax_rate = Decimal("0.23")
    shipping_tax_rate = Decimal("0.17")
    lines = []
    for i, line in enumerate(order_lines, start=1):
        line_tax_rate = tax_rate + Decimal(f"{i}") / 100
        lines.append(
            TaxLineData(
                total_net_amount=quantize_price(line.total_price.net.amount, currency),
                total_gross_amount=quantize_price(
                    line.total_price.net.amount * (1 + line_tax_rate), currency
                ),
                tax_rate=line_tax_rate * 100,
            )
        )

    shipping_net = quantize_price(order.shipping_price.net.amount, currency)
    shipping_gross = quantize_price(
        order.shipping_price.net.amount * (1 + shipping_tax_rate), currency
    )
    return TaxData(
        shipping_price_net_amount=shipping_net,
        shipping_price_gross_amount=shipping_gross,
        shipping_tax_rate=shipping_tax_rate * 100,
        lines=lines,
    )


@pytest.fixture
def tax_data_prices_entered_with_tax(order_with_lines, order_lines):
    order = order_with_lines
    tax_rate = Decimal("0.23")
    shipping_tax_rate = Decimal("0.17")
    currency = order.currency
    lines = []
    for i, line in enumerate(order_lines, start=1):
        line_tax_rate = tax_rate + Decimal(f"{i}") / 100
        lines.append(
            TaxLineData(
                total_net_amount=quantize_price(
                    line.total_price.net.amount / (1 + line_tax_rate), currency
                ),
                total_gross_amount=quantize_price(
                    line.total_price.net.amount, currency
                ),
                tax_rate=line_tax_rate * 100,
            )
        )

    shipping_net = quantize_price(
        order.shipping_price.net.amount / (1 + shipping_tax_rate), currency
    )
    shipping_gross = quantize_price(order.shipping_price.net.amount, currency)
    return TaxData(
        shipping_price_net_amount=shipping_net,
        shipping_price_gross_amount=shipping_gross,
        shipping_tax_rate=shipping_tax_rate * 100,
        lines=lines,
    )


def create_taxed_money(net: Decimal, gross: Decimal, currency: str) -> TaxedMoney:
    return TaxedMoney(net=Money(net, currency), gross=Money(gross, currency))


def create_order_taxed_prices_data(
    net: Decimal, gross: Decimal, currency: str
) -> OrderTaxedPricesData:
    return OrderTaxedPricesData(
        undiscounted_price=create_taxed_money(net, gross, currency),
        price_with_discounts=create_taxed_money(net, gross, currency),
    )


def test_recalculate_with_plugins(order_with_lines, order_lines, tax_data):
    # given
    order = order_with_lines
    currency = order.currency
    lines = list(order_lines)

    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    unit_prices = []
    for line, total_price in zip(lines, total_prices):
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=total_price.undiscounted_price / line.quantity,
                price_with_discounts=total_price.price_with_discounts / line.quantity,
            )
        )
    tax_rates = [line.tax_rate for line in tax_data.lines]
    shipping_tax_rate = tax_data.shipping_tax_rate
    shipping = get_taxed_money(tax_data, "shipping_price", currency)
    subtotal = sum(
        (get_taxed_money(line, "total", currency) for line in tax_data.lines),
        zero_taxed_money(order.currency),
    )
    total = shipping + subtotal

    manager = Mock(
        calculate_order_line_unit=Mock(side_effect=unit_prices),
        calculate_order_line_total=Mock(side_effect=total_prices),
        get_order_shipping_tax_rate=Mock(return_value=shipping_tax_rate),
        get_order_line_tax_rate=Mock(side_effect=tax_rates),
        calculate_order_shipping=Mock(return_value=shipping),
        calculate_order_total=Mock(return_value=total),
    )

    # when
    calculations._recalculate_with_plugins(manager, order, lines, False)

    # then
    assert order.total == total
    assert order.shipping_price == shipping
    assert order.shipping_tax_rate == shipping_tax_rate

    for line_unit, line_total, tax_rate, line in zip(
        unit_prices, total_prices, tax_rates, lines
    ):
        undiscounted_unit_gross = line_unit.undiscounted_price.net.amount * (
            1 + (tax_rate / 100)
        )
        undiscounted_total_gross = line_total.undiscounted_price.net.amount * (
            1 + (tax_rate / 100)
        )
        assert line.unit_price == line_unit.price_with_discounts
        assert line.undiscounted_unit_price.net == line_unit.undiscounted_price.net
        assert line.undiscounted_unit_price.gross.amount == undiscounted_unit_gross
        assert line.undiscounted_unit_price == line_unit.undiscounted_price
        assert line.total_price == line_total.price_with_discounts
        assert line.undiscounted_total_price == line_total.undiscounted_price
        assert line.undiscounted_total_price.net == line_total.undiscounted_price.net
        assert line.undiscounted_total_price.gross.amount == undiscounted_total_gross
        assert tax_rate == line.tax_rate


@pytest.mark.parametrize(
    "mocked_method_name",
    [
        "calculate_order_line_unit",
        "calculate_order_line_total",
        "get_order_line_tax_rate",
        "calculate_order_shipping",
        "get_order_shipping_tax_rate",
    ],
)
def test_recalculate_with_plugins_tax_error(
    order_with_lines, order_lines, mocked_method_name
):
    # given
    order = order_with_lines
    lines = order_lines
    zero_money = zero_taxed_money(order.currency)
    zero_prices = OrderTaxedPricesData(
        undiscounted_price=zero_money,
        price_with_discounts=zero_money,
    )
    manager_methods = {
        "calculate_order_line_unit": Mock(return_value=zero_prices),
        "calculate_order_line_total": Mock(return_value=zero_prices),
        "get_order_shipping_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_order_line_tax_rate": Mock(return_value=Decimal("0.00")),
        "calculate_order_shipping": Mock(return_value=zero_money),
        mocked_method_name: Mock(side_effect=TaxError()),
    }
    manager = Mock(**manager_methods)

    # when
    calculations._recalculate_with_plugins(manager, order, lines, False)

    # then
    # no exception is raised


def test_recalculate_with_plugins_tax_error_line_prices(
    order_with_lines, order_lines, tax_data
):
    # given
    order = order_with_lines
    currency = order.currency
    lines = list(order_lines)
    error_line = order_lines[0]
    old_line_unit_price = error_line.unit_price
    old_line_undiscounted_unit_price = error_line.undiscounted_unit_price
    old_line_total_price = error_line.total_price
    old_line_undiscounted_total_price = error_line.undiscounted_total_price
    old_line_tax_rate = error_line.tax_rate

    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    unit_prices = []
    for line, total_price in zip(lines, total_prices):
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=total_price.undiscounted_price / line.quantity,
                price_with_discounts=total_price.price_with_discounts / line.quantity,
            )
        )
    tax_rates = [line.tax_rate for line in tax_data.lines]
    shipping_tax_rate = tax_data.shipping_tax_rate
    shipping = get_taxed_money(tax_data, "shipping_price", currency)

    subtotal = error_line.total_price + sum(
        [get_taxed_money(line, "total", currency) for line in tax_data.lines[1:]],
        zero_taxed_money(currency),
    )
    total = shipping + subtotal

    manager = Mock(
        calculate_order_line_unit=Mock(side_effect=[TaxError] + unit_prices[1:]),
        calculate_order_line_total=Mock(side_effect=total_prices[1:]),
        get_order_shipping_tax_rate=Mock(return_value=shipping_tax_rate),
        get_order_line_tax_rate=Mock(side_effect=tax_rates[1:]),
        calculate_order_shipping=Mock(return_value=shipping),
        calculate_order_total=Mock(return_value=total),
    )

    # when
    calculations._recalculate_with_plugins(manager, order, lines, False)

    # then
    assert order.total == total
    assert order.shipping_price == shipping
    assert order.shipping_tax_rate == shipping_tax_rate

    assert old_line_unit_price == error_line.unit_price
    assert old_line_undiscounted_unit_price == error_line.undiscounted_unit_price
    assert old_line_total_price == error_line.total_price
    assert old_line_undiscounted_total_price == error_line.undiscounted_total_price
    assert old_line_tax_rate == error_line.tax_rate

    for line_unit, line_total, tax_rate, line in list(
        zip(unit_prices, total_prices, tax_rates, lines)
    )[1:]:
        undiscounted_unit_gross = line_unit.undiscounted_price.net.amount * (
            1 + (tax_rate / 100)
        )
        undiscounted_total_gross = line_total.undiscounted_price.net.amount * (
            1 + (tax_rate / 100)
        )
        assert line.unit_price == line_unit.price_with_discounts
        assert line.undiscounted_unit_price.net == line_unit.undiscounted_price.net
        assert line.undiscounted_unit_price.gross.amount == undiscounted_unit_gross
        assert line.undiscounted_unit_price == line_unit.undiscounted_price
        assert line.total_price == line_total.price_with_discounts
        assert line.undiscounted_total_price == line_total.undiscounted_price
        assert line.undiscounted_total_price.net == line_total.undiscounted_price.net
        assert line.undiscounted_total_price.gross.amount == undiscounted_total_gross
        assert tax_rate == line.tax_rate


def test_recalculate_with_plugins_tax_error_shipping_price(
    order_with_lines, order_lines, tax_data
):
    # given
    order = order_with_lines
    currency = order.currency
    lines = list(order_lines)

    old_shipping_price = order.shipping_price
    old_shipping_tax_rate = order.shipping_tax_rate

    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    unit_prices = []
    for line, total_price in zip(lines, total_prices):
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=total_price.undiscounted_price / line.quantity,
                price_with_discounts=total_price.price_with_discounts / line.quantity,
            )
        )
    tax_rates = [line.tax_rate for line in tax_data.lines]
    shipping_tax_rate = tax_data.shipping_tax_rate

    subtotal = sum(
        [get_taxed_money(line, "total", currency) for line in tax_data.lines],
        zero_taxed_money(currency),
    )

    manager = Mock(
        calculate_order_line_unit=Mock(side_effect=unit_prices),
        calculate_order_line_total=Mock(side_effect=total_prices),
        get_order_shipping_tax_rate=Mock(return_value=shipping_tax_rate),
        get_order_line_tax_rate=Mock(side_effect=tax_rates),
        calculate_order_shipping=Mock(side_effect=TaxError),
        calculate_order_total=Mock(return_value=subtotal + order.shipping_price),
    )

    # when
    calculations._recalculate_with_plugins(manager, order, lines, False)

    # then
    assert order.total == subtotal + old_shipping_price
    assert order.shipping_price == old_shipping_price
    assert order.shipping_tax_rate == old_shipping_tax_rate

    for line_unit, line_total, tax_rate, line in zip(
        unit_prices, total_prices, tax_rates, lines
    ):
        undiscounted_unit_gross = line_unit.undiscounted_price.net.amount * (
            1 + (tax_rate / 100)
        )
        undiscounted_total_gross = line_total.undiscounted_price.net.amount * (
            1 + (tax_rate / 100)
        )
        assert line.unit_price == line_unit.price_with_discounts
        assert line.undiscounted_unit_price.net == line_unit.undiscounted_price.net
        assert line.undiscounted_unit_price.gross.amount == undiscounted_unit_gross
        assert line.undiscounted_unit_price == line_unit.undiscounted_price
        assert line.total_price == line_total.price_with_discounts
        assert line.undiscounted_total_price == line_total.undiscounted_price
        assert line.undiscounted_total_price.net == line_total.undiscounted_price.net
        assert line.undiscounted_total_price.gross.amount == undiscounted_total_gross
        assert tax_rate == line.tax_rate


def test_recalculate_with_plugins_order_discounts_and_total_undiscounted_price_changed(
    draft_order, order_lines, shipping_method_weight_based, tax_data
):
    # given
    order = draft_order
    currency = order.currency
    lines = list(order_lines)

    old_shipping_price = order.shipping_price

    old_undiscounted_amount = draft_order.undiscounted_total
    discount_amount = old_undiscounted_amount.net
    order_discount = draft_order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=100,
        reason="Discount reason",
        amount=discount_amount,
    )

    new_shipping_price = Money(20, currency)
    shipping_listing = shipping_method_weight_based.channel_listings.get(
        channel=order.channel
    )
    shipping_listing.price = new_shipping_price
    shipping_listing.save(update_fields=["price_amount"])

    order.undiscounted_base_shipping_price = new_shipping_price
    order.base_shipping_price = new_shipping_price
    order.shipping_method = shipping_method_weight_based
    order.shipping_method_name = shipping_method_weight_based.name
    order.save(
        update_fields=[
            "base_shipping_price_amount",
            "shipping_method",
            "shipping_method_name",
        ]
    )

    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    unit_prices = []
    for line, total_price in zip(lines, total_prices):
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=total_price.undiscounted_price / line.quantity,
                price_with_discounts=total_price.price_with_discounts / line.quantity,
            )
        )
    shipping_tax_rate = 0

    manager = get_plugins_manager(allow_replica=True)

    # when
    calculations._recalculate_with_plugins(manager, order, lines, False)

    # then
    order_discount.refresh_from_db()
    assert order.undiscounted_total.net == old_undiscounted_amount.net + (
        new_shipping_price - old_shipping_price.net
    )
    assert order_discount.amount == order.undiscounted_total.net
    assert order.total == zero_taxed_money(currency)
    assert order.shipping_price == zero_taxed_money(currency)
    assert order.shipping_tax_rate == shipping_tax_rate


def test_recalculate_prices_total_shipping_price_changed(
    draft_order, order_lines, shipping_method_weight_based
):
    """Test that discounts are properly updated when shipping price changes."""
    # given
    order = draft_order
    currency = order.currency
    old_shipping_price = order.shipping_price

    old_undiscounted_amount = draft_order.undiscounted_total
    discount_amount = old_undiscounted_amount.net
    # add order manual discount
    order_discount = draft_order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=100,
        reason="Discount reason",
        amount=discount_amount,
    )

    # change the shipping, increase the shipping price
    new_shipping_price = Money(20, currency)
    shipping_listing = shipping_method_weight_based.channel_listings.get(
        channel=order.channel
    )
    shipping_listing.price = new_shipping_price
    shipping_listing.save(update_fields=["price_amount"])

    order.base_shipping_price = new_shipping_price
    order.undiscounted_base_shipping_price = new_shipping_price
    order.shipping_method = shipping_method_weight_based
    order.shipping_method_name = shipping_method_weight_based.name
    order.save(
        update_fields=[
            "base_shipping_price_amount",
            "shipping_method",
            "shipping_method_name",
        ]
    )

    # when
    calculations._recalculate_prices(
        order, get_plugins_manager(allow_replica=True), order_lines
    )

    # then
    order_discount.refresh_from_db()
    assert order.undiscounted_total.net == old_undiscounted_amount.net + (
        new_shipping_price - old_shipping_price.net
    )
    assert order_discount.amount == order.undiscounted_total.net


def test_recalculate_prices_line_quantity_changed(
    draft_order, order_lines, shipping_method_weight_based
):
    """Test that discounts are properly updated when line quantities change."""
    # given
    order = draft_order

    old_undiscounted_amount = draft_order.undiscounted_total
    discount_amount = old_undiscounted_amount.net
    # add order manual discount
    order_discount = draft_order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=100,
        reason="Discount reason",
        amount=discount_amount,
    )

    line = order_lines.first()
    line.quantity += 1
    line.save(update_fields=["quantity"])

    # when
    calculations._recalculate_prices(
        order, get_plugins_manager(allow_replica=True), order_lines
    )

    # then
    order_discount.refresh_from_db()
    assert (
        order.undiscounted_total.net
        == old_undiscounted_amount.net + line.unit_price.net
    )
    assert order_discount.amount == order.undiscounted_total.net


@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_apply_tax_data(
    prices_entered_with_tax,
    order_with_lines,
    order_lines,
    tax_data,
    tax_data_prices_entered_with_tax,
):
    # given
    order = order_with_lines
    lines = order_lines
    tax_data = tax_data_prices_entered_with_tax if prices_entered_with_tax else tax_data

    # when
    calculations._apply_tax_data(order, lines, tax_data, prices_entered_with_tax)

    # then
    assert str(order.shipping_price.net.amount) == str(
        tax_data.shipping_price_net_amount
    )
    assert str(order.shipping_price.gross.amount) == str(
        tax_data.shipping_price_gross_amount
    )
    for line, tax_line in zip(lines, tax_data.lines):
        assert str(line.total_price.net.amount) == str(tax_line.total_net_amount)
        assert str(line.total_price.gross.amount) == str(tax_line.total_gross_amount)
        assert str(line.undiscounted_total_price.net.amount) == str(
            tax_line.total_net_amount
        )
        assert str(line.undiscounted_total_price.gross.amount) == str(
            tax_line.total_gross_amount
        )

    subtotal_gross = sum(line.total_price.gross.amount for line in lines)
    subtotal_net = sum(line.total_price.net.amount for line in lines)
    undiscounted_subtotal_gross = sum(line.total_price.gross.amount for line in lines)
    undiscounted_subtotal_net = sum(line.total_price.net.amount for line in lines)

    assert order.subtotal_gross_amount == subtotal_gross
    assert order.subtotal_net_amount == subtotal_net
    assert (
        order.total_gross_amount == subtotal_gross + order.shipping_price_gross_amount
    )
    assert order.total_net_amount == subtotal_net + order.shipping_price_net_amount
    assert (
        order.undiscounted_total_gross_amount
        == undiscounted_subtotal_gross + order.shipping_price_gross_amount
    )
    assert (
        order.undiscounted_total_net_amount
        == undiscounted_subtotal_net + order.shipping_price_net_amount
    )


@pytest.fixture
def manager_with_mocked_plugins_calculations(
    plugins_manager, tax_data, order_with_lines
):
    currency = order_with_lines.currency
    plugins_manager.get_order_shipping_tax_rate = Mock(
        return_value=tax_data.shipping_tax_rate
    )
    plugins_manager.calculate_order_shipping = Mock(
        return_value=get_taxed_money(tax_data, "shipping_price", currency)
    )

    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    plugins_manager.calculate_order_line_total = Mock(side_effect=total_prices)

    unit_prices = []
    for line, total_price in zip(order_with_lines.lines.all(), total_prices):
        unit_price = quantize_price(
            total_price.price_with_discounts / line.quantity, currency
        )
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=unit_price,
                price_with_discounts=unit_price,
            )
        )

    plugins_manager.calculate_order_line_unit = Mock(side_effect=unit_prices)
    plugins_manager.get_order_line_tax_rate = Mock(
        side_effect=[line.tax_rate for line in tax_data.lines]
    )
    return plugins_manager


@pytest.fixture
def fetch_kwargs(order_with_lines, plugins_manager):
    return {
        "order": order_with_lines,
        "manager": plugins_manager,
        "force_update": True,
    }


@pytest.fixture
def fetch_kwargs_with_lines(order_with_lines, order_lines, plugins_manager):
    return {
        "order": order_with_lines,
        "lines": order_lines,
        "manager": plugins_manager,
    }


def get_taxed_money(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["unit", "total", "subtotal", "shipping_price"],
    currency: str,
    exempt_taxes: bool = False,
    prices_entered_with_taxes: bool = False,
) -> TaxedMoney:
    if prices_entered_with_taxes:
        gross_value = Money(getattr(obj, f"{attr}_gross_amount"), currency)
        if exempt_taxes:
            net_value = gross_value
        else:
            net_value = Money(getattr(obj, f"{attr}_net_amount"), currency)
    else:
        net_value = Money(getattr(obj, f"{attr}_net_amount"), currency)
        if exempt_taxes:
            gross_value = net_value
        else:
            gross_value = Money(getattr(obj, f"{attr}_gross_amount"), currency)

    return TaxedMoney(net_value, gross_value)


def get_order_priced_taxes_data(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["unit", "total", "subtotal", "shipping_price"],
    currency: str,
) -> OrderTaxedPricesData:
    return OrderTaxedPricesData(
        undiscounted_price=get_taxed_money(obj, attr, currency),
        price_with_discounts=get_taxed_money(obj, attr, currency),
    )


def test_fetch_order_prices_if_expired_plugins(
    plugins_manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
):
    # given
    currency = order_with_lines.currency
    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    subtotal = zero_taxed_money(currency)
    unit_prices = []
    for line, total_price in zip(order_with_lines.lines.all(), total_prices):
        subtotal += total_price.price_with_discounts
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=total_price.undiscounted_price / line.quantity,
                price_with_discounts=total_price.price_with_discounts / line.quantity,
            )
        )
    tax_rates = [line.tax_rate / 100 for line in tax_data.lines]
    shipping_tax_rate = tax_data.shipping_tax_rate / 100
    shipping = get_taxed_money(tax_data, "shipping_price", currency)

    total = subtotal + shipping

    plugins_manager.calculate_order_line_unit = Mock(side_effect=unit_prices)
    plugins_manager.calculate_order_line_total = Mock(side_effect=total_prices)
    plugins_manager.get_order_line_tax_rate = Mock(side_effect=tax_rates)
    plugins_manager.calculate_order_shipping = Mock(return_value=shipping)
    plugins_manager.get_order_shipping_tax_rate = Mock(return_value=shipping_tax_rate)
    plugins_manager.get_taxes_for_order = Mock(return_value=None)
    plugins_manager.calculate_order_total = Mock(return_value=total)

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.shipping_price == get_taxed_money(
        tax_data, "shipping_price", currency
    )
    assert order_with_lines.shipping_tax_rate == tax_data.shipping_tax_rate / 100
    assert order_with_lines.total == total
    for order_line, tax_line, unit_price in zip(
        order_with_lines.lines.all(), tax_data.lines, unit_prices
    ):
        assert order_line.unit_price == unit_price.price_with_discounts
        assert order_line.total_price == get_taxed_money(tax_line, "total", currency)
        assert order_line.tax_rate == tax_line.tax_rate / 100


@patch(
    "saleor.order.calculations.update_order_prices_with_flat_rates",
    wraps=update_order_prices_with_flat_rates,
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_fetch_order_prices_if_expired_flat_rates(
    mocked_update_order_prices_with_flat_rates,
    order_with_lines,
    fetch_kwargs,
    prices_entered_with_tax,
):
    # given
    order = order_with_lines
    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)
    order.refresh_from_db()
    line = order.lines.first()

    # then
    mocked_update_order_prices_with_flat_rates.assert_called_once_with(
        order,
        list(order.lines.all()),
        prices_entered_with_tax,
        database_connection_name=order.lines.db,
    )
    assert line.tax_rate == Decimal("0.2300")
    assert order.shipping_tax_rate == Decimal("0.2300")


def test_fetch_order_prices_if_expired_webhooks_success(
    plugins_manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
):
    # given
    currency = order_with_lines.currency
    plugins_manager.get_taxes_for_order = Mock(return_value=tax_data)

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    shipping_price = get_taxed_money(tax_data, "shipping_price", currency)
    assert order_with_lines.shipping_price == shipping_price
    assert order_with_lines.shipping_tax_rate == tax_data.shipping_tax_rate / 100
    subtotal = zero_taxed_money(currency)
    for order_line, tax_line in zip(order_with_lines.lines.all(), tax_data.lines):
        line_total = get_taxed_money(tax_line, "total", currency)
        subtotal += line_total
        assert order_line.total_price == line_total
        assert order_line.unit_price == line_total / order_line.quantity
        assert order_line.tax_rate == tax_line.tax_rate / 100
    assert order_with_lines.total == subtotal + shipping_price


@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_fetch_order_prices_if_expired_recalculate_all_prices(
    plugins_manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
    tax_data_prices_entered_with_tax,
    prices_entered_with_tax,
):
    # given
    tax_data = tax_data_prices_entered_with_tax if prices_entered_with_tax else tax_data
    tc = order_with_lines.channel.tax_configuration
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.save(update_fields=["prices_entered_with_tax"])

    currency = order_with_lines.currency
    order_with_lines.total_net_amount = Decimal("0.00")
    order_with_lines.total_gross_amount = Decimal("0.00")
    order_with_lines.undiscounted_total_net_amount = Decimal("0.00")
    order_with_lines.undiscounted_total_gross_amount = Decimal("0.00")
    order_with_lines.save()
    plugins_manager.get_taxes_for_order = Mock(return_value=tax_data)

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    shipping_price = get_taxed_money(tax_data, "shipping_price", currency)
    assert order_with_lines.shipping_price == shipping_price
    assert order_with_lines.shipping_tax_rate == tax_data.shipping_tax_rate / 100
    subtotal = zero_taxed_money(currency)
    for order_line, tax_line in zip(order_with_lines.lines.all(), tax_data.lines):
        line_total = get_taxed_money(tax_line, "total", currency)
        subtotal += line_total
        assert order_line.total_price == line_total
        assert order_line.unit_price == quantize_price(
            line_total / order_line.quantity, currency
        )
        assert order_line.tax_rate == tax_line.tax_rate / 100
        assert order_line.undiscounted_total_price == line_total
        assert order_line.undiscounted_unit_price == quantize_price(
            line_total / order_line.quantity, currency
        )

    assert order_with_lines.undiscounted_total == subtotal + shipping_price
    assert order_with_lines.total == subtotal + shipping_price


@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_fetch_order_prices_when_tax_exemption(
    plugins_manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
    tax_data_prices_entered_with_tax,
    prices_entered_with_tax,
):
    """Test tax exemption when taxes are included in prices.

    When Order.tax_exemption = True and SiteSettings.include_taxes_in_prices = True
    taxes should be calculated by plugins and net prices returned.
    """
    # given
    tax_data = tax_data_prices_entered_with_tax if prices_entered_with_tax else tax_data
    tc = order_with_lines.channel.tax_configuration
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.save(update_fields=["prices_entered_with_tax"])

    currency = order_with_lines.currency
    order_with_lines.total_net_amount = Decimal("0.00")
    order_with_lines.total_gross_amount = Decimal("0.00")
    order_with_lines.undiscounted_total_net_amount = Decimal("0.00")
    order_with_lines.undiscounted_total_gross_amount = Decimal("0.00")
    order_with_lines.tax_exemption = True
    order_with_lines.save()
    plugins_manager.get_taxes_for_order = Mock(return_value=tax_data)

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    shipping_price = get_taxed_money(
        tax_data,
        "shipping_price",
        currency,
        exempt_taxes=True,
        prices_entered_with_taxes=prices_entered_with_tax,
    )
    assert order_with_lines.shipping_price == shipping_price
    assert order_with_lines.shipping_tax_rate == Decimal("0.00")
    subtotal = zero_taxed_money(currency)
    for order_line, tax_line in zip(order_with_lines.lines.all(), tax_data.lines):
        line_total = get_taxed_money(
            tax_line,
            "total",
            currency,
            exempt_taxes=True,
            prices_entered_with_taxes=prices_entered_with_tax,
        )
        subtotal += line_total
        assert order_line.total_price == line_total
        assert order_line.unit_price == quantize_price(
            line_total / order_line.quantity, currency
        )
        assert order_line.tax_rate == Decimal("0.00")
        assert order_line.undiscounted_total_price == line_total
        assert order_line.undiscounted_unit_price == quantize_price(
            line_total / order_line.quantity, currency
        )

    assert order_with_lines.undiscounted_total == subtotal + shipping_price
    assert order_with_lines.total == subtotal + shipping_price


def test_fetch_order_prices_if_expired_prefetch(fetch_kwargs, order_lines):
    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    assert all(line._state.fields_cache for line in order_lines)


def test_fetch_order_prices_if_expired_prefetch_with_lines(
    fetch_kwargs_with_lines, order_lines
):
    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs_with_lines)

    # then
    assert all(line._state.fields_cache for line in order_lines)


def test_fetch_order_prices_if_expired_use_base_shipping_price(
    plugins_manager, fetch_kwargs, order_with_lines
):
    # given
    order = order_with_lines
    currency = order.currency
    shipping_channel_listing = order.shipping_method.channel_listings.get(
        channel=order.channel
    )
    expected_price = Money("2.00", currency)
    order.base_shipping_price = expected_price
    order.undiscounted_base_shipping_price = expected_price
    order.save()

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.base_shipping_price != shipping_channel_listing.price
    assert order_with_lines.base_shipping_price == expected_price
    assert order_with_lines.shipping_price == TaxedMoney(
        net=expected_price, gross=expected_price
    )


@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_fetch_order_prices_if_expired_flat_rates_and_no_tax_calc_strategy(
    order_with_lines,
    fetch_kwargs,
    prices_entered_with_tax,
):
    # given
    order = order_with_lines
    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.tax_calculation_strategy = None
    tc.save(update_fields=["prices_entered_with_tax", "tax_calculation_strategy"])

    country_code = order.shipping_address.country.code
    for line in order.lines.all():
        line.variant.product.tax_class.country_rates.update_or_create(
            country=country_code, rate=23
        )

    order.shipping_method.tax_class.country_rates.update_or_create(
        country=country_code, rate=23
    )

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)
    order.refresh_from_db()
    line = order.lines.first()

    assert line.tax_rate == Decimal("0.2300")
    assert order.shipping_tax_rate == Decimal("0.2300")


def test_fetch_order_prices_on_promotion_if_expired_recalculate_all_prices(
    plugins_manager,
    fetch_kwargs,
    order_with_lines,
    order_line_on_promotion,
    tax_data_prices_entered_with_tax,
):
    # given
    tax_data = tax_data_prices_entered_with_tax
    currency = order_with_lines.currency
    order_line_on_promotion.order = order_with_lines
    plugins_manager.get_taxes_for_order = Mock(return_value=tax_data)

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    shipping_price = get_taxed_money(tax_data, "shipping_price", currency)
    assert order_with_lines.shipping_price == shipping_price
    assert order_with_lines.shipping_tax_rate == tax_data.shipping_tax_rate / 100
    subtotal = zero_taxed_money(currency)
    undiscounted_subtotal = zero_taxed_money(currency)
    for order_line, tax_line in zip(order_with_lines.lines.all(), tax_data.lines):
        line_total = get_taxed_money(tax_line, "total", currency)
        subtotal += line_total
        undiscounted_subtotal += order_line.undiscounted_total_price
        assert order_line.total_price == line_total
        assert order_line.unit_price == quantize_price(
            line_total / order_line.quantity, currency
        )
        assert order_line.tax_rate == tax_line.tax_rate / 100

    assert order_with_lines.total != order_with_lines.undiscounted_total

    assert order_with_lines.undiscounted_total == undiscounted_subtotal + shipping_price
    assert order_with_lines.total == subtotal + shipping_price


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_unit(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_unit_price = create_taxed_money(
        Decimal("1234.0000"), Decimal("1234.0000"), "USD"
    )
    expected_line_undiscounted_unit_price = create_taxed_money(
        Decimal("5678.0000"), Decimal("5678.0000"), "USD"
    )

    order = Mock(currency="USD")
    order_line = Mock(
        pk=1,
        unit_price=expected_line_unit_price,
        undiscounted_unit_price=expected_line_undiscounted_unit_price,
    )
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_unit_price = calculations.order_line_unit(order, order_line, Mock())

    # then
    assert line_unit_price == OrderTaxedPricesData(
        undiscounted_price=expected_line_undiscounted_unit_price,
        price_with_discounts=expected_line_unit_price,
    )


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_total(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_total_price = create_taxed_money(
        Decimal("1234.0000"), Decimal("1234.0000"), "USD"
    )
    expected_line_undiscounted_total_price = create_taxed_money(
        Decimal("5678.0000"), Decimal("5678.0000"), "USD"
    )

    order = Mock(currency="USD")
    order_line = Mock(
        pk=1,
        total_price=expected_line_total_price,
        undiscounted_total_price=expected_line_undiscounted_total_price,
    )
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_total_price = calculations.order_line_total(order, order_line, Mock())

    # then
    assert line_total_price == OrderTaxedPricesData(
        undiscounted_price=expected_line_undiscounted_total_price,
        price_with_discounts=expected_line_total_price,
    )


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_tax_rate(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_tax_rate = sentinel.TAX_RATE

    order_line = Mock(pk=1, tax_rate=expected_line_tax_rate)
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_tax_rate = calculations.order_line_tax_rate(Mock(), order_line, Mock())

    # then
    assert line_tax_rate == expected_line_tax_rate


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_shipping(mocked_fetch_order_prices_if_expired):
    # given
    expected_shipping_price = Decimal("1234.0000")

    order = Mock(shipping_price=expected_shipping_price, currency="USD")
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    shipping_price = calculations.order_shipping(order, Mock())

    # then
    assert shipping_price == quantize_price(expected_shipping_price, order.currency)


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_shipping_tax_rate(mocked_fetch_order_prices_if_expired):
    # given
    expected_shipping_tax_rate = sentinel.SHIPPING_TAX_RATE

    order = Mock(shipping_tax_rate=expected_shipping_tax_rate)
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    shipping_tax_rate = calculations.order_shipping_tax_rate(order, Mock())

    # then
    assert shipping_tax_rate == expected_shipping_tax_rate


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_total(mocked_fetch_order_prices_if_expired):
    # given
    expected_total = Decimal("1234.0000")

    order = Mock(total=expected_total, currency="USD")
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    total = calculations.order_total(order, Mock())

    # then
    assert total == quantize_price(expected_total, order.currency)


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_subtotal(mocked_fetch_order_prices_if_expired):
    # given
    currency = "USD"
    manager = Mock()
    expected_line_totals = [
        TaxedMoney(Money(Decimal("1.00"), currency), Money(Decimal("1.00"), currency)),
        TaxedMoney(Money(Decimal("2.00"), currency), Money(Decimal("2.00"), currency)),
        TaxedMoney(Money(Decimal("4.00"), currency), Money(Decimal("4.00"), currency)),
    ]
    order = Mock(
        currency=currency,
        subtotal=TaxedMoney(
            Money(Decimal("7.00"), currency), Money(Decimal("7.00"), currency)
        ),
    )
    lines = []
    for expected_line_total in expected_line_totals:
        line = Mock(total_price=expected_line_total, currency=currency)
        lines.append(line)
    mocked_fetch_order_prices_if_expired.return_value = (order, lines)

    # when
    subtotal = calculations.order_subtotal(order, manager, lines)

    # then
    expected_subtotal = quantize_price(
        TaxedMoney(Money(Decimal("7.00"), currency), Money(Decimal("7.00"), currency)),
        currency,
    )
    assert subtotal == expected_subtotal


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_undiscounted_total(mocked_fetch_order_prices_if_expired):
    # given
    expected_undiscounted_total = Decimal("1234.0000")

    order = Mock(undiscounted_total=expected_undiscounted_total, currency="USD")
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    undiscounted_total = calculations.order_undiscounted_total(order, Mock())

    # then
    assert undiscounted_total == quantize_price(
        expected_undiscounted_total, order.currency
    )


@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_total")
@patch("saleor.plugins.manager.PluginsManager.get_taxes_for_order")
@override_settings(PLUGINS=["saleor.plugins.tests.sample_plugins.PluginSample"])
def test_fetch_order_data_calls_plugin(
    mock_get_taxes,
    mock_calculate_order_line_total,
    order_with_lines,
    order_lines,
):
    # given
    order = order_with_lines
    order.channel.tax_configuration.tax_app_id = (
        PLUGIN_IDENTIFIER_PREFIX + PluginSample.PLUGIN_ID
    )
    order.channel.tax_configuration.save()

    price = Money("10.0", currency=order.currency)
    mock_calculate_order_line_total.return_value = OrderTaxedPricesData(
        undiscounted_price=TaxedMoney(price, price),
        price_with_discounts=TaxedMoney(price, price),
    )

    fetch_kwargs = {
        "order": order,
        "manager": get_plugins_manager(allow_replica=False),
        "lines": order_lines,
        "force_update": True,
    }

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    assert mock_calculate_order_line_total.call_count == 2
    mock_get_taxes.assert_not_called()


@patch("saleor.order.calculations.validate_tax_data")
@patch("saleor.plugins.manager.PluginsManager.calculate_order_total")
@patch("saleor.plugins.manager.PluginsManager.get_taxes_for_order")
@patch("saleor.order.calculations._apply_tax_data")
@override_settings(PLUGINS=["saleor.plugins.tests.sample_plugins.PluginSample"])
def test_fetch_order_data_calls_tax_app(
    mock_apply_tax_data,
    mock_get_taxes,
    mock_calculate_order_total,
    mock_validate_tax_data,
    order_with_lines,
    order_lines,
):
    # given
    mock_validate_tax_data.return_value = False

    order = order_with_lines
    order.channel.tax_configuration.tax_app_id = "test.app"
    order.channel.tax_configuration.save()

    fetch_kwargs = {
        "order": order,
        "manager": get_plugins_manager(allow_replica=False),
        "lines": order_lines,
        "force_update": True,
    }

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    mock_apply_tax_data.assert_called_once()
    mock_get_taxes.assert_called_once()
    mock_calculate_order_total.assert_not_called()


def test_fetch_order_data_calls_inactive_plugin(
    order_with_lines,
    order_lines,
):
    # given
    order = order_with_lines
    order.channel.tax_configuration.tax_app_id = "plugin:test"
    order.channel.tax_configuration.save()

    fetch_kwargs = {
        "order": order,
        "manager": get_plugins_manager(allow_replica=False),
        "lines": order_lines,
        "force_update": True,
    }

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    assert order_with_lines.tax_error == "Empty tax data."


@pytest.mark.parametrize("tax_app_id", [None, "test.app"])
def test_recalculate_prices_empty_tax_data_logging_address(
    tax_app_id, draft_order, order_lines, address, caplog
):
    # given
    order = draft_order

    address.validation_skipped = True
    address.postal_code = "invalid postal code"
    address.save(update_fields=["postal_code", "validation_skipped"])

    order.shipping_address = address
    order.billing_address = address
    order.save(update_fields=["billing_address", "shipping_address"])

    order.channel.tax_configuration.tax_app_id = tax_app_id
    order.channel.tax_configuration.save()

    zero_money = zero_taxed_money(order.currency)
    zero_prices = OrderTaxedPricesData(
        undiscounted_price=zero_money,
        price_with_discounts=zero_money,
    )
    manager_methods = {
        "calculate_order_line_unit": Mock(side_effect=TaxError()),
        "calculate_order_line_total": Mock(return_value=zero_prices),
        "get_order_shipping_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_order_line_tax_rate": Mock(return_value=Decimal("0.00")),
        "calculate_order_shipping": Mock(return_value=zero_money),
        "get_taxes_for_order": Mock(return_value=None),
    }
    manager = Mock(**manager_methods)

    # when
    calculations._recalculate_prices(order, manager, order_lines)

    # then
    assert (
        f"Fetching tax data for order with address validation skipped. "
        f"Address ID: {address.pk}" in caplog.text
    )


@pytest.mark.parametrize(
    ("prices_entered_with_tax", "tax_app_id"),
    [(True, None), (True, "test.app"), (False, None), (False, "test.app")],
)
def test_fetch_order_data_tax_data_with_negative_values(
    prices_entered_with_tax,
    tax_app_id,
    order_with_lines,
    caplog,
):
    # given
    order = order_with_lines

    channel = order.channel
    channel.tax_configuration.tax_app_id = tax_app_id
    channel.tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    channel.tax_configuration.save()

    tax_data = TaxData(
        shipping_price_net_amount=Decimal("-1"),
        shipping_price_gross_amount=Decimal("1.5"),
        shipping_tax_rate=Decimal("50"),
        lines=[
            TaxLineData(
                total_net_amount=Decimal("2"),
                total_gross_amount=Decimal("3"),
                tax_rate=Decimal("50"),
            ),
            TaxLineData(
                total_net_amount=Decimal("4"),
                total_gross_amount=Decimal("6"),
                tax_rate=Decimal("50"),
            ),
        ],
    )

    zero_money = zero_taxed_money(order.currency)
    zero_prices = OrderTaxedPricesData(
        undiscounted_price=zero_money,
        price_with_discounts=zero_money,
    )
    manager_methods = {
        "calculate_order_line_unit": Mock(return_value=zero_prices),
        "calculate_order_line_total": Mock(return_value=zero_prices),
        "calculate_order_total": Mock(return_value=zero_money),
        "calculate_order_shipping": Mock(return_value=zero_money),
        "get_order_shipping_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_order_line_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_taxes_for_order": Mock(return_value=tax_data),
    }
    manager = Mock(**manager_methods)

    # when
    calculations.fetch_order_prices_if_expired(order, manager, None, True)

    # then
    assert order.tax_error == TaxDataErrorMessage.NEGATIVE_VALUE
    assert TaxDataErrorMessage.NEGATIVE_VALUE in caplog.text
    assert caplog.records[0].order_id == to_global_id_or_none(order)


@pytest.mark.parametrize(
    ("prices_entered_with_tax", "tax_app_id"),
    [(True, None), (True, "test.app"), (False, None), (False, "test.app")],
)
def test_fetch_order_data_tax_data_with_wrong_number_of_lines(
    prices_entered_with_tax,
    tax_app_id,
    order_with_lines,
    caplog,
):
    # given
    order = order_with_lines
    channel = order.channel
    channel.tax_configuration.tax_app_id = tax_app_id
    channel.tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    channel.tax_configuration.save()

    tax_data = TaxData(
        shipping_price_net_amount=Decimal("1"),
        shipping_price_gross_amount=Decimal("1.5"),
        shipping_tax_rate=Decimal("50"),
        lines=[
            TaxLineData(
                total_net_amount=Decimal("2"),
                total_gross_amount=Decimal("3"),
                tax_rate=Decimal("50"),
            ),
        ],
    )

    zero_money = zero_taxed_money(order.currency)
    zero_prices = OrderTaxedPricesData(
        undiscounted_price=zero_money,
        price_with_discounts=zero_money,
    )
    manager_methods = {
        "calculate_order_line_unit": Mock(return_value=zero_prices),
        "calculate_order_line_total": Mock(return_value=zero_prices),
        "calculate_order_total": Mock(return_value=zero_money),
        "calculate_order_shipping": Mock(return_value=zero_money),
        "get_order_shipping_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_order_line_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_taxes_for_order": Mock(return_value=tax_data),
    }
    manager = Mock(**manager_methods)

    # when
    calculations.fetch_order_prices_if_expired(order, manager, None, True)

    # then
    assert order.tax_error == TaxDataErrorMessage.LINE_NUMBER
    assert TaxDataErrorMessage.LINE_NUMBER in caplog.text
    assert caplog.records[0].order_id == to_global_id_or_none(order)


@pytest.mark.parametrize(
    ("prices_entered_with_tax", "tax_app_id"),
    [(True, None), (True, "test.app"), (False, None), (False, "test.app")],
)
def test_fetch_order_data_tax_data_with_price_overflow(
    prices_entered_with_tax,
    tax_app_id,
    order_with_lines,
    caplog,
):
    # given
    order = order_with_lines
    channel = order.channel
    channel.tax_configuration.tax_app_id = tax_app_id
    channel.tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    channel.tax_configuration.save()

    tax_data = TaxData(
        shipping_price_net_amount=Decimal("1"),
        shipping_price_gross_amount=Decimal("1.5"),
        shipping_tax_rate=Decimal("50"),
        lines=[
            TaxLineData(
                total_net_amount=Decimal("99999999999"),
                total_gross_amount=Decimal("3"),
                tax_rate=Decimal("50"),
            ),
            TaxLineData(
                total_net_amount=Decimal("4"),
                total_gross_amount=Decimal("6"),
                tax_rate=Decimal("50"),
            ),
        ],
    )

    zero_money = zero_taxed_money(order.currency)
    zero_prices = OrderTaxedPricesData(
        undiscounted_price=zero_money,
        price_with_discounts=zero_money,
    )
    manager_methods = {
        "calculate_order_line_unit": Mock(return_value=zero_prices),
        "calculate_order_line_total": Mock(return_value=zero_prices),
        "calculate_order_total": Mock(return_value=zero_money),
        "calculate_order_shipping": Mock(return_value=zero_money),
        "get_order_shipping_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_order_line_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_taxes_for_order": Mock(return_value=tax_data),
    }
    manager = Mock(**manager_methods)

    # when
    calculations.fetch_order_prices_if_expired(order, manager, None, True)

    # then
    assert order.tax_error == TaxDataErrorMessage.OVERFLOW
    assert TaxDataErrorMessage.OVERFLOW in caplog.text
    assert caplog.records[0].order_id == to_global_id_or_none(order)


@patch("saleor.plugins.avatax.plugin.get_order_tax_data")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_fetch_order_data_plugin_tax_data_with_negative_values(
    mock_get_tax_data,
    order_with_lines,
    caplog,
    plugin_configuration,  # noqa: F811
):
    # given
    order = order_with_lines

    channel = order.channel
    channel.tax_configuration.tax_app_id = AvataxPlugin.PLUGIN_IDENTIFIER
    channel.tax_configuration.save(update_fields=["tax_app_id"])

    tax_data = {
        "lines": [
            {
                "lineAmount": -30.0000,
                "quantity": 3.0,
                "itemCode": "SKU_A",
            },
            {
                "lineAmount": 40.0000,
                "quantity": 2.0,
                "itemCode": "SKU_B",
            },
            {
                "lineAmount": 8.1300,
                "quantity": 1.0,
                "itemCode": "Shipping",
            },
        ]
    }
    mock_get_tax_data.return_value = tax_data

    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    # when
    calculations.fetch_order_prices_if_expired(order, manager, None, True)

    # then
    assert order.tax_error == TaxDataErrorMessage.NEGATIVE_VALUE
    assert TaxDataErrorMessage.NEGATIVE_VALUE in caplog.text
    assert caplog.records[0].order_id == to_global_id_or_none(order)


@patch("saleor.plugins.avatax.plugin.get_order_tax_data")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_fetch_order_data_plugin_tax_data_price_overflow(
    mock_get_tax_data,
    order_with_lines,
    caplog,
    plugin_configuration,  # noqa: F811
):
    # given
    order = order_with_lines

    channel = order.channel
    channel.tax_configuration.tax_app_id = AvataxPlugin.PLUGIN_IDENTIFIER
    channel.tax_configuration.save(update_fields=["tax_app_id"])

    tax_data = {
        "lines": [
            {
                "lineAmount": 30.0000,
                "quantity": 3.0,
                "itemCode": "SKU_A",
            },
            {
                "lineAmount": 40.0000,
                "quantity": 2.0,
                "itemCode": "SKU_B",
            },
            {
                "lineAmount": 8368725697628976.1300,
                "quantity": 1.0,
                "itemCode": "Shipping",
            },
        ]
    }
    mock_get_tax_data.return_value = tax_data

    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    # when
    calculations.fetch_order_prices_if_expired(order, manager, None, True)

    # then
    assert order.tax_error == TaxDataErrorMessage.OVERFLOW
    assert TaxDataErrorMessage.OVERFLOW in caplog.text
    assert caplog.records[0].order_id == to_global_id_or_none(order)

from decimal import Decimal
from typing import Literal, Union
from unittest.mock import Mock, patch, sentinel

import pytest
from freezegun import freeze_time
from prices import Money, TaxedMoney

from ...core.prices import quantize_price
from ...core.taxes import TaxData, TaxError, TaxLineData, zero_taxed_money
from ...plugins.manager import get_plugins_manager
from .. import OrderStatus
from ..calculations import (
    _apply_tax_data,
    _combine_prices_from_manager_into_tax_data,
    fetch_order_prices_if_expired,
    order_line_tax_rate,
    order_line_total,
    order_line_unit,
    order_shipping,
    order_shipping_tax_rate,
)


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
    tax_rate = Decimal("1.23")
    net = Decimal("10.000")
    gross = Decimal("12.300")
    lines = [
        TaxLineData(
            id=line.id,
            currency=order.currency,
            unit_net_amount=line.unit_price.net.amount + net,
            unit_gross_amount=line.unit_price.gross.amount + gross,
            total_net_amount=line.total_price.net.amount + net,
            total_gross_amount=line.total_price.gross.amount + gross,
            tax_rate=tax_rate,
        )
        for line in order_lines
    ]
    total_net = sum(line.total_net_amount for line in lines)
    total_gross = sum(line.total_gross_amount for line in lines)
    return TaxData(
        currency=order.currency,
        shipping_price_net_amount=order.shipping_price.net.amount + net,
        shipping_price_gross_amount=order.shipping_price.gross.amount + gross,
        shipping_tax_rate=tax_rate,
        subtotal_net_amount=Mock(),
        subtotal_gross_amount=Mock(),
        total_net_amount=total_net,
        total_gross_amount=total_gross,
        lines=lines,
    )


def create_taxed_money(net: Decimal, gross: Decimal, currency: str) -> TaxedMoney:
    return TaxedMoney(net=Money(net, currency), gross=Money(gross, currency))


@patch("saleor.order.calculations.prefetch_related_objects")
def test_combine_prices_from_manager_into_tax_data(order_with_lines, order_lines):
    # given
    line_without_variant = Mock(variant=None)
    order = order_with_lines
    lines = list(order_lines)
    lines.insert(0, line_without_variant)
    lines.insert(2, line_without_variant)

    currency = order.currency

    line_tax_rates = [
        Decimal("0.23") + Decimal(i / 100) for i, _ in enumerate(order_lines)
    ]

    line_unit_prices = []
    for i, tax_rate in enumerate(line_tax_rates):
        net = Decimal("5.00") + i
        gross = net * (tax_rate + 1)
        line_unit_prices.append(create_taxed_money(net, gross, currency))

    line_total_prices = [
        unit_price * line.quantity
        for unit_price, line in zip(line_unit_prices, order_lines)
    ]

    shipping_tax_rate = Decimal("0.17")
    shipping_price = create_taxed_money(Decimal("10.00"), Decimal("11.70"), currency)

    manager = Mock(
        calculate_order_line_unit=Mock(side_effect=line_unit_prices),
        calculate_order_line_total=Mock(side_effect=line_total_prices),
        get_order_line_tax_rate=Mock(side_effect=line_tax_rates),
        calculate_order_shipping=Mock(return_value=shipping_price),
        get_order_shipping_tax_rate=Mock(return_value=shipping_tax_rate),
    )

    # when
    tax_data = _combine_prices_from_manager_into_tax_data(manager, order, lines)

    # then
    for line, unit_price, total_price, tax_rate in zip(
        tax_data.lines, line_unit_prices, line_total_prices, line_tax_rates
    ):
        assert get_taxed_money(line, "unit") == unit_price
        assert get_taxed_money(line, "total") == total_price
        assert line.tax_rate == tax_rate

    assert get_taxed_money(tax_data, "shipping_price") == shipping_price
    assert tax_data.shipping_tax_rate == shipping_tax_rate
    assert (
        get_taxed_money(tax_data, "total")
        == sum(
            [
                create_taxed_money(
                    line.total_net_amount, line.total_gross_amount, currency
                )
                for line in tax_data.lines
            ],
            zero_taxed_money(order.currency),
        )
        + shipping_price
    )


MANAGER_ORDER_METHODS = (
    "calculate_order_line_unit",
    "calculate_order_line_total",
    "get_order_line_tax_rate",
    "calculate_order_shipping",
    "get_order_shipping_tax_rate",
)


@pytest.mark.parametrize("mocked_method_name", MANAGER_ORDER_METHODS)
@patch("saleor.order.calculations.prefetch_related_objects")
def test_combine_prices_from_manager_to_tax_data(
    order_with_lines, order_lines, mocked_method_name
):
    # given
    order = order_with_lines
    lines = list(order_lines)
    manager_methods = {
        method_name: Mock(return_value=zero_taxed_money(order.currency))
        for method_name in MANAGER_ORDER_METHODS
    }
    manager_methods[mocked_method_name] = Mock(side_effect=TaxError())
    manager = Mock(**manager_methods)

    # when
    tax_data = _combine_prices_from_manager_into_tax_data(manager, order, lines)

    # then
    assert not tax_data


def test_apply_tax_data(order_with_lines, order_lines, tax_data):
    # given
    order = order_with_lines
    lines = order_lines

    def qp(amount):
        return quantize_price(amount, order.currency)

    # when
    _apply_tax_data(order, [line for line in lines], tax_data)

    # then
    assert str(order.total.net.amount) == str(qp(tax_data.total_net_amount))
    assert str(order.total.gross.amount) == str(qp(tax_data.total_gross_amount))

    assert str(order.shipping_price.net.amount) == str(
        qp(tax_data.shipping_price_net_amount)
    )
    assert str(order.shipping_price.gross.amount) == str(
        qp(tax_data.shipping_price_gross_amount)
    )

    for line, tax_line in zip(lines, tax_data.lines):
        assert str(line.unit_price.net.amount) == str(qp(tax_line.unit_net_amount))
        assert str(line.unit_price.gross.amount) == str(qp(tax_line.unit_gross_amount))

        assert str(line.total_price.net.amount) == str(qp(tax_line.total_net_amount))
        assert str(line.total_price.gross.amount) == str(
            qp(tax_line.total_gross_amount)
        )


@pytest.fixture
def manager():
    return get_plugins_manager()


@pytest.fixture
def fetch_kwargs(order_with_lines, manager):
    return {
        "order": order_with_lines,
        "manager": manager,
    }


def get_taxed_money(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["unit", "total", "subtotal", "shipping_price"],
) -> TaxedMoney:
    return TaxedMoney(
        Money(getattr(obj, f"{attr}_net_amount"), obj.currency),
        Money(getattr(obj, f"{attr}_gross_amount"), obj.currency),
    )


@freeze_time("2020-12-12 12:00:00")
@patch("saleor.order.calculations._combine_prices_from_manager_into_tax_data")
def test_fetch_order_prices_if_expired_plugins(
    mocked_combine_prices_from_manager_into_tax_data,
    manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
):
    # given
    manager.get_taxes_for_order = Mock(return_value=None)
    mocked_combine_prices_from_manager_into_tax_data.return_value = tax_data

    # when
    fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.shipping_price == get_taxed_money(
        tax_data, "shipping_price"
    )
    assert order_with_lines.shipping_tax_rate == tax_data.shipping_tax_rate
    assert order_with_lines.total == get_taxed_money(tax_data, "total")
    for order_line, tax_line in zip(order_with_lines.lines.all(), tax_data.lines):
        assert order_line.unit_price == get_taxed_money(tax_line, "unit")
        assert order_line.total_price == get_taxed_money(tax_line, "total")
        assert order_line.tax_rate == tax_line.tax_rate


@freeze_time("2020-12-12 12:00:00")
@patch("saleor.order.calculations._combine_prices_from_manager_into_tax_data")
def test_fetch_order_prices_if_expired_plugins_tax_error(
    mocked_combine_prices_from_manager_into_tax_data,
    order_with_lines,
    order_lines,
):
    # given
    manager = Mock(get_taxes_for_order=Mock(return_value=None))
    mocked_combine_prices_from_manager_into_tax_data.return_value = None
    order = order_with_lines
    unchanged = create_taxed_money(Decimal(-1), Decimal(-1), order.currency)

    order.shipping_price = unchanged
    order.shipping_tax_rate = unchanged
    order.total = unchanged
    for line in order_lines:
        line.unit_price = unchanged
        line.total_price = unchanged
        line.tax_rate = unchanged

    # when
    fetch_order_prices_if_expired(order, manager)

    # then
    assert order.shipping_price == unchanged
    assert order.shipping_tax_rate == unchanged
    assert order.total == unchanged
    for line in order_lines:
        assert line.unit_price == unchanged
        assert line.total_price == unchanged
        assert line.tax_rate == unchanged


@freeze_time("2020-12-12 12:00:00")
def test_fetch_order_prices_if_expired_webhooks_success(
    manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
):
    # given
    manager.get_taxes_for_order = Mock(return_value=tax_data)

    # when
    fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.shipping_price == get_taxed_money(
        tax_data, "shipping_price"
    )
    assert order_with_lines.shipping_tax_rate == tax_data.shipping_tax_rate
    assert order_with_lines.total == get_taxed_money(tax_data, "total")
    for order_line, tax_line in zip(order_with_lines.lines.all(), tax_data.lines):
        assert order_line.unit_price == get_taxed_money(tax_line, "unit")
        assert order_line.total_price == get_taxed_money(tax_line, "total")
        assert order_line.tax_rate == tax_line.tax_rate


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_unit(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_unit_price = sentinel.UNIT_PRICE

    order = Mock()
    order_line = Mock(pk=1, unit_price=expected_line_unit_price)
    manager = Mock()
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_unit_price = order_line_unit(order, order_line, manager)

    # then
    assert line_unit_price == expected_line_unit_price


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_total(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_total_price = sentinel.UNIT_PRICE

    order_line = Mock(pk=1, total_price=expected_line_total_price)
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_total_price = order_line_total(Mock(), order_line, Mock())

    # then
    assert line_total_price == expected_line_total_price


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_tax_rate(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_tax_rate = sentinel.UNIT_PRICE

    order_line = Mock(pk=1, tax_rate=expected_line_tax_rate)
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_tax_rate = order_line_tax_rate(Mock(), order_line, Mock())

    # then
    assert line_tax_rate == expected_line_tax_rate


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_shipping(mocked_fetch_order_prices_if_expired):
    # given
    expected_shipping_price = sentinel.UNIT_PRICE

    order = Mock(shipping_price=expected_shipping_price)
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    shipping_price = order_shipping(order, Mock())

    # then
    assert shipping_price == expected_shipping_price


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_shipping_tax_rate(mocked_fetch_order_prices_if_expired):
    # given
    expected_shipping_tax_rate = sentinel.UNIT_PRICE

    order = Mock(shipping_tax_rate=expected_shipping_tax_rate)
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    shipping_tax_rate = order_shipping_tax_rate(order, Mock())

    # then
    assert shipping_tax_rate == expected_shipping_tax_rate

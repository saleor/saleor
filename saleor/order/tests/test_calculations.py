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
    _apply_tax_data_from_manager,
    fetch_order_prices_if_expired,
    order_line_tax_rate,
    order_line_total,
    order_line_unit,
    order_shipping,
    order_shipping_tax_rate,
)
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


def create_order_taxed_prices_data(
    net: Decimal, gross: Decimal, currency: str
) -> OrderTaxedPricesData:
    return OrderTaxedPricesData(
        undiscounted_price=create_taxed_money(net, gross, currency),
        price_with_discounts=create_taxed_money(net, gross, currency),
    )


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
@patch("saleor.order.calculations.prefetch_related_objects", new=Mock())
def test_apply_tax_data_from_manager_tax_error(
    order_with_lines, order_lines, mocked_method_name
):
    # given
    order = order_with_lines
    price = create_taxed_money(Decimal("-100"), Decimal("-100"), "USD")
    tax_rate = Decimal("-100")

    order.total = price
    order.shipping_price = price
    order.shipping_tax_rate = tax_rate

    lines = list(order_lines)
    for line in lines:
        line.unit_price = price
        line.undiscounted_unit_price = price
        line.total_price = price
        line.undiscounted_total_price = price
        line.tax_rate = tax_rate

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
    tax_error = _apply_tax_data_from_manager(manager, order, lines)

    # then
    assert tax_error
    assert order.total == price
    assert order.shipping_price == price
    assert order.shipping_tax_rate == tax_rate

    for line in lines:
        assert line.unit_price == price
        assert line.undiscounted_unit_price == price
        assert line.total_price == price
        assert line.undiscounted_total_price == price
        assert line.tax_rate == tax_rate


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
def manager(tax_data, order_with_lines):
    manager = get_plugins_manager()
    manager.get_order_shipping_tax_rate = Mock(return_value=tax_data.shipping_tax_rate)
    manager.calculate_order_shipping = Mock(
        return_value=get_taxed_money(tax_data, "shipping_price")
    )
    manager.calculate_order_line_total = Mock(
        side_effect=[
            get_order_priced_taxes_data(line, "total") for line in tax_data.lines
        ]
    )
    manager.calculate_order_line_unit = Mock(
        side_effect=[
            get_order_priced_taxes_data(line, "unit") for line in tax_data.lines
        ]
    )
    manager.get_order_line_tax_rate = Mock(
        side_effect=[line.tax_rate for line in tax_data.lines]
    )
    return manager


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


def get_order_priced_taxes_data(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["unit", "total", "subtotal", "shipping_price"],
) -> OrderTaxedPricesData:
    return OrderTaxedPricesData(
        undiscounted_price=get_taxed_money(obj, attr),
        price_with_discounts=get_taxed_money(obj, attr),
    )


@freeze_time("2020-12-12 12:00:00")
def test_fetch_order_prices_if_expired_plugins(
    manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
):
    # given
    manager.get_taxes_for_order = Mock(return_value=None)

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
@patch("saleor.order.calculations._apply_tax_data_from_manager")
def test_fetch_order_prices_if_expired_plugins_tax_error(
    mocked_apply_tax_data_from_manager,
    order_with_lines,
    order_lines,
):
    # given
    manager = Mock(get_taxes_for_order=Mock(return_value=None))
    mocked_apply_tax_data_from_manager.return_value = None
    order = order_with_lines
    unchanged_money = create_taxed_money(Decimal(-1), Decimal(-1), order.currency)
    unchanged_tax_rate = Decimal(-1)

    order.shipping_price = unchanged_money
    order.shipping_tax_rate = unchanged_tax_rate
    order.total = unchanged_money
    for line in order_lines:
        line.unit_price = unchanged_money
        line.total_price = unchanged_money
        line.tax_rate = unchanged_tax_rate

    # when
    fetch_order_prices_if_expired(order, manager)

    # then
    assert order.shipping_price == unchanged_money
    assert order.shipping_tax_rate == unchanged_tax_rate
    assert order.total == unchanged_money
    for line in order_lines:
        assert line.unit_price == unchanged_money
        assert line.total_price == unchanged_money
        assert line.tax_rate == unchanged_tax_rate


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
    expected_line_undiscounted_unit_price = sentinel.UNDISCOUNTED_UNIT_PRICE

    order_line = Mock(
        pk=1,
        unit_price=expected_line_unit_price,
        undiscounted_unit_price=expected_line_undiscounted_unit_price,
    )
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_unit_price = order_line_unit(Mock(), order_line, Mock())

    # then
    assert line_unit_price == OrderTaxedPricesData(
        undiscounted_price=expected_line_undiscounted_unit_price,
        price_with_discounts=expected_line_unit_price,
    )


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_total(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_total_price = sentinel.TOTAL_PRICE
    expected_line_undiscounted_total_price = sentinel.UNDISCOUNTED_TOTAL_PRICE

    order_line = Mock(
        pk=1,
        total_price=expected_line_total_price,
        undiscounted_total_price=expected_line_undiscounted_total_price,
    )
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_total_price = order_line_total(Mock(), order_line, Mock())

    # then
    assert line_total_price == OrderTaxedPricesData(
        undiscounted_price=expected_line_undiscounted_total_price,
        price_with_discounts=expected_line_total_price,
    )


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

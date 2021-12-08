from decimal import Decimal
from typing import Literal, Union
from unittest.mock import Mock, patch

import pytest
from freezegun import freeze_time
from prices import Money, TaxedMoney

from saleor.core.prices import quantize_price
from saleor.core.taxes import TaxData, TaxLineData
from saleor.order.calculations import _apply_tax_data, fetch_order_prices_if_expired
from saleor.plugins.manager import get_plugins_manager


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
@patch("saleor.order.calculations._apply_tax_data")
def test_fetch_order_prices_if_expired_plugins(
    _mocked_apply_tax_data,
    manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
):
    # given
    manager.get_taxes_for_order = Mock(return_value=None)

    unit_prices, totals, tax_rates = zip(
        *[
            (
                get_taxed_money(line, "unit"),
                get_taxed_money(line, "total"),
                line.tax_rate,
            )
            for line in tax_data.lines
        ]
    )
    manager.calculate_order_line_unit = Mock(side_effect=unit_prices)
    manager.calculate_order_line_total = Mock(side_effect=totals)
    manager.get_order_line_tax_rate = Mock(side_effect=tax_rates)

    shipping_price = get_taxed_money(tax_data, "shipping_price")
    manager.calculate_order_shipping = Mock(return_value=shipping_price)

    shipping_tax_rate = tax_data.shipping_tax_rate
    manager.get_order_shipping_tax_rate = Mock(return_value=shipping_tax_rate)

    total = get_taxed_money(tax_data, "total")
    manager.calculate_order_total = Mock(return_value=total)

    # when
    fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.shipping_price == shipping_price
    assert order_with_lines.shipping_tax_rate == shipping_tax_rate
    assert order_with_lines.total == total
    for order_line, tax_line in zip(order_with_lines.lines.all(), tax_data.lines):
        assert order_line.unit_price == get_taxed_money(tax_line, "unit")
        assert order_line.total_price == get_taxed_money(tax_line, "total")
        assert order_line.tax_rate == tax_line.tax_rate


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

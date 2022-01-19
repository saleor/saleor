from decimal import Decimal
from typing import Literal, Union
from unittest.mock import Mock, patch

import pytest
from freezegun import freeze_time
from prices import Money, TaxedMoney

from ...core.prices import quantize_price
from ...core.taxes import TaxData, TaxLineData
from ...plugins.manager import get_plugins_manager
from ..calculations import _apply_tax_data, fetch_checkout_prices_if_expired
from ..fetch import CheckoutLineInfo, fetch_checkout_info, fetch_checkout_lines
from ..interface import CheckoutTaxedPricesData


@pytest.fixture
def checkout_lines(checkout_with_items):
    return checkout_with_items.lines.all()


@pytest.fixture
def tax_data(checkout_with_items, checkout_lines):
    checkout = checkout_with_items
    tax_rate = Decimal("1.23")
    net = Decimal("10.000")
    gross = Decimal("12.300")
    lines = checkout_lines
    return TaxData(
        currency=checkout.currency,
        shipping_price_net_amount=checkout.shipping_price.net.amount + net,
        shipping_price_gross_amount=checkout.shipping_price.gross.amount + gross,
        shipping_tax_rate=tax_rate,
        subtotal_net_amount=checkout.subtotal.net.amount + net,
        subtotal_gross_amount=checkout.subtotal.gross.amount + gross,
        total_net_amount=checkout.shipping_price.net.amount + net,
        total_gross_amount=checkout.shipping_price.gross.amount + gross,
        lines=[
            TaxLineData(
                id=line.id,
                currency=checkout.currency,
                unit_net_amount=line.unit_price.net.amount + net,
                unit_gross_amount=line.unit_price.gross.amount + gross,
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

    def qp(amount):
        return quantize_price(amount, checkout.currency)

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
    assert str(checkout.total.net.amount) == str(qp(tax_data.total_net_amount))
    assert str(checkout.total.gross.amount) == str(qp(tax_data.total_gross_amount))

    assert str(checkout.subtotal.net.amount) == str(qp(tax_data.subtotal_net_amount))
    assert str(checkout.subtotal.gross.amount) == str(
        qp(tax_data.subtotal_gross_amount)
    )

    assert str(checkout.shipping_price.net.amount) == str(
        qp(tax_data.shipping_price_net_amount)
    )
    assert str(checkout.shipping_price.gross.amount) == str(
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
def fetch_kwargs(checkout_with_items, manager):
    lines = fetch_checkout_lines(checkout_with_items)
    discounts = []
    return {
        "checkout_info": fetch_checkout_info(
            checkout_with_items, lines, discounts, manager
        ),
        "manager": manager,
        "lines": lines,
        "address": checkout_with_items.shipping_address
        or checkout_with_items.billing_address,
        "discounts": discounts,
    }


def get_checkout_taxed_prices_data(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["unit", "total", "subtotal", "shipping_price"],
) -> CheckoutTaxedPricesData:
    price = TaxedMoney(
        Money(getattr(obj, f"{attr}_net_amount"), obj.currency),
        Money(getattr(obj, f"{attr}_gross_amount"), obj.currency),
    )
    return CheckoutTaxedPricesData(
        undiscounted_price=price, price_with_sale=price, price_with_discounts=price
    )


def get_taxed_money(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["unit", "total", "subtotal", "shipping_price"],
) -> TaxedMoney:
    return TaxedMoney(
        Money(getattr(obj, f"{attr}_net_amount"), obj.currency),
        Money(getattr(obj, f"{attr}_gross_amount"), obj.currency),
    )


@freeze_time("2020-12-12 12:00:00")
@patch("saleor.checkout.calculations._apply_tax_data")
def test_fetch_checkout_prices_if_expired_plugins(
    _mocked_apply_tax_data,
    manager,
    fetch_kwargs,
    checkout_with_items,
    tax_data,
):
    # given
    manager.get_taxes_for_checkout = Mock(return_value=None)

    unit_prices, totals, tax_rates = zip(
        *[
            (
                get_checkout_taxed_prices_data(line, "unit"),
                get_checkout_taxed_prices_data(line, "total"),
                line.tax_rate,
            )
            for line in tax_data.lines
        ]
    )
    manager.calculate_checkout_line_unit_price = Mock(side_effect=unit_prices)
    manager.calculate_checkout_line_total = Mock(side_effect=totals)
    manager.get_checkout_line_tax_rate = Mock(side_effect=tax_rates)

    subtotal = get_taxed_money(tax_data, "subtotal")
    manager.calculate_checkout_subtotal = Mock(return_value=subtotal)

    shipping_price = get_taxed_money(tax_data, "shipping_price")
    manager.calculate_checkout_shipping = Mock(return_value=shipping_price)

    shipping_tax_rate = tax_data.shipping_tax_rate
    manager.get_checkout_shipping_tax_rate = Mock(return_value=shipping_tax_rate)

    total = get_taxed_money(tax_data, "total")
    manager.calculate_checkout_total = Mock(return_value=total)

    # when
    fetch_checkout_prices_if_expired(**fetch_kwargs)

    # then
    checkout_with_items.refresh_from_db()
    assert checkout_with_items.subtotal == subtotal
    assert checkout_with_items.shipping_price == shipping_price
    assert checkout_with_items.shipping_tax_rate == shipping_tax_rate
    assert checkout_with_items.total == total
    for checkout_line, tax_line in zip(checkout_with_items.lines.all(), tax_data.lines):
        assert checkout_line.unit_price == get_taxed_money(tax_line, "unit")
        assert checkout_line.total_price == get_taxed_money(tax_line, "total")
        assert checkout_line.tax_rate == tax_line.tax_rate


@freeze_time("2020-12-12 12:00:00")
def test_fetch_checkout_prices_if_expired_webhooks_success(
    manager,
    fetch_kwargs,
    checkout_with_items,
    tax_data,
):
    # given
    manager.get_taxes_for_checkout = Mock(return_value=tax_data)

    # when
    fetch_checkout_prices_if_expired(**fetch_kwargs)

    # then
    checkout_with_items.refresh_from_db()
    assert checkout_with_items.subtotal == get_taxed_money(tax_data, "subtotal")
    assert checkout_with_items.shipping_price == get_taxed_money(
        tax_data, "shipping_price"
    )
    assert checkout_with_items.shipping_tax_rate == tax_data.shipping_tax_rate
    assert checkout_with_items.total == get_taxed_money(tax_data, "total")
    for checkout_line, tax_line in zip(checkout_with_items.lines.all(), tax_data.lines):
        assert checkout_line.unit_price == get_taxed_money(tax_line, "unit")
        assert checkout_line.total_price == get_taxed_money(tax_line, "total")
        assert checkout_line.tax_rate == tax_line.tax_rate

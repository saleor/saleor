from decimal import Decimal
from typing import Literal, Union
from unittest.mock import Mock, patch

import pytest
from django.utils import timezone
from freezegun import freeze_time
from prices import Money, TaxedMoney

from ...core.prices import quantize_price
from ...core.taxes import TaxData, TaxLineData, zero_taxed_money
from ..calculations import _apply_tax_data_from_app, fetch_checkout_prices_if_expired
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
    _apply_tax_data_from_app(
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
    discounts = []
    return {
        "checkout_info": fetch_checkout_info(
            checkout_with_items, lines, discounts, plugins_manager
        ),
        "manager": plugins_manager,
        "lines": lines,
        "address": checkout_with_items.shipping_address
        or checkout_with_items.billing_address,
        "discounts": discounts,
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
@patch("saleor.checkout.calculations._apply_tax_data_from_app")
def test_fetch_checkout_prices_if_expired_plugins(
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
    plugins_manager.calculate_checkout_total = Mock(
        return_value=shipping_price + subtotal
    )

    # when
    fetch_checkout_prices_if_expired(**fetch_kwargs)

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


@freeze_time("2020-12-12 12:00:00")
def test_fetch_checkout_prices_if_expired_webhooks_success(
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
    fetch_checkout_prices_if_expired(**fetch_kwargs)

    # then
    checkout_with_items.refresh_from_db()
    assert checkout_with_items.shipping_price == get_taxed_money(
        tax_data, "shipping_price", currency
    )
    assert checkout_with_items.shipping_tax_rate == tax_data.shipping_tax_rate / 100
    for checkout_line, tax_line in zip(checkout_with_items.lines.all(), tax_data.lines):
        assert checkout_line.total_price == get_taxed_money(tax_line, "total", currency)
        assert checkout_line.tax_rate == tax_line.tax_rate / 100

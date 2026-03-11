"""Verify that Saleor's tax calculations produce identical results to Xero's.

Xero receives 2dp unit prices, applies tax per line with banker's rounding
(ROUND_HALF_EVEN), and sums line totals. These tests run the real Saleor tax
calculation pipeline and compare against a Xero simulation.

If these tests break, Saleor and Xero will compute different totals for the
same order — causing reconciliation failures between proforma invoices and
Xero quotes.

See: https://developer.xero.com/documentation/guides/how-to-guides/rounding-in-xero/
"""

from decimal import ROUND_HALF_EVEN, Decimal

import pytest
from prices import Money

from ...core.prices import quantize_price
from ...order.base_calculations import calculate_prices
from ..calculations.order import update_order_prices_with_flat_rates
from ..models import TaxClassCountryRate


def _enable_flat_rates(order, prices_entered_with_tax):
    from ..utils import TaxCalculationStrategy

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()


def _xero_line_tax(unit_price_2dp, quantity, tax_rate_pct):
    """Simulate Xero: tax = round(unit_price * qty * rate / 100, 2dp, banker's)."""
    line_amount = unit_price_2dp * quantity
    return (line_amount * tax_rate_pct / 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_EVEN
    )


def _assert_line_matches_xero(line, currency):
    unit_net = quantize_price(
        Money(line.unit_price_net_amount, currency), currency
    ).amount
    tax_rate_pct = line.tax_rate * 100

    xero_line_net = unit_net * line.quantity
    xero_line_tax = _xero_line_tax(unit_net, line.quantity, tax_rate_pct)
    xero_line_gross = xero_line_net + xero_line_tax

    assert line.total_price_net_amount == xero_line_net, (
        f"Net mismatch: saleor={line.total_price_net_amount}, xero={xero_line_net}"
    )
    assert line.total_price_gross_amount == xero_line_gross, (
        f"Gross mismatch: saleor={line.total_price_gross_amount}, xero={xero_line_gross}"
    )


@pytest.mark.django_db
def test_no_discount_lines_match_xero(order_with_lines_untaxed):
    # given
    order = order_with_lines_untaxed
    _enable_flat_rates(order, prices_entered_with_tax=False)
    lines = list(order.lines.all())
    calculate_prices(order, lines)

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax=False)

    # then
    for line in lines:
        _assert_line_matches_xero(line, order.currency)


@pytest.mark.django_db
def test_per_unit_rounding_boundary_matches_xero(order_with_lines_untaxed):
    """unit_net=10.05, qty=3, rate=10% triggers per-unit vs per-line rounding diff.

    Saleor (per-unit):  unit_gross = round(10.05*1.10) = round(11.055) = 11.06
                        line_gross = 11.06 * 3 = 33.18
    Xero   (per-line):  line_tax   = round(10.05*3*0.10) = round(3.015) = 3.02
                        line_gross = 30.15 + 3.02 = 33.17
    """
    from ...order.utils import get_order_country

    # given
    order = order_with_lines_untaxed
    _enable_flat_rates(order, prices_entered_with_tax=False)
    country = get_order_country(order)

    lines = list(order.lines.all())
    line = lines[0]
    line.quantity = 3
    line.base_unit_price_amount = Decimal("10.05")
    line.undiscounted_base_unit_price_amount = Decimal("10.05")

    TaxClassCountryRate.objects.update_or_create(
        tax_class=line.tax_class, country=country, defaults={"rate": Decimal(10)}
    )

    calculate_prices(order, [line])

    # when
    update_order_prices_with_flat_rates(order, [line], prices_entered_with_tax=False)

    # then
    _assert_line_matches_xero(line, order.currency)


@pytest.mark.django_db
def test_no_discount_order_total_matches_xero(order_with_lines_untaxed):
    # given
    order = order_with_lines_untaxed
    _enable_flat_rates(order, prices_entered_with_tax=False)
    lines = list(order.lines.all())
    calculate_prices(order, lines)

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax=False)

    # then — sum line totals the way Xero does (per-line tax, then sum)
    xero_net = Decimal(0)
    xero_gross = Decimal(0)
    for line in lines:
        unit_net = quantize_price(
            Money(line.unit_price_net_amount, order.currency), order.currency
        ).amount
        tax_rate_pct = line.tax_rate * 100
        line_net = unit_net * line.quantity
        line_tax = _xero_line_tax(unit_net, line.quantity, tax_rate_pct)
        xero_net += line_net
        xero_gross += line_net + line_tax

    shipping_net = order.shipping_price_net_amount
    shipping_tax_rate_pct = (order.shipping_tax_rate or Decimal(0)) * 100
    shipping_tax = _xero_line_tax(shipping_net, 1, shipping_tax_rate_pct)

    assert order.subtotal_net_amount == xero_net
    assert order.subtotal_gross_amount == xero_gross
    assert order.total_net_amount == xero_net + shipping_net
    assert order.total_gross_amount == xero_gross + shipping_net + shipping_tax


@pytest.mark.django_db
def test_no_discount_different_tax_rates_match_xero(
    order_with_lines_untaxed, default_tax_class
):
    # given — second line gets a different tax rate
    order = order_with_lines_untaxed
    _enable_flat_rates(order, prices_entered_with_tax=False)

    from ...order.utils import get_order_country

    country = get_order_country(order)

    lines = list(order.lines.all())
    second_line = lines[1]
    TaxClassCountryRate.objects.update_or_create(
        tax_class=second_line.tax_class, country=country, defaults={"rate": Decimal(5)}
    )

    calculate_prices(order, lines)

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax=False)

    # then
    for line in lines:
        _assert_line_matches_xero(line, order.currency)

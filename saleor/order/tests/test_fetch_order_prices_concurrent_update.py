"""Regression tests for orders left with prices that carry no tax.

`fetch_order_prices_if_expired` writes the order prices twice:

1. `process_order_promotion` -> `handle_order_promotion` -> `_set_order_base_prices`
   saves the *pre-tax* `subtotal` and `total` straight to the database, before taxes
   are calculated at all. It touches neither `shipping_price` nor the lines.
2. `process_order_prices` -> `process_calculation_result` saves the taxed prices for
   the order and all of its lines.

The second write is skipped when the `updated_at` guard in `process_calculation_result`
decides the order was modified concurrently. The taxes calculated in that pass are
correct - they are dropped only to avoid overwriting the concurrent change - so the
order is left with the untaxed values from the first write, next to a `shipping_price`
and lines that keep the taxed values from an earlier, successful recalculation.

To keep such an order recoverable, `_set_order_base_prices` sets `should_refresh_prices`
in the very same write that stores the untaxed prices, and the guarded save clears the
flag only when it actually stores the taxed prices. A skipped
save - or a process that dies in between - therefore leaves the order flagged, so the
prices are recalculated on the next read and `draftOrderComplete` refuses to finalize an
order whose stored prices may carry no tax. A completed order is no longer recalculated,
so the mistake could not be corrected afterwards.

This happens the same way for flat rates and for a tax app - it does not depend on how
the taxes are calculated.
"""

import dataclasses
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from django.utils import timezone
from prices import Money, TaxedMoney
from promise import Promise

from ...core.prices import quantize_price
from ...core.taxes import (
    TaxData,
    TaxLineData,
    zero_taxed_money,
)
from ...plugins.manager import get_plugins_manager
from ...tests import race_condition
from .. import calculations
from ..models import Order

if TYPE_CHECKING:
    pass

PLUGIN_TAX_RATE = Decimal("0.13")

# Base (pre-tax) prices of the `draft_order` fixture.
SUBTOTAL_NET = Decimal("70.00")
SHIPPING_NET = Decimal("10.00")
TOTAL_NET = SUBTOTAL_NET + SHIPPING_NET


def _with_plugin_tax(net: Money) -> TaxedMoney:
    return TaxedMoney(
        net=net, gross=quantize_price(net * (1 + PLUGIN_TAX_RATE), net.currency)
    )


def _untaxed(amount: Decimal, currency: str) -> TaxedMoney:
    money = Money(amount, currency)
    return TaxedMoney(net=money, gross=money)


def _sum_line_totals(order: Order) -> TaxedMoney:
    return sum(
        (line.total_price for line in order.lines.all()),
        zero_taxed_money(order.currency),
    )


def _recalculate(order, manager=None):
    return calculations.fetch_order_prices_if_expired(
        order,
        manager or get_plugins_manager(allow_replica=False),
        None,
        force_update=True,
    ).get()


# --------------------------------------------------------------------------------
# The recalculated prices are dropped, the pre-tax ones stay.
# --------------------------------------------------------------------------------


@pytest.fixture
def order_with_taxed_prices(draft_order, plugins_manager, tax_configuration_flat_rates):
    """Draft order whose persisted prices are taxed and internally consistent."""
    _recalculate(draft_order, plugins_manager)
    draft_order.refresh_from_db()
    assert draft_order.total.tax.amount > Decimal(0)
    assert draft_order.total == draft_order.subtotal + draft_order.shipping_price
    return draft_order


def _recalculate_while_order_is_touched(order, manager):
    def touch_order_from_another_process(*args, **kwargs):
        Order.objects.filter(pk=order.pk).update(updated_at=timezone.now())

    # `_set_order_base_prices` has already written the pre-tax prices by the time
    # `calculate_taxes` runs, so this mimics another process touching the order
    # between the two writes.
    with race_condition.RunBefore(
        "saleor.order.calculations.calculate_taxes", touch_order_from_another_process
    ):
        return _recalculate(order, manager)


def test_concurrent_update_leaves_untaxed_subtotal_and_total_persisted(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    currency = order.currency
    order_in_request = Order.objects.get(pk=order.pk)

    # when
    _recalculate_while_order_is_touched(order_in_request, plugins_manager)

    # then
    # The taxed save was skipped, so the untaxed prices written by
    # `_set_order_base_prices` are what stayed in the database.
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.subtotal == _untaxed(SUBTOTAL_NET, currency)
    assert persisted.total == _untaxed(TOTAL_NET, currency)
    # They are marked as provisional, which is what keeps the order recoverable.
    assert persisted.should_refresh_prices is True


def test_concurrent_update_leaves_order_prices_inconsistent_with_lines(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    order_in_request = Order.objects.get(pk=order.pk)

    # when
    _recalculate_while_order_is_touched(order_in_request, plugins_manager)

    # then
    # The lines and the shipping price keep the taxes from the previous pass while the
    # order-level amounts lost them. This inconsistency is the reported bug and it is
    # not repaired here - it is only flagged, so the next read recalculates it away.
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.subtotal != _sum_line_totals(persisted)
    assert persisted.total != persisted.subtotal + persisted.shipping_price
    assert persisted.should_refresh_prices is True


def test_concurrent_update_returns_prices_that_were_not_persisted(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    order_in_request = Order.objects.get(pk=order.pk)

    # when
    returned_order, _ = _recalculate_while_order_is_touched(
        order_in_request, plugins_manager
    )

    # then
    # The caller still gets the correctly taxed prices that were never stored, and no
    # tax error - so the returned prices alone cannot tell `draftOrderComplete` that
    # anything went wrong. The flag is what it has to look at instead.
    assert returned_order.tax_error is None
    assert returned_order.total.tax.amount > Decimal(0)
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.total != returned_order.total
    assert returned_order.should_refresh_prices is True


def test_concurrent_update_prices_are_recalculated_on_the_next_pass(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    currency = order.currency
    _recalculate_while_order_is_touched(Order.objects.get(pk=order.pk), plugins_manager)

    # when
    # `draftOrderComplete` recalculates without forcing an update, so this is what it
    # does for an order whose previous recalculation was dropped.
    calculations.fetch_order_prices_if_expired(
        Order.objects.get(pk=order.pk), plugins_manager, None
    ).get()

    # then
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.total.tax.amount > Decimal(0)
    assert persisted.total != _untaxed(TOTAL_NET, currency)
    assert persisted.subtotal == _sum_line_totals(persisted)
    assert persisted.total == persisted.subtotal + persisted.shipping_price


def test_concurrent_update_leaves_the_order_flagged_for_recalculation(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    order_in_request = Order.objects.get(pk=order.pk)
    assert order_in_request.should_refresh_prices is False

    # when
    _recalculate_while_order_is_touched(order_in_request, plugins_manager)

    # then
    # The taxed save was skipped, so the flag set before the tax calculation is still
    # there - the prices are recalculated on the next read and `draftOrderComplete`
    # refuses to finalize the order in the meantime.
    assert Order.objects.get(pk=order.pk).should_refresh_prices is True
    # The instance the caller holds says the same, so the mutation can tell without
    # going back to the database.
    assert order_in_request.should_refresh_prices is True


def test_successful_recalculation_clears_the_flag(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    currency = order.currency
    order_in_request = Order.objects.get(pk=order.pk)

    # when
    calculations.fetch_order_prices_if_expired(
        order_in_request, plugins_manager, None, force_update=True
    ).get()

    # then
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.should_refresh_prices is False
    assert order_in_request.should_refresh_prices is False
    assert persisted.total.tax.amount > Decimal(0)
    assert persisted.total != _untaxed(TOTAL_NET, currency)
    assert persisted.subtotal == _sum_line_totals(persisted)
    assert persisted.total == persisted.subtotal + persisted.shipping_price


def test_flag_is_set_before_the_tax_calculation_can_crash(
    order_with_taxed_prices, plugins_manager
):
    """The flag must land before anything that can die between the two writes.

    `calculate_prices` and the tax strategy lookup run between the untaxed base prices
    being stored and the taxed prices being saved. A pod killed there would otherwise
    leave untaxed prices behind with nothing marking them.
    """
    # given
    order = order_with_taxed_prices
    order_in_request = Order.objects.get(pk=order.pk)

    def blow_up(*args, **kwargs):
        raise RuntimeError("pod killed mid-recalculation")

    # when
    with patch("saleor.order.calculations.calculate_prices", side_effect=blow_up):
        with pytest.raises(RuntimeError):
            calculations.fetch_order_prices_if_expired(
                order_in_request, plugins_manager, None, force_update=True
            ).get()

    # then
    # The order is flagged, so the next read recalculates it instead of trusting
    # whatever the interrupted pass left behind.
    assert Order.objects.get(pk=order.pk).should_refresh_prices is True


def test_flag_is_set_before_taxes_are_calculated(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    order_in_request = Order.objects.get(pk=order.pk)
    flag_during_tax_calculation = []

    def record_persisted_flag(*args, **kwargs):
        flag_during_tax_calculation.append(
            Order.objects.get(pk=order.pk).should_refresh_prices
        )

    # when
    with race_condition.RunBefore(
        "saleor.order.calculations.calculate_taxes", record_persisted_flag
    ):
        calculations.fetch_order_prices_if_expired(
            order_in_request, plugins_manager, None, force_update=True
        ).get()

    # then
    # The order is flagged for the whole duration of the tax calculation, so a crash or
    # a skipped save in between cannot leave untaxed prices behind unnoticed.
    assert flag_during_tax_calculation == [True]
    assert Order.objects.get(pk=order.pk).should_refresh_prices is False


# --------------------------------------------------------------------------------
# The same, with a tax app instead of a tax plugin.
#
# `_apply_tax_data` is all-or-nothing - it bails out on missing tax data and derives
# `subtotal`/`total` from the same payload it used for the lines - so the app path
# cannot produce a half-taxed order on its own. It is still left with the untaxed
# `subtotal`/`total` that `_set_order_base_prices` persisted whenever the taxed save
# is skipped, which is where the two paths behave the same.
# --------------------------------------------------------------------------------

APP_TAX_RATE = Decimal(10)


def _tax_data_for(order: Order) -> TaxData:
    currency = order.currency
    rate = Decimal(1) + APP_TAX_RATE / Decimal(100)
    shipping_net = order.base_shipping_price_amount
    return TaxData(
        shipping_price_net_amount=shipping_net,
        shipping_price_gross_amount=quantize_price(shipping_net * rate, currency),
        shipping_tax_rate=APP_TAX_RATE,
        lines=[
            TaxLineData(
                total_net_amount=line.base_unit_price_amount * line.quantity,
                total_gross_amount=quantize_price(
                    line.base_unit_price_amount * line.quantity * rate, currency
                ),
                tax_rate=APP_TAX_RATE,
            )
            for line in order.lines.all()
        ],
    )


@patch("saleor.tax.webhooks.shared.trigger_webhook_sync_promise")
def test_app_concurrent_update_leaves_untaxed_subtotal_and_total_persisted(
    mocked_trigger_webhook_sync_promise,
    draft_order,
    tax_configuration_tax_app,
    plugins_manager,
):
    # given
    order = draft_order
    currency = order.currency
    mocked_trigger_webhook_sync_promise.return_value = Promise.resolve(
        dataclasses.asdict(_tax_data_for(order))
    )
    _recalculate(order, plugins_manager)
    order.refresh_from_db()
    assert order.total.tax.amount > Decimal(0)

    # when
    _recalculate_while_order_is_touched(Order.objects.get(pk=order.pk), plugins_manager)

    # then
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.subtotal == _untaxed(SUBTOTAL_NET, currency)
    assert persisted.total == _untaxed(TOTAL_NET, currency)
    assert persisted.should_refresh_prices is True


@patch("saleor.tax.webhooks.shared.trigger_webhook_sync_promise")
def test_app_concurrent_update_leaves_order_prices_inconsistent_with_lines(
    mocked_trigger_webhook_sync_promise,
    draft_order,
    tax_configuration_tax_app,
    plugins_manager,
):
    # given
    order = draft_order
    mocked_trigger_webhook_sync_promise.return_value = Promise.resolve(
        dataclasses.asdict(_tax_data_for(order))
    )
    _recalculate(order, plugins_manager)

    # when
    _recalculate_while_order_is_touched(Order.objects.get(pk=order.pk), plugins_manager)

    # then
    # As on the plugin path, the inconsistency is flagged rather than repaired.
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.subtotal != _sum_line_totals(persisted)
    assert persisted.total != persisted.subtotal + persisted.shipping_price
    assert persisted.should_refresh_prices is True


def test_app_without_taxes_webhook_persists_consistent_untaxed_prices(
    draft_order, tax_app, tax_configuration_tax_app, plugins_manager
):
    # given
    order = draft_order
    currency = order.currency
    tax_app.webhooks.all().delete()

    # when
    _recalculate(order, plugins_manager)

    # then
    # `_apply_tax_data` is never reached, so the order and its lines keep the base
    # prices `calculate_prices` assigned - untaxed, but consistent with each other.
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.tax_error == (
        "Configured tax app's webhook for taxes calculation doesn't exists."
    )
    assert persisted.subtotal == _untaxed(SUBTOTAL_NET, currency)
    assert persisted.shipping_price == _untaxed(SHIPPING_NET, currency)
    assert persisted.total == _untaxed(TOTAL_NET, currency)
    assert persisted.subtotal == _sum_line_totals(persisted)


@patch("saleor.tax.webhooks.shared.trigger_webhook_sync_promise")
def test_app_returning_too_few_lines_persists_consistent_untaxed_prices(
    mocked_trigger_webhook_sync_promise,
    draft_order,
    tax_configuration_tax_app,
    plugins_manager,
):
    # given
    order = draft_order
    currency = order.currency
    assert order.lines.count() == 2
    tax_data = _tax_data_for(order)
    tax_data = dataclasses.replace(tax_data, lines=tax_data.lines[:1])
    mocked_trigger_webhook_sync_promise.return_value = Promise.resolve(
        dataclasses.asdict(tax_data)
    )

    # when
    _recalculate(order, plugins_manager)

    # then
    # The app response is line-count validated, so a short response is rejected whole
    # instead of taxing only the lines it covered. The plugin path has no equivalent.
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.subtotal == _untaxed(SUBTOTAL_NET, currency)
    assert persisted.shipping_price == _untaxed(SHIPPING_NET, currency)
    assert persisted.total == _untaxed(TOTAL_NET, currency)
    assert persisted.subtotal == _sum_line_totals(persisted)

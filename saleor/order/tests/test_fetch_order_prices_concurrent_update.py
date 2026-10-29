"""Regression tests for orders left with prices that carry no tax.

`fetch_order_prices_if_expired` used to write the order prices twice:

1. `process_order_promotion` -> `handle_order_promotion` -> `_set_order_base_prices`
   saved the *pre-tax* `subtotal` and `total` straight to the database, before taxes
   were calculated at all - order promotions are qualified by a predicate evaluated in
   SQL, so the pre-tax prices have to be persisted.
2. `process_order_prices` -> `process_calculation_result` saves the taxed prices for
   the order and all of its lines, unless its `updated_at` guard decides the order was
   modified concurrently, in which case the save is skipped.

A skipped second write left the order with the untaxed values from the first one, next
to a `shipping_price` and lines that kept the taxes from an earlier, successful pass.

The pre-tax prices now live in their own `base_subtotal`/`base_total` columns, the way
`Checkout` keeps them, so `subtotal`/`total` are written only by the taxed save. When
that save is skipped the order simply keeps the prices it had before, consistent with
its lines. The skip is mirrored into the `should_refresh_prices` flag of the instance
the caller holds, so `draftOrderComplete` refuses to finalize an order whose stored
prices are not the ones it just calculated.

This holds the same way for flat rates and for a tax app - it does not depend on how
the taxes are calculated.
"""

import dataclasses
from decimal import Decimal
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

# Base (pre-tax) prices of the `draft_order` fixture.
SUBTOTAL_NET = Decimal("70.00")
SHIPPING_NET = Decimal("10.00")
TOTAL_NET = SUBTOTAL_NET + SHIPPING_NET


def _sum_line_totals(order: Order) -> TaxedMoney:
    return sum(
        (line.total_price for line in order.lines.all()),
        zero_taxed_money(order.currency),
    )


def _line_totals(order: Order) -> dict:
    return {line.pk: line.total_price for line in order.lines.all()}


def _recalculate(order, manager=None):
    return calculations.fetch_order_prices_if_expired(
        order,
        manager or get_plugins_manager(allow_replica=False),
        None,
        force_update=True,
    ).get()


def _recalculate_while_order_is_touched(order, manager, force_update=True):
    def touch_order_from_another_process(*args, **kwargs):
        Order.objects.filter(pk=order.pk).update(updated_at=timezone.now())

    # The base prices have already been written by the time `calculate_taxes` runs,
    # so this mimics another process touching the order between that write and the
    # taxed save.
    with race_condition.RunBefore(
        "saleor.order.calculations.calculate_taxes", touch_order_from_another_process
    ):
        return calculations.fetch_order_prices_if_expired(
            order, manager, None, force_update=force_update
        ).get()


def _assert_prices_unchanged(persisted: Order, before: Order):
    assert persisted.subtotal == before.subtotal
    assert persisted.total == before.total
    assert persisted.shipping_price == before.shipping_price
    assert _line_totals(persisted) == _line_totals(before)
    assert persisted.subtotal == _sum_line_totals(persisted)
    assert persisted.total == persisted.subtotal + persisted.shipping_price


@pytest.fixture
def order_with_taxed_prices(draft_order, plugins_manager, tax_configuration_flat_rates):
    """Draft order whose persisted prices are taxed and internally consistent."""
    _recalculate(draft_order, plugins_manager)
    draft_order.refresh_from_db()
    assert draft_order.total.tax.amount > Decimal(0)
    assert draft_order.total == draft_order.subtotal + draft_order.shipping_price
    return draft_order


# --------------------------------------------------------------------------------
# The pre-tax prices never touch `subtotal`/`total`.
# --------------------------------------------------------------------------------


def test_base_prices_are_stored_apart_from_the_taxed_prices(
    draft_order, plugins_manager, tax_configuration_flat_rates
):
    # given
    order = draft_order
    currency = order.currency
    before = Order.objects.get(pk=order.pk)
    assert before.base_subtotal == Money(0, currency)
    assert before.base_total == Money(0, currency)
    persisted_during_tax_calculation = []

    def record_persisted_order(*args, **kwargs):
        persisted_during_tax_calculation.append(Order.objects.get(pk=order.pk))

    # when
    with race_condition.RunBefore(
        "saleor.order.calculations.calculate_taxes", record_persisted_order
    ):
        _recalculate(Order.objects.get(pk=order.pk), plugins_manager)

    # then
    # By the time the taxes are calculated the pre-tax prices are already stored, in
    # their own columns - `subtotal` and `total` are still what they were before.
    assert len(persisted_during_tax_calculation) == 1
    during = persisted_during_tax_calculation[0]
    assert during.base_subtotal == Money(SUBTOTAL_NET, currency)
    assert during.base_total == Money(TOTAL_NET, currency)
    assert during.subtotal == before.subtotal
    assert during.total == before.total


def test_crash_during_recalculation_leaves_the_stored_prices_untouched(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    before = Order.objects.get(pk=order.pk)

    def blow_up(*args, **kwargs):
        raise RuntimeError("pod killed mid-recalculation")

    # when
    with patch("saleor.order.calculations.calculate_prices", side_effect=blow_up):
        with pytest.raises(RuntimeError):
            _recalculate(Order.objects.get(pk=order.pk), plugins_manager)

    # then
    _assert_prices_unchanged(Order.objects.get(pk=order.pk), before)


# --------------------------------------------------------------------------------
# The recalculated prices are dropped, the previous ones stay.
# --------------------------------------------------------------------------------


def test_concurrent_update_keeps_the_previously_stored_prices(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    before = Order.objects.get(pk=order.pk)

    # when
    _recalculate_while_order_is_touched(Order.objects.get(pk=order.pk), plugins_manager)

    # then
    # The taxed save was skipped and nothing else wrote the prices, so the order keeps
    # the taxed, consistent prices it had.
    persisted = Order.objects.get(pk=order.pk)
    _assert_prices_unchanged(persisted, before)
    assert persisted.total.tax.amount > Decimal(0)


def test_concurrent_update_returns_prices_that_were_not_persisted(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    order_in_request = Order.objects.get(pk=order.pk)
    assert order_in_request.should_refresh_prices is False

    # when
    returned_order, _ = _recalculate_while_order_is_touched(
        order_in_request, plugins_manager
    )

    # then
    # The caller gets correctly taxed prices and no tax error, so the returned prices
    # alone cannot tell `draftOrderComplete` that they were never stored. The flag on
    # the instance is what it has to look at.
    assert returned_order.tax_error is None
    assert returned_order.total.tax.amount > Decimal(0)
    assert returned_order.should_refresh_prices is True
    # The caller did not flag the order before recalculating, so nothing in the
    # database says a recalculation was dropped - the instance is the only signal.
    assert Order.objects.get(pk=order.pk).should_refresh_prices is False


def test_concurrent_update_keeps_the_flag_the_caller_set(
    order_with_taxed_prices, plugins_manager
):
    # given
    # Mutations flag the order before recalculating, which is what makes it need a
    # recalculation in the first place.
    order = order_with_taxed_prices
    Order.objects.filter(pk=order.pk).update(should_refresh_prices=True)

    # when
    _recalculate_while_order_is_touched(
        Order.objects.get(pk=order.pk), plugins_manager, force_update=False
    )

    # then
    # Only the taxed save clears the flag, so a skipped save leaves it set and the
    # prices are recalculated on the next read.
    assert Order.objects.get(pk=order.pk).should_refresh_prices is True


def test_concurrent_update_prices_are_recalculated_on_the_next_pass(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    Order.objects.filter(pk=order.pk).update(should_refresh_prices=True)
    _recalculate_while_order_is_touched(
        Order.objects.get(pk=order.pk), plugins_manager, force_update=False
    )
    assert Order.objects.get(pk=order.pk).should_refresh_prices is True

    # when
    # `draftOrderComplete` recalculates without forcing an update, so this is what it
    # does for an order whose previous recalculation was dropped.
    calculations.fetch_order_prices_if_expired(
        Order.objects.get(pk=order.pk), plugins_manager, None
    ).get()

    # then
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.should_refresh_prices is False
    assert persisted.total.tax.amount > Decimal(0)
    assert persisted.subtotal == _sum_line_totals(persisted)
    assert persisted.total == persisted.subtotal + persisted.shipping_price


def test_successful_recalculation_clears_the_flag(
    order_with_taxed_prices, plugins_manager
):
    # given
    order = order_with_taxed_prices
    Order.objects.filter(pk=order.pk).update(should_refresh_prices=True)
    order_in_request = Order.objects.get(pk=order.pk)

    # when
    calculations.fetch_order_prices_if_expired(
        order_in_request, plugins_manager, None
    ).get()

    # then
    persisted = Order.objects.get(pk=order.pk)
    assert persisted.should_refresh_prices is False
    assert order_in_request.should_refresh_prices is False
    assert persisted.total.tax.amount > Decimal(0)
    assert persisted.subtotal == _sum_line_totals(persisted)
    assert persisted.total == persisted.subtotal + persisted.shipping_price


# --------------------------------------------------------------------------------
# The same, with a tax app instead of a tax plugin.
#
# `_apply_tax_data` is all-or-nothing - it bails out on missing tax data and derives
# `subtotal`/`total` from the same payload it used for the lines - so the app path
# cannot produce a half-taxed order on its own. Where the two paths behave the same is
# the skipped taxed save, so that is what is covered here.
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
def test_app_concurrent_update_keeps_the_previously_stored_prices(
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
    before = Order.objects.get(pk=order.pk)
    assert before.total.tax.amount > Decimal(0)

    # when
    _recalculate_while_order_is_touched(Order.objects.get(pk=order.pk), plugins_manager)

    # then
    _assert_prices_unchanged(Order.objects.get(pk=order.pk), before)

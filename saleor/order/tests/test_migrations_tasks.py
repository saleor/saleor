from decimal import Decimal

from django.db import transaction

from ...payment import TransactionEventType
from ...payment.transaction_item_calculations import recalculate_transaction_amounts
from .. import OrderChargeStatus, OrderRefundStatus
from ..migrations.tasks import saleor3_24
from ..migrations.tasks.saleor3_24 import (
    _get_locked_orders_batch,
    backfill_order_statuses,
)
from ..models import Order


def test_sets_the_statuses_of_a_refunded_order(
    order_with_lines,
    transaction_item_generator,
    transaction_events_generator,
):
    """The task sets the statuses of an order refunded before the field was added.

    The refund and the charge status are derived from the transaction amounts, so an
    order with nothing charged left is not reported as fully charged anymore.
    """
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    transaction = transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    transaction_events_generator(
        transaction=transaction,
        psp_references=["refund-1"],
        types=[TransactionEventType.REFUND_SUCCESS],
        amounts=[order_total],
    )
    recalculate_transaction_amounts(transaction)
    # the stale statuses an order refunded before the field was added has stored
    order.refund_status = OrderRefundStatus.NONE
    order.charge_status = OrderChargeStatus.FULL
    order.total_charged_amount = Decimal(0)
    order.save(update_fields=["refund_status", "charge_status", "total_charged_amount"])

    # when
    backfill_order_statuses(current_depth=0)

    # then
    order.refresh_from_db()
    assert order.refund_status == OrderRefundStatus.FULL
    assert order.charge_status == OrderChargeStatus.NONE


def test_corrects_the_statuses_of_a_charged_order(
    order_with_lines,
    transaction_item_generator,
):
    """An order without refunds is reported as charged and not refunded."""
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    # the stale statuses an order has before the backfill runs
    order.refund_status = OrderRefundStatus.FULL
    order.charge_status = OrderChargeStatus.NONE
    order.total_charged_amount = order_total
    order.save(update_fields=["refund_status", "charge_status", "total_charged_amount"])

    # when
    backfill_order_statuses(current_depth=0)

    # then
    order.refresh_from_db()
    assert order.refund_status == OrderRefundStatus.NONE
    assert order.charge_status == OrderChargeStatus.FULL


def test_locks_the_orders_before_writing(
    order_with_lines,
    transaction_item_generator,
    assert_locks_rows_before_write,
):
    """The task locks the batch it processes, so concurrent runs cannot deadlock."""
    # given
    transaction_item_generator(
        order_id=order_with_lines.pk,
        charged_value=order_with_lines.total_gross_amount,
    )

    # when/then
    with assert_locks_rows_before_write():
        backfill_order_statuses(current_depth=0)


def test_processes_the_orders_from_the_newest(
    orders,
    monkeypatch,
):
    """The task walks the orders from the newest to the oldest.

    The recently placed orders are corrected first, so they stop reporting the stale
    status before the task works its way through the older ones.
    """
    # given
    monkeypatch.setattr(saleor3_24, "BACKFILL_ORDER_STATUSES_BATCH_SIZE", 1)
    expected_pks = list(Order.objects.order_by("-pk").values_list("pk", flat=True))
    assert len(expected_pks) >= 2

    # when
    with transaction.atomic():
        first_batch = _get_locked_orders_batch(None)
    with transaction.atomic():
        second_batch = _get_locked_orders_batch(first_batch[-1].pk)

    # then
    assert [order.pk for order in first_batch] == expected_pks[:1]
    assert [order.pk for order in second_batch] == expected_pks[1:2]

from decimal import Decimal
from unittest.mock import ANY, patch

from ...payment import ChargeStatus
from ...plugins.manager import get_plugins_manager
from ...warehouse.models import Allocation
from .. import FulfillmentLineData, FulfillmentStatus, OrderLineData
from ..actions import create_refund_fulfillment
from ..models import FulfillmentLine


@patch("saleor.order.actions.gateway.refund")
def test_create_refund_fulfillment_only_order_lines(
    mocked_refund, order_with_lines, payment_dummy
):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    payment = order_with_lines.get_last_payment()

    order_lines_to_refund = order_with_lines.lines.all()
    original_quantity = {
        line.id: line.quantity_unfulfilled for line in order_with_lines.lines.all()
    }
    order_line_ids = order_lines_to_refund.values_list("id", flat=True)
    original_allocations = list(
        Allocation.objects.filter(order_line_id__in=order_line_ids)
    )
    lines_count = order_with_lines.lines.count()

    returned_fulfillemnt = create_refund_fulfillment(
        requester=None,
        order=order_with_lines,
        payment=payment,
        order_lines_to_refund=[
            OrderLineData(line=line, quantity=2) for line in order_lines_to_refund
        ],
        fulfillment_lines_to_refund=[],
        manager=get_plugins_manager(),
    )

    returned_fulfillment_lines = returned_fulfillemnt.lines.all()
    assert returned_fulfillemnt.status == FulfillmentStatus.REFUNDED
    assert len(returned_fulfillment_lines) == lines_count
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids
    for line in order_lines_to_refund:
        assert line.quantity_unfulfilled == original_quantity.get(line.pk) - 2

    current_allocations = Allocation.objects.in_bulk(
        [allocation.pk for allocation in original_allocations]
    )
    for original_allocation in original_allocations:
        current_allocation = current_allocations.get(original_allocation.pk)
        assert (
            original_allocation.quantity_allocated - 2
            == current_allocation.quantity_allocated
        )
    amount = sum([line.unit_price_gross_amount * 2 for line in order_lines_to_refund])
    mocked_refund.assert_called_once_with(payment_dummy, ANY, amount)


@patch("saleor.order.actions.gateway.refund")
def test_create_refund_fulfillment_included_shipping_costs(
    mocked_refund, order_with_lines, payment_dummy
):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    payment = order_with_lines.get_last_payment()
    order_lines_to_refund = order_with_lines.lines.all()
    original_quantity = {
        line.id: line.quantity_unfulfilled for line in order_with_lines.lines.all()
    }
    order_line_ids = order_lines_to_refund.values_list("id", flat=True)
    lines_count = order_with_lines.lines.count()

    returned_fulfillemnt = create_refund_fulfillment(
        requester=None,
        order=order_with_lines,
        payment=payment,
        order_lines_to_refund=[
            OrderLineData(line=line, quantity=2) for line in order_lines_to_refund
        ],
        fulfillment_lines_to_refund=[],
        manager=get_plugins_manager(),
        refund_shipping_costs=True,
    )
    returned_fulfillment_lines = returned_fulfillemnt.lines.all()
    assert returned_fulfillemnt.status == FulfillmentStatus.REFUNDED
    assert len(returned_fulfillment_lines) == lines_count
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids
    for line in order_lines_to_refund:
        assert line.quantity_unfulfilled == original_quantity.get(line.pk) - 2
    amount = sum([line.unit_price_gross_amount * 2 for line in order_lines_to_refund])
    amount += order_with_lines.shipping_price_gross_amount
    mocked_refund.assert_called_once_with(payment_dummy, ANY, amount)


@patch("saleor.order.actions.gateway.refund")
def test_create_refund_fulfillment_only_fulfillment_lines(
    mocked_refund, fulfilled_order, payment_dummy
):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    payment = fulfilled_order.get_last_payment()
    order_line_ids = fulfilled_order.lines.all().values_list("id", flat=True)
    fulfillment_lines = FulfillmentLine.objects.filter(order_line_id__in=order_line_ids)
    original_quantity = {line.id: line.quantity for line in fulfillment_lines}
    fulfillment_lines_to_refund = fulfillment_lines

    returned_fulfillemnt = create_refund_fulfillment(
        requester=None,
        order=fulfilled_order,
        payment=payment,
        order_lines_to_refund=[],
        fulfillment_lines_to_refund=[
            FulfillmentLineData(line=line, quantity=2)
            for line in fulfillment_lines_to_refund
        ],
        manager=get_plugins_manager(),
    )
    returned_fulfillment_lines = returned_fulfillemnt.lines.all()
    assert returned_fulfillemnt.status == FulfillmentStatus.REFUNDED
    assert len(returned_fulfillment_lines) == len(order_line_ids)
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids

    for line in fulfillment_lines:
        assert line.quantity == original_quantity.get(line.pk) - 2
    amount = sum(
        [line.order_line.unit_price_gross_amount * 2 for line in fulfillment_lines]
    )
    mocked_refund.assert_called_once_with(payment_dummy, ANY, amount)


@patch("saleor.order.actions.gateway.refund")
def test_create_refund_fulfillment_custom_amount(
    mocked_refund, fulfilled_order, payment_dummy
):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    payment = fulfilled_order.get_last_payment()
    order_line_ids = fulfilled_order.lines.all().values_list("id", flat=True)
    fulfillment_lines = FulfillmentLine.objects.filter(order_line_id__in=order_line_ids)
    original_quantity = {line.id: line.quantity for line in fulfillment_lines}
    fulfillment_lines_to_refund = fulfillment_lines
    amount = Decimal("10.00")

    returned_fulfillemnt = create_refund_fulfillment(
        requester=None,
        order=fulfilled_order,
        payment=payment,
        order_lines_to_refund=[],
        fulfillment_lines_to_refund=[
            FulfillmentLineData(line=line, quantity=2)
            for line in fulfillment_lines_to_refund
        ],
        manager=get_plugins_manager(),
        amount=amount,
    )

    returned_fulfillment_lines = returned_fulfillemnt.lines.all()
    assert returned_fulfillemnt.status == FulfillmentStatus.REFUNDED
    assert len(returned_fulfillment_lines) == len(order_line_ids)
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids

    for line in fulfillment_lines:
        assert line.quantity == original_quantity.get(line.pk) - 2
    mocked_refund.assert_called_once_with(payment_dummy, ANY, amount)

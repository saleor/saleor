from decimal import Decimal
from unittest.mock import patch

from prices import Money, TaxedMoney

from ...payment import ChargeStatus
from ...plugins.manager import get_plugins_manager
from ...warehouse.models import Allocation, Stock
from .. import FulfillmentLineData, FulfillmentStatus, OrderLineData
from ..actions import create_refund_fulfillment
from ..models import Fulfillment, FulfillmentLine


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
        line.id: line.quantity_unfulfilled for line in order_with_lines
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
        plugin_manager=get_plugins_manager(),
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
    mocked_refund.assert_called_once_with(payment_dummy, amount)


@patch("saleor.order.actions.gateway.refund")
def test_create_refund_fulfillment_multiple_order_line_refunds(
    mocked_refund, order_with_lines, payment_dummy
):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    payment = order_with_lines.get_last_payment()
    order_lines_to_refund = order_with_lines.lines.all()
    original_quantity = {
        line.id: line.quantity_unfulfilled for line in order_with_lines
    }
    order_line_ids = order_lines_to_refund.values_list("id", flat=True)
    lines_count = order_lines_to_refund.count()

    for _ in range(2):
        # call refund two times
        create_refund_fulfillment(
            requester=None,
            order=order_with_lines,
            payment=payment,
            order_lines_to_refund=[
                OrderLineData(line=line, quantity=1) for line in order_lines_to_refund
            ],
            fulfillment_lines_to_refund=[],
            plugin_manager=get_plugins_manager(),
        )

    returned_fulfillemnt = Fulfillment.objects.get(
        order=order_with_lines, status=FulfillmentStatus.REFUNDED
    )
    returned_fulfillment_lines = returned_fulfillemnt.lines.all()
    assert returned_fulfillemnt.status == FulfillmentStatus.REFUNDED
    assert len(returned_fulfillment_lines) == lines_count
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids
    for line in order_lines_to_refund:
        assert line.quantity_unfulfilled == original_quantity.get(line.pk) - 2

    assert mocked_refund.call_count == 2


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
        line.id: line.quantity_unfulfilled for line in order_with_lines
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
        plugin_manager=get_plugins_manager(),
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
    mocked_refund.assert_called_once_with(payment_dummy, amount)


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
        plugin_manager=get_plugins_manager(),
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
    mocked_refund.assert_called_once_with(payment_dummy, amount)


@patch("saleor.order.actions.gateway.refund")
def test_create_refund_fulfillment_multiple_fulfillment_lines_refunds(
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

    for _ in range(2):
        create_refund_fulfillment(
            requester=None,
            order=fulfilled_order,
            payment=payment,
            order_lines_to_refund=[],
            fulfillment_lines_to_refund=[
                FulfillmentLineData(line=line, quantity=1)
                for line in fulfillment_lines_to_refund
            ],
            plugin_manager=get_plugins_manager(),
        )

    returned_fulfillemnt = Fulfillment.objects.get(
        order=fulfilled_order, status=FulfillmentStatus.REFUNDED
    )
    returned_fulfillment_lines = returned_fulfillemnt.lines.all()
    assert returned_fulfillemnt.status == FulfillmentStatus.REFUNDED
    assert len(returned_fulfillment_lines) == len(order_line_ids)
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids

    for line in fulfillment_lines:
        assert line.quantity == original_quantity.get(line.pk) - 2

    assert mocked_refund.call_count == 2


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
        plugin_manager=get_plugins_manager(),
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
    mocked_refund.assert_called_once_with(payment_dummy, amount)


@patch("saleor.order.actions.gateway.refund")
def test_create_refund_fulfillment_multiple_refunds(
    mocked_refund, fulfilled_order, variant, payment_dummy, warehouse, channel_USD
):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    payment = fulfilled_order.get_last_payment()

    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    channel_listing = variant.channel_listings.get()
    net = variant.get_price(variant.product, [], channel_USD, channel_listing)
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    quantity = 5
    unit_price = TaxedMoney(net=net, gross=gross)
    order_line = fulfilled_order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        quantity_fulfilled=2,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=Decimal("0.23"),
        total_price=unit_price * quantity,
    )
    Allocation.objects.create(
        order_line=order_line, stock=stock, quantity_allocated=order_line.quantity
    )
    fulfillment = fulfilled_order.fulfillments.get()
    fulfillment.lines.create(order_line=order_line, quantity=2, stock=stock)

    order_line_ids = fulfilled_order.lines.all().values_list("id", flat=True)
    fulfillment_lines = fulfillment.lines.all()
    original_fulfillment_quantity = {
        line.id: line.quantity for line in fulfillment_lines
    }
    fulfillment_lines_to_refund = fulfillment_lines

    for _ in range(2):
        create_refund_fulfillment(
            requester=None,
            order=fulfilled_order,
            payment=payment,
            order_lines_to_refund=[OrderLineData(line=order_line, quantity=1)],
            fulfillment_lines_to_refund=[
                FulfillmentLineData(line=line, quantity=1)
                for line in fulfillment_lines_to_refund
            ],
            plugin_manager=get_plugins_manager(),
        )

    returned_fulfillemnt = Fulfillment.objects.get(
        order=fulfilled_order, status=FulfillmentStatus.REFUNDED
    )
    returned_fulfillment_lines = returned_fulfillemnt.lines.all()
    assert returned_fulfillemnt.status == FulfillmentStatus.REFUNDED
    assert len(returned_fulfillment_lines) == len(order_line_ids) + 1  # + order line
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids

    for line in fulfillment_lines:
        assert line.quantity == original_fulfillment_quantity.get(line.pk) - 2

    order_line.refresh_from_db()
    assert order_line.quantity_fulfilled == 4
    assert order_line.quantity_unfulfilled == 1
    assert mocked_refund.call_count == 2

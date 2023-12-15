from decimal import Decimal
from unittest.mock import ANY, patch

from prices import Money, TaxedMoney

from ...payment.interface import RefundData
from ...plugins.manager import get_plugins_manager
from ...tests.utils import flush_post_commit_hooks
from ...warehouse.models import Allocation, Stock
from .. import FulfillmentLineData, FulfillmentStatus, OrderEvents, OrderOrigin
from ..actions import create_fulfillments_for_returned_products
from ..fetch import OrderLineInfo
from ..models import Fulfillment, FulfillmentLine


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.order.actions.gateway.refund")
def test_create_return_fulfillment_only_order_lines(
    mocked_refund,
    mocked_order_updated,
    order_with_lines,
    payment_dummy_fully_charged,
    staff_user,
):
    order_with_lines.payments.add(payment_dummy_fully_charged)
    payment = order_with_lines.get_last_payment()

    order_lines_to_return = order_with_lines.lines.all()
    original_quantity = {
        line.id: line.quantity_unfulfilled for line in order_with_lines.lines.all()
    }
    order_line_ids = order_lines_to_return.values_list("id", flat=True)
    original_allocations = list(
        Allocation.objects.filter(order_line_id__in=order_line_ids)
    )
    lines_count = order_with_lines.lines.count()

    response = create_fulfillments_for_returned_products(
        user=staff_user,
        app=None,
        order=order_with_lines,
        payment=payment,
        order_lines=[
            OrderLineInfo(line=line, quantity=2, replace=False)
            for line in order_lines_to_return
        ],
        fulfillment_lines=[],
        manager=get_plugins_manager(allow_replica=False),
    )
    returned_fulfillment, replaced_fulfillment, replace_order = response

    returned_fulfillment_lines = returned_fulfillment.lines.all()
    assert returned_fulfillment.status == FulfillmentStatus.RETURNED
    assert len(returned_fulfillment_lines) == lines_count
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids
    for line in order_lines_to_return:
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
    assert not mocked_refund.called
    assert not replace_order

    # check if we have correct events
    flush_post_commit_hooks()
    events = order_with_lines.events.all()
    assert events.count() == 1
    returned_event = events[0]
    assert returned_event.type == OrderEvents.FULFILLMENT_RETURNED
    assert len(returned_event.parameters["lines"]) == 2
    event_lines = returned_event.parameters["lines"]
    assert order_lines_to_return.filter(id=event_lines[0]["line_pk"]).exists()
    assert event_lines[0]["quantity"] == 2

    assert order_lines_to_return.filter(id=event_lines[1]["line_pk"]).exists()
    assert event_lines[1]["quantity"] == 2

    mocked_order_updated.assert_called_once_with(order_with_lines)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.order.actions.gateway.refund")
def test_create_return_fulfillment_only_order_lines_with_refund(
    mocked_refund,
    mocked_order_updated,
    order_with_lines,
    payment_dummy_fully_charged,
    staff_user,
):
    order_with_lines.payments.add(payment_dummy_fully_charged)
    payment = order_with_lines.get_last_payment()

    order_lines_to_return = order_with_lines.lines.all()
    original_quantity = {
        line.id: line.quantity_unfulfilled for line in order_with_lines.lines.all()
    }
    order_line_ids = order_lines_to_return.values_list("id", flat=True)
    original_allocations = list(
        Allocation.objects.filter(order_line_id__in=order_line_ids)
    )
    lines_count = order_with_lines.lines.count()

    order_lines_to_refund = [
        OrderLineInfo(line=line, quantity=2, replace=False)
        for line in order_lines_to_return
    ]
    response = create_fulfillments_for_returned_products(
        user=staff_user,
        app=None,
        order=order_with_lines,
        payment=payment,
        order_lines=order_lines_to_refund,
        fulfillment_lines=[],
        manager=get_plugins_manager(allow_replica=False),
        refund=True,
    )
    returned_fulfillment, replaced_fulfillment, replace_order = response

    flush_post_commit_hooks()
    returned_fulfillment_lines = returned_fulfillment.lines.all()
    assert returned_fulfillment.status == FulfillmentStatus.REFUNDED_AND_RETURNED
    assert len(returned_fulfillment_lines) == lines_count
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids
    for line in order_lines_to_return:
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

    amount = sum([line.unit_price_gross_amount * 2 for line in order_lines_to_return])
    mocked_refund.assert_called_once_with(
        payment_dummy_fully_charged,
        ANY,
        amount=amount,
        channel_slug=order_with_lines.channel.slug,
        refund_data=RefundData(
            order_lines_to_refund=order_lines_to_refund,
        ),
    )
    assert not replace_order

    assert returned_fulfillment.total_refund_amount == amount
    assert returned_fulfillment.shipping_refund_amount is None

    mocked_order_updated.assert_called_once_with(order_with_lines)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.order.actions.gateway.refund")
def test_create_return_fulfillment_only_order_lines_included_shipping_costs(
    mocked_refund,
    mocked_order_updated,
    order_with_lines,
    payment_dummy_fully_charged,
    staff_user,
):
    order_with_lines.payments.add(payment_dummy_fully_charged)
    payment = order_with_lines.get_last_payment()

    order_lines_to_return = order_with_lines.lines.all()
    original_quantity = {
        line.id: line.quantity_unfulfilled for line in order_with_lines.lines.all()
    }
    order_line_ids = order_lines_to_return.values_list("id", flat=True)
    original_allocations = list(
        Allocation.objects.filter(order_line_id__in=order_line_ids)
    )
    lines_count = order_with_lines.lines.count()

    order_lines_to_refund = [
        OrderLineInfo(line=line, quantity=2, replace=False)
        for line in order_lines_to_return
    ]
    response = create_fulfillments_for_returned_products(
        user=staff_user,
        app=None,
        order=order_with_lines,
        payment=payment,
        order_lines=order_lines_to_refund,
        fulfillment_lines=[],
        manager=get_plugins_manager(allow_replica=False),
        refund=True,
        refund_shipping_costs=True,
    )
    returned_fulfillment, replaced_fulfillment, replace_order = response

    flush_post_commit_hooks()
    returned_fulfillment_lines = returned_fulfillment.lines.all()
    assert returned_fulfillment.status == FulfillmentStatus.REFUNDED_AND_RETURNED
    assert len(returned_fulfillment_lines) == lines_count
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids
    for line in order_lines_to_return:
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

    amount = sum([line.unit_price_gross_amount * 2 for line in order_lines_to_return])
    amount += order_with_lines.shipping_price_gross_amount
    mocked_refund.assert_called_once_with(
        payment_dummy_fully_charged,
        ANY,
        amount=amount,
        channel_slug=order_with_lines.channel.slug,
        refund_data=RefundData(
            order_lines_to_refund=order_lines_to_refund,
            refund_shipping_costs=True,
        ),
    )
    assert not replace_order

    assert returned_fulfillment.total_refund_amount == amount
    assert (
        returned_fulfillment.shipping_refund_amount
        == order_with_lines.shipping_price_gross_amount
    )

    mocked_order_updated.assert_called_once_with(order_with_lines)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.order.actions.gateway.refund")
def test_create_return_fulfillment_only_order_lines_with_replace_request(
    mocked_refund,
    mocked_order_updated,
    order_with_lines,
    payment_dummy_fully_charged,
    staff_user,
):
    order_with_lines.payments.add(payment_dummy_fully_charged)
    payment = order_with_lines.get_last_payment()

    order_lines_to_return = order_with_lines.lines.all()
    original_quantity = {
        line.id: line.quantity_unfulfilled for line in order_with_lines.lines.all()
    }
    order_line_ids = order_lines_to_return.values_list("id", flat=True)
    original_allocations = list(
        Allocation.objects.filter(order_line_id__in=order_line_ids)
    )
    lines_count = order_with_lines.lines.count()
    quantity_to_replace = 2
    order_lines_data = [
        OrderLineInfo(line=line, quantity=2, replace=False)
        for line in order_lines_to_return
    ]

    # set replace request for the first line
    order_lines_data[0].replace = True
    order_lines_data[0].quantity = quantity_to_replace

    # set metadata
    order_with_lines.metadata = {"test_key": "test_val"}
    order_with_lines.private_metadata = {"priv_test_key": "priv_test_val"}
    order_with_lines.save(update_fields=["metadata", "private_metadata"])

    response = create_fulfillments_for_returned_products(
        user=staff_user,
        app=None,
        order=order_with_lines,
        payment=payment,
        order_lines=order_lines_data,
        fulfillment_lines=[],
        manager=get_plugins_manager(allow_replica=False),
    )
    returned_fulfillment, replaced_fulfillment, replace_order = response

    flush_post_commit_hooks()
    returned_fulfillment_lines = returned_fulfillment.lines.all()
    assert returned_fulfillment.status == FulfillmentStatus.RETURNED
    # we replaced one line
    assert len(returned_fulfillment_lines) == lines_count - 1

    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids

    order_lines_to_return = order_with_lines.lines.all()
    for line in order_lines_to_return:
        assert line.quantity_unfulfilled == original_quantity.get(line.pk) - 2

    replaced_fulfillment_lines = replaced_fulfillment.lines.all()
    assert replaced_fulfillment_lines.count() == 1
    assert replaced_fulfillment_lines[0].quantity == quantity_to_replace
    assert replaced_fulfillment_lines[0].order_line_id == order_lines_data[0].line.id

    current_allocations = Allocation.objects.in_bulk(
        [allocation.pk for allocation in original_allocations]
    )
    for original_allocation in original_allocations:
        current_allocation = current_allocations.get(original_allocation.pk)
        assert (
            original_allocation.quantity_allocated - 2
            == current_allocation.quantity_allocated
        )

    order_with_lines.refresh_from_db()

    # refund should not be called
    assert not mocked_refund.called

    # new order should have own id
    assert replace_order.id != order_with_lines.id

    # make sure that we have new instances of addresses
    assert replace_order.shipping_address.id != order_with_lines.shipping_address.id
    assert replace_order.billing_address.id != order_with_lines.billing_address.id

    # the rest of address data should be the same
    replace_order.shipping_address.id = None
    order_with_lines.shipping_address.id = None
    assert replace_order.shipping_address == order_with_lines.shipping_address

    replace_order.billing_address.id = None
    order_with_lines.billing_address.id = None
    assert replace_order.billing_address == order_with_lines.billing_address
    assert replace_order.original == order_with_lines
    assert replace_order.origin == OrderOrigin.REISSUE
    assert replace_order.metadata == order_with_lines.metadata
    assert replace_order.private_metadata == order_with_lines.private_metadata

    expected_replaced_line = order_lines_to_return[0]

    assert replace_order.lines.count() == 1
    replaced_line = replace_order.lines.first()
    # make sure that all data from original line is in replaced line
    assert replaced_line.variant_id == expected_replaced_line.variant_id
    assert replaced_line.product_name == expected_replaced_line.product_name
    assert replaced_line.variant_name == expected_replaced_line.variant_name
    assert replaced_line.product_sku == expected_replaced_line.product_sku
    assert replaced_line.product_variant_id == expected_replaced_line.product_variant_id
    assert (
        replaced_line.is_shipping_required
        == expected_replaced_line.is_shipping_required
    )
    assert replaced_line.quantity == quantity_to_replace
    assert replaced_line.quantity_fulfilled == 0
    assert replaced_line.currency == expected_replaced_line.currency
    assert (
        replaced_line.unit_price_net_amount
        == expected_replaced_line.unit_price_net_amount
    )
    assert (
        replaced_line.unit_price_gross_amount
        == expected_replaced_line.unit_price_gross_amount
    )
    assert replaced_line.tax_rate == expected_replaced_line.tax_rate

    mocked_order_updated.assert_called_once_with(order_with_lines)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.order.actions.gateway.refund")
def test_create_return_fulfillment_only_fulfillment_lines(
    mocked_refund,
    mocked_order_updated,
    fulfilled_order,
    payment_dummy_fully_charged,
    staff_user,
):
    fulfilled_order.payments.add(payment_dummy_fully_charged)
    payment = fulfilled_order.get_last_payment()
    order_line_ids = fulfilled_order.lines.all().values_list("id", flat=True)
    fulfillment_lines = FulfillmentLine.objects.filter(order_line_id__in=order_line_ids)
    original_quantity = {line.id: line.quantity for line in fulfillment_lines}

    response = create_fulfillments_for_returned_products(
        user=staff_user,
        app=None,
        order=fulfilled_order,
        payment=payment,
        order_lines=[],
        fulfillment_lines=[
            FulfillmentLineData(line=line, quantity=2, replace=False)
            for line in fulfillment_lines
        ],
        manager=get_plugins_manager(allow_replica=False),
    )

    returned_fulfillment, replaced_fulfillment, replace_order = response

    flush_post_commit_hooks()
    returned_fulfillment_lines = returned_fulfillment.lines.all()
    assert returned_fulfillment.status == FulfillmentStatus.RETURNED
    assert returned_fulfillment_lines.count() == len(order_line_ids)

    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids

    for line in fulfillment_lines:
        assert line.quantity == original_quantity.get(line.pk) - 2

    assert not mocked_refund.called
    assert not replace_order

    mocked_order_updated.assert_called_once_with(fulfilled_order)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.order.actions.gateway.refund")
def test_create_return_fulfillment_only_fulfillment_lines_replace_order(
    mocked_refund,
    mocked_order_updated,
    fulfilled_order,
    payment_dummy_fully_charged,
    staff_user,
):
    fulfilled_order.payments.add(payment_dummy_fully_charged)
    payment = fulfilled_order.get_last_payment()
    order_line_ids = fulfilled_order.lines.all().values_list("id", flat=True)
    fulfillment_lines = FulfillmentLine.objects.filter(order_line_id__in=order_line_ids)
    original_quantity = {line.id: line.quantity for line in fulfillment_lines}

    # Prepare the structure for return method
    fulfillment_lines_to_return = [
        FulfillmentLineData(line=line, quantity=2, replace=False)
        for line in fulfillment_lines
    ]
    # The line which should be replaced
    replace_quantity = 2
    fulfillment_lines_to_return[0].replace = True
    fulfillment_lines_to_return[0].quantity = replace_quantity

    response = create_fulfillments_for_returned_products(
        user=staff_user,
        app=None,
        order=fulfilled_order,
        payment=payment,
        order_lines=[],
        fulfillment_lines=fulfillment_lines_to_return,
        manager=get_plugins_manager(allow_replica=False),
    )

    returned_fulfillment, replaced_fulfillment, replace_order = response

    flush_post_commit_hooks()
    returned_fulfillment_lines = returned_fulfillment.lines.all()
    assert returned_fulfillment.status == FulfillmentStatus.RETURNED
    # make sure that all order lines from refund are in expected fulfillment
    # minus one as we replaced the one item
    assert returned_fulfillment_lines.count() == len(order_line_ids) - 1

    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids

    for line in fulfillment_lines:
        assert line.quantity == original_quantity.get(line.pk) - 2

    replaced_fulfillment_lines = replaced_fulfillment.lines.all()
    assert replaced_fulfillment_lines.count() == 1
    assert replaced_fulfillment_lines[0].quantity == replace_quantity
    assert (
        replaced_fulfillment_lines[0].order_line_id
        == fulfillment_lines_to_return[0].line.order_line_id
    )

    assert not mocked_refund.called

    # new order should have own id
    assert replace_order.id != fulfilled_order.id

    # make sure that we have new instances of addresses
    assert replace_order.shipping_address.id != fulfilled_order.shipping_address.id
    assert replace_order.billing_address.id != fulfilled_order.billing_address.id

    # the rest of address data should be the same
    replace_order.shipping_address.id = None
    fulfilled_order.shipping_address.id = None
    assert replace_order.shipping_address == fulfilled_order.shipping_address

    replace_order.billing_address.id = None
    fulfilled_order.billing_address.id = None
    assert replace_order.billing_address == fulfilled_order.billing_address

    expected_replaced_line = fulfillment_lines[0].order_line

    assert replace_order.lines.count() == 1
    replaced_line = replace_order.lines.first()
    # make sure that all data from original line is in replaced line
    assert replaced_line.variant_id == expected_replaced_line.variant_id
    assert replaced_line.product_name == expected_replaced_line.product_name
    assert replaced_line.variant_name == expected_replaced_line.variant_name
    assert replaced_line.product_sku == expected_replaced_line.product_sku
    assert replaced_line.product_variant_id == expected_replaced_line.product_variant_id
    assert (
        replaced_line.is_shipping_required
        == expected_replaced_line.is_shipping_required
    )
    assert replaced_line.quantity == replace_quantity
    assert replaced_line.quantity_fulfilled == 0
    assert replaced_line.currency == expected_replaced_line.currency
    assert (
        replaced_line.unit_price_net_amount
        == expected_replaced_line.unit_price_net_amount
    )
    assert (
        replaced_line.unit_price_gross_amount
        == expected_replaced_line.unit_price_gross_amount
    )
    assert replaced_line.tax_rate == expected_replaced_line.tax_rate

    mocked_order_updated.assert_called_once_with(fulfilled_order)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.order.actions.gateway.refund")
def test_create_return_fulfillment_with_lines_already_refunded(
    mocked_refund,
    mocked_order_updated,
    fulfilled_order,
    payment_dummy_fully_charged,
    staff_user,
    channel_USD,
    variant,
    warehouse,
):
    fulfilled_order.payments.add(payment_dummy_fully_charged)
    payment = fulfilled_order.get_last_payment()
    order_line_ids = fulfilled_order.lines.all().values_list("id", flat=True)
    fulfillment_lines = FulfillmentLine.objects.filter(order_line_id__in=order_line_ids)
    original_quantity = {line.id: line.quantity for line in fulfillment_lines}
    fulfillment_lines_to_return = fulfillment_lines

    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )

    channel_listing = variant.channel_listings.get()
    net = variant.get_price(channel_listing)
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    quantity = 5
    order_line = fulfilled_order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        quantity_fulfilled=2,
        variant=variant,
        unit_price=unit_price,
        tax_rate=Decimal("0.23"),
        total_price=unit_price * quantity,
    )
    Allocation.objects.create(
        order_line=order_line, stock=stock, quantity_allocated=order_line.quantity
    )
    refunded_fulfillment = Fulfillment.objects.create(
        order=fulfilled_order, status=FulfillmentStatus.REFUNDED
    )
    refunded_fulfillment_line = refunded_fulfillment.lines.create(
        order_line=order_line, quantity=2
    )
    fulfilled_order.fulfillments.add(refunded_fulfillment)

    fulfillment_lines_to_process = [
        FulfillmentLineData(line=line, quantity=2)
        for line in fulfillment_lines_to_return
    ]
    fulfillment_lines_to_process.append(
        FulfillmentLineData(line=refunded_fulfillment_line, quantity=2)
    )
    create_fulfillments_for_returned_products(
        user=staff_user,
        app=None,
        order=fulfilled_order,
        payment=payment,
        order_lines=[],
        fulfillment_lines=fulfillment_lines_to_process,
        manager=get_plugins_manager(allow_replica=False),
        refund=True,
    )

    flush_post_commit_hooks()
    returned_and_refunded_fulfillment = Fulfillment.objects.get(
        order=fulfilled_order, status=FulfillmentStatus.REFUNDED_AND_RETURNED
    )
    returned_and_refunded_lines = returned_and_refunded_fulfillment.lines.all()

    assert returned_and_refunded_lines.count() == len(order_line_ids)
    for fulfillment_line in returned_and_refunded_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids

    for line in fulfillment_lines:
        assert line.quantity == original_quantity.get(line.pk) - 2

    # the already refunded line is not included in amount
    amount = sum(
        [
            line.order_line.unit_price_gross_amount * 2
            for line in fulfillment_lines_to_return
        ]
    )
    mocked_refund.assert_called_once_with(
        payment_dummy_fully_charged,
        ANY,
        amount=amount,
        channel_slug=fulfilled_order.channel.slug,
        refund_data=RefundData(
            fulfillment_lines_to_refund=fulfillment_lines_to_process,
        ),
    )

    assert returned_and_refunded_fulfillment.total_refund_amount == amount
    assert returned_and_refunded_fulfillment.shipping_refund_amount is None

    mocked_order_updated.assert_called_once_with(fulfilled_order)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.order.actions.gateway.refund")
def test_create_return_fulfillment_only_order_lines_with_old_ids(
    mocked_refund,
    mocked_order_updated,
    order_with_lines,
    payment_dummy_fully_charged,
    staff_user,
):
    order_with_lines.payments.add(payment_dummy_fully_charged)
    payment = order_with_lines.get_last_payment()

    order_lines_to_return = order_with_lines.lines.all()
    order_lines_to_return[0].old_id = 16
    order_lines_to_return[1].old_id = 12
    original_quantity = {
        line.id: line.quantity_unfulfilled for line in order_with_lines.lines.all()
    }
    order_line_ids = order_lines_to_return.values_list("id", flat=True)
    original_allocations = list(
        Allocation.objects.filter(order_line_id__in=order_line_ids)
    )
    lines_count = order_with_lines.lines.count()

    response = create_fulfillments_for_returned_products(
        user=staff_user,
        app=None,
        order=order_with_lines,
        payment=payment,
        order_lines=[
            OrderLineInfo(line=line, quantity=2, replace=False)
            for line in order_lines_to_return
        ],
        fulfillment_lines=[],
        manager=get_plugins_manager(allow_replica=False),
    )
    returned_fulfillment, replaced_fulfillment, replace_order = response

    returned_fulfillment_lines = returned_fulfillment.lines.all()
    assert returned_fulfillment.status == FulfillmentStatus.RETURNED
    assert len(returned_fulfillment_lines) == lines_count
    for fulfillment_line in returned_fulfillment_lines:
        assert fulfillment_line.quantity == 2
        assert fulfillment_line.order_line_id in order_line_ids
    for line in order_lines_to_return:
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
    assert not mocked_refund.called
    assert not replace_order

    # check if we have correct events
    flush_post_commit_hooks()
    events = order_with_lines.events.all()
    assert events.count() == 1
    returned_event = events[0]
    assert returned_event.type == OrderEvents.FULFILLMENT_RETURNED
    assert len(returned_event.parameters["lines"]) == 2
    event_lines = returned_event.parameters["lines"]
    assert order_lines_to_return.filter(id=event_lines[0]["line_pk"]).exists()
    assert event_lines[0]["quantity"] == 2

    assert order_lines_to_return.filter(id=event_lines[1]["line_pk"]).exists()
    assert event_lines[1]["quantity"] == 2

    mocked_order_updated.assert_called_once_with(order_with_lines)

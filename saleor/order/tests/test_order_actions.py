from decimal import Decimal
from unittest.mock import patch

import pytest
from prices import Money, TaxedMoney

from ...payment import ChargeStatus, PaymentError, TransactionKind
from ...payment.models import Payment
from ...product.models import DigitalContent
from ...product.tests.utils import create_image
from ...warehouse.models import Allocation, Stock
from .. import FulfillmentStatus, OrderEvents, OrderEventsEmails, OrderStatus
from ..actions import (
    automatically_fulfill_digital_lines,
    cancel_fulfillment,
    cancel_order,
    clean_mark_order_as_paid,
    create_refund_fulfillment,
    fulfill_order_line,
    handle_fully_paid_order,
    mark_order_as_paid,
    order_refunded,
)
from ..models import Fulfillment, FulfillmentLine


@pytest.fixture
def order_with_digital_line(order, digital_content, stock, site_settings):
    site_settings.automatic_fulfillment_digital_products = True
    site_settings.save()

    variant = stock.product_variant
    variant.digital_content = digital_content
    variant.digital_content.save()

    product_type = variant.product.product_type
    product_type.is_shipping_required = False
    product_type.is_digital = True
    product_type.save()

    quantity = 3
    product = variant.product
    channel = order.channel
    variant_channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(product, [], channel, variant_channel_listing, None)
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
    )

    Allocation.objects.create(order_line=line, stock=stock, quantity_allocated=quantity)

    return order


@patch("saleor.order.emails.send_fulfillment_confirmation.delay")
@patch("saleor.order.emails.send_payment_confirmation.delay")
def test_handle_fully_paid_order_digital_lines(
    mock_send_payment_confirmation,
    mock_send_fulfillment_confirmation,
    order_with_digital_line,
):
    redirect_url = "http://localhost.pl"
    order = order_with_digital_line
    order.redirect_url = redirect_url
    order.save()
    handle_fully_paid_order(order)

    fulfillment = order.fulfillments.first()

    (
        event_order_paid,
        event_email_sent,
        event_order_fulfilled,
        event_digital_links,
    ) = order.events.all()
    assert event_order_paid.type == OrderEvents.ORDER_FULLY_PAID

    assert event_email_sent.type == OrderEvents.EMAIL_SENT
    assert event_order_fulfilled.type == OrderEvents.EMAIL_SENT
    assert event_digital_links.type == OrderEvents.EMAIL_SENT

    assert (
        event_order_fulfilled.parameters["email_type"] == OrderEventsEmails.FULFILLMENT
    )
    assert (
        event_digital_links.parameters["email_type"] == OrderEventsEmails.DIGITAL_LINKS
    )

    mock_send_payment_confirmation.assert_called_once_with(order.pk)
    mock_send_fulfillment_confirmation.assert_called_once_with(
        order.pk, fulfillment.pk, redirect_url
    )

    order.refresh_from_db()
    assert order.status == OrderStatus.FULFILLED


@patch("saleor.order.emails.send_payment_confirmation.delay")
def test_handle_fully_paid_order(mock_send_payment_confirmation, order):
    handle_fully_paid_order(order)
    event_order_paid, event_email_sent = order.events.all()
    assert event_order_paid.type == OrderEvents.ORDER_FULLY_PAID

    assert event_email_sent.type == OrderEvents.EMAIL_SENT
    assert event_email_sent.parameters == {
        "email": order.get_customer_email(),
        "email_type": OrderEventsEmails.PAYMENT,
    }

    mock_send_payment_confirmation.assert_called_once_with(order.pk)


@patch("saleor.order.emails.send_payment_confirmation.delay")
def test_handle_fully_paid_order_no_email(mock_send_payment_confirmation, order):
    order.user = None
    order.user_email = ""

    handle_fully_paid_order(order)
    event = order.events.get()
    assert event.type == OrderEvents.ORDER_FULLY_PAID
    assert not mock_send_payment_confirmation.called


def test_mark_as_paid(admin_user, draft_order):
    mark_order_as_paid(draft_order, admin_user)
    payment = draft_order.payments.last()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == draft_order.total.gross.amount
    assert draft_order.events.last().type == (OrderEvents.ORDER_MARKED_AS_PAID)
    transactions = payment.transactions.all()
    assert transactions.count() == 1
    assert transactions[0].kind == TransactionKind.EXTERNAL


def test_mark_as_paid_with_external_reference(admin_user, draft_order):
    external_reference = "transaction_id"
    mark_order_as_paid(draft_order, admin_user, external_reference=external_reference)
    payment = draft_order.payments.last()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == draft_order.total.gross.amount
    assert draft_order.events.last().type == (OrderEvents.ORDER_MARKED_AS_PAID)
    transactions = payment.transactions.all()
    assert transactions.count() == 1
    assert transactions[0].kind == TransactionKind.EXTERNAL
    assert transactions[0].searchable_key == external_reference
    assert transactions[0].token == external_reference


def test_mark_as_paid_no_billing_address(admin_user, draft_order):
    draft_order.billing_address = None
    draft_order.save()

    with pytest.raises(Exception):
        mark_order_as_paid(draft_order, admin_user)


def test_clean_mark_order_as_paid(payment_txn_preauth):
    order = payment_txn_preauth.order
    with pytest.raises(PaymentError):
        clean_mark_order_as_paid(order)


def test_cancel_fulfillment(fulfilled_order, warehouse):
    fulfillment = fulfilled_order.fulfillments.first()
    line_1, line_2 = fulfillment.lines.all()

    cancel_fulfillment(fulfillment, None, warehouse)

    fulfillment.refresh_from_db()
    fulfilled_order.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.CANCELED
    assert fulfilled_order.status == OrderStatus.UNFULFILLED
    assert line_1.order_line.quantity_fulfilled == 0
    assert line_2.order_line.quantity_fulfilled == 0


def test_cancel_fulfillment_variant_witout_inventory_tracking(
    fulfilled_order_without_inventory_tracking, warehouse
):
    fulfillment = fulfilled_order_without_inventory_tracking.fulfillments.first()
    line = fulfillment.lines.first()
    stock = line.order_line.variant.stocks.get()
    stock_quantity_before = stock.quantity

    cancel_fulfillment(fulfillment, None, warehouse)

    fulfillment.refresh_from_db()
    line.refresh_from_db()
    fulfilled_order_without_inventory_tracking.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.CANCELED
    assert line.order_line.quantity_fulfilled == 0
    assert fulfilled_order_without_inventory_tracking.status == OrderStatus.UNFULFILLED
    assert stock_quantity_before == line.order_line.variant.stocks.get().quantity


@patch("saleor.order.actions.send_order_canceled_confirmation")
def test_cancel_order(
    send_order_canceled_confirmation_mock,
    fulfilled_order_with_all_cancelled_fulfillments,
):
    # given
    order = fulfilled_order_with_all_cancelled_fulfillments

    assert Allocation.objects.filter(
        order_line__order=order, quantity_allocated__gt=0
    ).exists()

    # when
    cancel_order(order, None)

    # then
    order_event = order.events.last()
    assert order_event.type == OrderEvents.CANCELED

    assert order.status == OrderStatus.CANCELED
    assert not Allocation.objects.filter(
        order_line__order=order, quantity_allocated__gt=0
    ).exists()

    send_order_canceled_confirmation_mock.assert_called_once_with(order, None)


@patch("saleor.order.actions.send_order_refunded_confirmation")
def test_order_refunded(
    send_order_refunded_confirmation_mock,
    order,
    checkout_with_item,
):
    # given
    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy", is_active=True, checkout=checkout_with_item
    )
    amount = order.total.gross.amount

    # when
    order_refunded(order, order.user, amount, payment)

    # then
    order_event = order.events.last()
    assert order_event.type == OrderEvents.PAYMENT_REFUNDED

    send_order_refunded_confirmation_mock.assert_called_once_with(
        order, order.user, amount, payment.currency
    )


def test_fulfill_order_line(order_with_lines):
    order = order_with_lines
    line = order.lines.first()
    quantity_fulfilled_before = line.quantity_fulfilled
    variant = line.variant
    stock = Stock.objects.get(product_variant=variant)
    stock_quantity_after = stock.quantity - line.quantity

    fulfill_order_line(line, line.quantity, stock.warehouse.pk)

    stock.refresh_from_db()
    assert stock.quantity == stock_quantity_after
    assert line.quantity_fulfilled == quantity_fulfilled_before + line.quantity


def test_fulfill_order_line_with_variant_deleted(order_with_lines):
    line = order_with_lines.lines.first()
    line.variant.delete()

    line.refresh_from_db()

    fulfill_order_line(line, line.quantity, "warehouse_pk")


def test_fulfill_order_line_without_inventory_tracking(order_with_lines):
    order = order_with_lines
    line = order.lines.first()
    quantity_fulfilled_before = line.quantity_fulfilled
    variant = line.variant
    variant.track_inventory = False
    variant.save()
    stock = Stock.objects.get(product_variant=variant)

    # stock should not change
    stock_quantity_after = stock.quantity

    fulfill_order_line(line, line.quantity, stock.warehouse.pk)

    stock.refresh_from_db()
    assert stock.quantity == stock_quantity_after
    assert line.quantity_fulfilled == quantity_fulfilled_before + line.quantity


@patch("saleor.order.actions.emails.send_fulfillment_confirmation")
@patch("saleor.order.utils.get_default_digital_content_settings")
def test_fulfill_digital_lines(
    mock_digital_settings, mock_email_fulfillment, order_with_lines, media_root
):
    mock_digital_settings.return_value = {"automatic_fulfillment": True}
    line = order_with_lines.lines.all()[0]

    image_file, image_name = create_image()
    variant = line.variant
    digital_content = DigitalContent.objects.create(
        content_file=image_file, product_variant=variant, use_default_settings=True
    )

    line.variant.digital_content = digital_content
    line.is_shipping_required = False
    line.save()

    order_with_lines.refresh_from_db()
    automatically_fulfill_digital_lines(order_with_lines)
    line.refresh_from_db()
    fulfillment = Fulfillment.objects.get(order=order_with_lines)
    fulfillment_lines = fulfillment.lines.all()

    assert fulfillment_lines.count() == 1
    assert line.digital_content_url
    assert mock_email_fulfillment.delay.called


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
    order_lines_quantities_to_refund = [2 for _ in range(lines_count)]
    fulfillment_lines_to_refund = []
    fulfillment_lines_quantities_to_refund = []
    returned_fulfillemnt = create_refund_fulfillment(
        requester=None,
        order=order_with_lines,
        payment=payment,
        order_lines_to_refund=order_lines_to_refund,
        order_lines_quantities_to_refund=order_lines_quantities_to_refund,
        fulfillment_lines_to_refund=fulfillment_lines_to_refund,
        fulfillment_lines_quantities_to_refund=fulfillment_lines_quantities_to_refund,
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
    order_lines_quantities_to_refund = [1 for _ in range(order_lines_to_refund.count())]
    lines_count = order_lines_to_refund.count()
    for _ in range(2):
        # call refund two times
        create_refund_fulfillment(
            requester=None,
            order=order_with_lines,
            payment=payment,
            order_lines_to_refund=order_lines_to_refund,
            order_lines_quantities_to_refund=order_lines_quantities_to_refund,
            fulfillment_lines_to_refund=[],
            fulfillment_lines_quantities_to_refund=[],
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
    order_lines_quantities_to_refund = [2 for _ in range(lines_count)]
    fulfillment_lines_to_refund = []
    fulfillment_lines_quantities_to_refund = []
    returned_fulfillemnt = create_refund_fulfillment(
        requester=None,
        order=order_with_lines,
        payment=payment,
        order_lines_to_refund=order_lines_to_refund,
        order_lines_quantities_to_refund=order_lines_quantities_to_refund,
        fulfillment_lines_to_refund=fulfillment_lines_to_refund,
        fulfillment_lines_quantities_to_refund=fulfillment_lines_quantities_to_refund,
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
    fulfillment_lines_count = fulfillment_lines.count()
    fulfillment_lines_to_refund = fulfillment_lines
    fulfillment_lines_quantities_to_refund = [2 for _ in range(fulfillment_lines_count)]
    returned_fulfillemnt = create_refund_fulfillment(
        requester=None,
        order=fulfilled_order,
        payment=payment,
        order_lines_to_refund=[],
        order_lines_quantities_to_refund=[],
        fulfillment_lines_to_refund=fulfillment_lines_to_refund,
        fulfillment_lines_quantities_to_refund=fulfillment_lines_quantities_to_refund,
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
    fulfillment_lines_count = fulfillment_lines.count()
    fulfillment_lines_to_refund = fulfillment_lines
    fulfillment_lines_quantities_to_refund = [1 for _ in range(fulfillment_lines_count)]
    for _ in range(2):
        create_refund_fulfillment(
            requester=None,
            order=fulfilled_order,
            payment=payment,
            order_lines_to_refund=[],
            order_lines_quantities_to_refund=[],
            fulfillment_lines_to_refund=fulfillment_lines_to_refund,
            fulfillment_lines_quantities_to_refund=(
                fulfillment_lines_quantities_to_refund
            ),
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
    fulfillment_lines_count = fulfillment_lines.count()
    fulfillment_lines_to_refund = fulfillment_lines
    fulfillment_lines_quantities_to_refund = [2 for _ in range(fulfillment_lines_count)]
    amount = Decimal("10.00")
    returned_fulfillemnt = create_refund_fulfillment(
        requester=None,
        order=fulfilled_order,
        payment=payment,
        order_lines_to_refund=[],
        order_lines_quantities_to_refund=[],
        fulfillment_lines_to_refund=fulfillment_lines_to_refund,
        fulfillment_lines_quantities_to_refund=fulfillment_lines_quantities_to_refund,
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
    mocked_refund,
    fulfilled_order,
    variant,
    payment_dummy,
    warehouse,
    channel_USD,
    collection,
):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    payment = fulfilled_order.get_last_payment()
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)

    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    net = variant.get_price(
        variant.product, [collection], channel_USD, variant_channel_listing, []
    )
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
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
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
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

    fulfillment_lines_count = fulfillment_lines.count()
    fulfillment_lines_to_refund = fulfillment_lines
    fulfillment_lines_quantities_to_refund = [1 for _ in range(fulfillment_lines_count)]

    for _ in range(2):
        create_refund_fulfillment(
            requester=None,
            order=fulfilled_order,
            payment=payment,
            order_lines_to_refund=[order_line],
            order_lines_quantities_to_refund=[1],
            fulfillment_lines_to_refund=fulfillment_lines_to_refund,
            fulfillment_lines_quantities_to_refund=(
                fulfillment_lines_quantities_to_refund
            ),
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

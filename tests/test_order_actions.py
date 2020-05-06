from decimal import Decimal
from unittest.mock import patch

import pytest
from prices import Money, TaxedMoney

from saleor.order import FulfillmentStatus, OrderEvents, OrderEventsEmails, OrderStatus
from saleor.order.actions import (
    automatically_fulfill_digital_lines,
    cancel_fulfillment,
    cancel_order,
    clean_mark_order_as_paid,
    fulfill_order_line,
    handle_fully_paid_order,
    mark_order_as_paid,
)
from saleor.order.models import Fulfillment
from saleor.payment import ChargeStatus, PaymentError
from saleor.product.models import DigitalContent
from saleor.warehouse.models import Allocation, Stock

from .utils import create_image


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
    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=23,
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

    order = order_with_digital_line
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
    mock_send_fulfillment_confirmation.assert_called_once_with(order.pk, fulfillment.pk)

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


def test_cancel_order(fulfilled_order_with_all_cancelled_fulfillments):
    order = fulfilled_order_with_all_cancelled_fulfillments

    assert Allocation.objects.filter(
        order_line__order=order, quantity_allocated__gt=0
    ).exists()

    cancel_order(order, None)

    order_event = order.events.last()
    assert order_event.type == OrderEvents.CANCELED

    assert order.status == OrderStatus.CANCELED
    assert not Allocation.objects.filter(
        order_line__order=order, quantity_allocated__gt=0
    ).exists()


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

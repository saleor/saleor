import logging
from decimal import Decimal
from typing import TYPE_CHECKING, List

from django.db import transaction

from ..core import analytics
from ..plugins.manager import get_plugins_manager
from ..payment import ChargeStatus, CustomPaymentChoices, PaymentError
from ..warehouse.management import decrease_stock
from . import FulfillmentStatus, OrderStatus, emails, events, utils
from .emails import send_fulfillment_confirmation_to_customer, send_payment_confirmation
from .models import Fulfillment, FulfillmentLine
from .utils import (
    get_order_country,
    order_line_needs_automatic_fulfillment,
    recalculate_order,
    restock_fulfillment_lines,
    update_order_status,
)

if TYPE_CHECKING:
    from .models import Order
    from ..account.models import User
    from ..payment.models import Payment


logger = logging.getLogger(__name__)


def order_created(order: "Order", user: "User", from_draft: bool = False):
    events.order_created_event(order=order, user=user, from_draft=from_draft)
    manager = get_plugins_manager()
    manager.order_created(order)


def handle_fully_paid_order(order: "Order"):
    events.order_fully_paid_event(order=order)

    if order.get_customer_email():
        events.email_sent_event(
            order=order, user=None, email_type=events.OrderEventsEmails.PAYMENT
        )
        send_payment_confirmation.delay(order.pk)

        if utils.order_needs_automatic_fullfilment(order):
            automatically_fulfill_digital_lines(order)
    try:
        analytics.report_order(order.tracking_client_id, order)
    except Exception:
        # Analytics failing should not abort the checkout flow
        logger.exception("Recording order in analytics failed")
    manager = get_plugins_manager()
    manager.order_fully_paid(order)
    manager.order_updated(order)


def cancel_order(order: "Order", user: "User", restock: bool):
    """Cancel order and associated fulfillments.

    Return products to corresponding stocks if restock is set to True.
    """

    events.order_canceled_event(order=order, user=user)
    if restock:
        events.fulfillment_restocked_items_event(
            order=order, user=user, fulfillment=order
        )
        utils.restock_order_lines(order)

    for fulfillment in order.fulfillments.all():
        fulfillment.status = FulfillmentStatus.CANCELED
        fulfillment.save(update_fields=["status"])
    order.status = OrderStatus.CANCELED
    order.save(update_fields=["status"])

    payments = order.payments.filter(is_active=True).exclude(
        charge_status=ChargeStatus.FULLY_REFUNDED
    )

    from ..payment import gateway

    for payment in payments:
        if payment.can_refund():
            gateway.refund(payment)
        elif payment.can_void():
            gateway.void(payment)

    manager = get_plugins_manager()
    manager.order_cancelled(order)
    manager.order_updated(order)


def order_refunded(order: "Order", user: "User", amount: "Decimal", payment: "Payment"):
    events.payment_refunded_event(
        order=order, user=user, amount=amount, payment=payment
    )
    get_plugins_manager().order_updated(order)


def order_voided(order: "Order", user: "User", payment: "Payment"):
    events.payment_voided_event(order=order, user=user, payment=payment)
    get_plugins_manager().order_updated(order)


def order_fulfilled(
    fulfillment: "Fulfillment",
    user: "User",
    fulfillment_lines: List["FulfillmentLine"],
    notify_customer=True,
):
    order = fulfillment.order
    update_order_status(order)
    events.fulfillment_fulfilled_items_event(
        order=order, user=user, fulfillment_lines=fulfillment_lines
    )
    manager = get_plugins_manager()
    manager.order_updated(order)
    manager.fulfillment_created(fulfillment)

    if order.status == OrderStatus.FULFILLED:
        manager.order_fulfilled(order)

    if notify_customer:
        send_fulfillment_confirmation_to_customer(order, fulfillment, user)


def order_shipping_updated(order: "Order"):
    recalculate_order(order)
    get_plugins_manager().order_updated(order)


def order_captured(order: "Order", user: "User", amount: "Decimal", payment: "Payment"):
    events.payment_captured_event(
        order=order, user=user, amount=amount, payment=payment
    )
    get_plugins_manager().order_updated(order)


def fulfillment_tracking_updated(
    fulfillment: "Fulfillment", user: "User", tracking_number: str
):
    events.fulfillment_tracking_updated_event(
        order=fulfillment.order,
        user=user,
        tracking_number=tracking_number,
        fulfillment=fulfillment,
    )
    get_plugins_manager().order_updated(fulfillment.order)


def cancel_fulfillment(fulfillment: "Fulfillment", user: "User", restock: bool):
    """Cancel fulfillment.

    Return products to corresponding stocks if restock is set to True.
    """
    events.fulfillment_canceled_event(
        order=fulfillment.order, user=user, fulfillment=fulfillment
    )
    if restock:
        events.fulfillment_restocked_items_event(
            order=fulfillment.order, user=user, fulfillment=fulfillment
        )
        restock_fulfillment_lines(fulfillment)
    for line in fulfillment:
        order_line = line.order_line
        order_line.quantity_fulfilled -= line.quantity
        order_line.save(update_fields=["quantity_fulfilled"])
    fulfillment.status = FulfillmentStatus.CANCELED
    fulfillment.save(update_fields=["status"])
    update_order_status(fulfillment.order)
    get_plugins_manager().order_updated(fulfillment.order)


@transaction.atomic
def mark_order_as_paid(order: "Order", request_user: "User"):
    """Mark order as paid.

    Allows to create a payment for an order without actually performing any
    payment by the gateway.
    """
    # pylint: disable=cyclic-import
    from ..payment.utils import create_payment

    payment = create_payment(
        gateway=CustomPaymentChoices.MANUAL,
        payment_token="",
        currency=order.total.gross.currency,
        email=order.user_email,
        total=order.total.gross.amount,
        order=order,
    )
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = order.total.gross.amount
    payment.save(update_fields=["captured_amount", "charge_status", "modified"])

    events.order_manually_marked_as_paid_event(order=order, user=request_user)
    manager = get_plugins_manager()
    manager.order_fully_paid(order)
    manager.order_updated(order)


def clean_mark_order_as_paid(order: "Order"):
    """Check if an order can be marked as paid."""
    if order.payments.exists():
        raise PaymentError("Orders with payments can not be manually marked as paid.",)


def fulfill_order_line(order_line, quantity):
    """Fulfill order line with given quantity."""
    country = get_order_country(order_line.order)
    if order_line.variant and order_line.variant.track_inventory:
        decrease_stock(order_line.variant, country, quantity)
    order_line.quantity_fulfilled += quantity
    order_line.save(update_fields=["quantity_fulfilled"])


def automatically_fulfill_digital_lines(order: "Order"):
    """Fulfill all digital lines which have enabled automatic fulfillment setting.

    Send confirmation email afterward.
    """
    digital_lines = order.lines.filter(
        is_shipping_required=False, variant__digital_content__isnull=False
    )
    digital_lines = digital_lines.prefetch_related("variant__digital_content")

    if not digital_lines:
        return
    fulfillment, _ = Fulfillment.objects.get_or_create(order=order)
    for line in digital_lines:
        if not order_line_needs_automatic_fulfillment(line):
            continue
        if line.variant:
            digital_content = line.variant.digital_content
            digital_content.urls.create(line=line)
        quantity = line.quantity
        FulfillmentLine.objects.create(
            fulfillment=fulfillment, order_line=line, quantity=quantity
        )
        fulfill_order_line(order_line=line, quantity=quantity)
    emails.send_fulfillment_confirmation_to_customer(
        order, fulfillment, user=order.user
    )
    update_order_status(order)

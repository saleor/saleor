import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, List

from django.db import transaction

from ..core import analytics
from ..core.exceptions import InsufficientStock
from ..payment import ChargeStatus, CustomPaymentChoices, PaymentError
from ..plugins.manager import get_plugins_manager
from ..warehouse.management import deallocate_stock_for_order, decrease_stock
from . import FulfillmentStatus, OrderStatus, emails, events, utils
from .emails import send_fulfillment_confirmation_to_customer, send_payment_confirmation
from .models import Fulfillment, FulfillmentLine
from .utils import (
    order_line_needs_automatic_fulfillment,
    recalculate_order,
    restock_fulfillment_lines,
    update_order_status,
)

if TYPE_CHECKING:
    from .models import Order
    from ..account.models import User
    from ..payment.models import Payment
    from ..warehouse.models import Warehouse


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


@transaction.atomic
def cancel_order(order: "Order", user: "User"):
    """Cancel order.

    Release allocation of unfulfilled order items.
    """

    events.order_canceled_event(order=order, user=user)

    deallocate_stock_for_order(order)
    order.status = OrderStatus.CANCELED
    order.save(update_fields=["status"])

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
    fulfillments: List["Fulfillment"],
    user: "User",
    fulfillment_lines: List["FulfillmentLine"],
    notify_customer=True,
):
    order = fulfillments[0].order
    update_order_status(order)
    events.fulfillment_fulfilled_items_event(
        order=order, user=user, fulfillment_lines=fulfillment_lines
    )
    manager = get_plugins_manager()
    manager.order_updated(order)

    for fulfillment in fulfillments:
        manager.fulfillment_created(fulfillment)

    if order.status == OrderStatus.FULFILLED:
        manager.order_fulfilled(order)

    if notify_customer:
        for fulfillment in fulfillments:
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


@transaction.atomic
def cancel_fulfillment(
    fulfillment: "Fulfillment", user: "User", warehouse: "Warehouse"
):
    """Cancel fulfillment.

    Return products to corresponding stocks.
    """
    fulfillment = Fulfillment.objects.select_for_update().get(pk=fulfillment.pk)
    restock_fulfillment_lines(fulfillment, warehouse)
    events.fulfillment_canceled_event(
        order=fulfillment.order, user=user, fulfillment=fulfillment
    )
    events.fulfillment_restocked_items_event(
        order=fulfillment.order,
        user=user,
        fulfillment=fulfillment,
        warehouse_pk=warehouse.pk,
    )
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


def fulfill_order_line(order_line, quantity, warehouse_pk):
    """Fulfill order line with given quantity."""
    if order_line.variant and order_line.variant.track_inventory:
        decrease_stock(order_line, quantity, warehouse_pk)
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
        warehouse_pk = line.allocations.first().stock.warehouse.pk  # type: ignore
        fulfill_order_line(
            order_line=line, quantity=quantity, warehouse_pk=warehouse_pk
        )
    emails.send_fulfillment_confirmation_to_customer(
        order, fulfillment, user=order.user
    )
    update_order_status(order)


def _create_fulfillment_lines(
    fulfillment: Fulfillment, warehouse_pk: str, lines: List[Dict]
) -> List[FulfillmentLine]:
    """Modify stocks and allocations. Return list of unsaved FulfillmentLines.

    Args:
        fulfillment (Fulfillment): Fulfillment to create lines
        warehouse_pk (str): Warehouse to fulfill order.
        lines (List[Dict]): List with information from which system
            create FulfillmentLines. Example:
                [
                    {
                        "order_line": (OrderLine),
                        "quantity": (int),
                    },
                    ...
                ]

    Return:
        List[FulfillmentLine]: Unsaved fulfillmet lines created for this fulfillment
            based on information form `lines`

    Raise:
        InsufficientStock: If system hasn't containt enough item in stock for any line.

    """
    fulfillment_lines = []
    for line in lines:
        quantity = line["quantity"]
        order_line = line["order_line"]
        if quantity > 0:
            stock = order_line.variant.stocks.filter(warehouse=warehouse_pk).first()
            if stock is None:
                error_context = {"order_line": order_line, "warehouse_pk": warehouse_pk}
                raise InsufficientStock(order_line.variant, error_context)
            fulfill_order_line(order_line, quantity, warehouse_pk)
            if order_line.is_digital:
                order_line.variant.digital_content.urls.create(line=order_line)
            fulfillment_lines.append(
                FulfillmentLine(
                    order_line=order_line,
                    fulfillment=fulfillment,
                    quantity=quantity,
                    stock=stock,
                )
            )
    return fulfillment_lines


@transaction.atomic()
def create_fulfillments(
    requester: "User",
    order: "Order",
    fulfillment_lines_for_warehouses: Dict,
    notify_customer: bool = True,
) -> List[Fulfillment]:
    """Fulfill order.

    Function create fulfillments with lines.
    Next updates Order based on created fulfillments.

    Args:
        requester (User): Requester who trigger this action.
        order (Order): Order to fulfill
        fulfillment_lines_for_warehouses (Dict): Dict with information from which
            system create fulfillments. Example:
                {
                    (Warehouse.pk): [
                        {
                            "order_line": (OrderLine),
                            "quantity": (int),
                        },
                        ...
                    ]
                }
        notify_customer (bool): If `True` system send email about
            fulfillments to customer.

    Return:
        List[Fulfillment]: Fulfillmet with lines created for this order
            based on information form `fulfillment_lines_for_warehouses`


    Raise:
        InsufficientStock: If system hasn't containt enough item in stock for any line.

    """
    fulfillments: List[Fulfillment] = []
    fulfillment_lines: List[FulfillmentLine] = []
    for warehouse_pk in fulfillment_lines_for_warehouses:
        fulfillment = Fulfillment.objects.create(order=order)
        fulfillments.append(fulfillment)
        fulfillment_lines.extend(
            _create_fulfillment_lines(
                fulfillment,
                warehouse_pk,
                fulfillment_lines_for_warehouses[warehouse_pk],
            )
        )

    FulfillmentLine.objects.bulk_create(fulfillment_lines)
    order_fulfilled(
        fulfillments, requester, fulfillment_lines, notify_customer,
    )
    return fulfillments

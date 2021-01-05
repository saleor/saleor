import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from django.contrib.sites.models import Site
from django.db import transaction

from ..core import analytics
from ..core.exceptions import AllocationError, InsufficientStock
from ..order.emails import send_order_confirmed
from ..payment import (
    ChargeStatus,
    CustomPaymentChoices,
    PaymentError,
    TransactionKind,
    gateway,
)
from ..payment.models import Payment, Transaction
from ..payment.utils import create_payment
from ..plugins.manager import get_plugins_manager
from ..warehouse.management import (
    deallocate_stock,
    deallocate_stock_for_order,
    decrease_stock,
)
from . import FulfillmentStatus, OrderStatus, emails, events, utils
from .emails import (
    send_fulfillment_confirmation_to_customer,
    send_order_canceled_confirmation,
    send_order_refunded_confirmation,
    send_payment_confirmation,
)
from .events import fulfillment_refunded_event
from .models import Fulfillment, FulfillmentLine, OrderLine
from .utils import (
    order_line_needs_automatic_fulfillment,
    recalculate_order,
    restock_fulfillment_lines,
    update_order_status,
)

if TYPE_CHECKING:
    from ..account.models import User
    from ..warehouse.models import Warehouse
    from .models import Order

logger = logging.getLogger(__name__)


def order_created(order: "Order", user: "User", from_draft: bool = False):
    events.order_created_event(order=order, user=user, from_draft=from_draft)
    manager = get_plugins_manager()
    manager.order_created(order)
    payment = order.get_last_payment()
    if payment:
        if order.is_captured():
            order_captured(
                order=order, user=user, amount=payment.total, payment=payment
            )
        elif order.is_pre_authorized():
            order_authorized(
                order=order, user=user, amount=payment.total, payment=payment
            )
    site_settings = Site.objects.get_current().settings
    if site_settings.automatically_confirm_all_new_orders:
        order_confirmed(order, user)


def order_confirmed(
    order: "Order", user: "User", send_confirmation_email: bool = False
):
    """Order confirmed.

    Trigger event, plugin hooks and optionally confirmation email.
    """
    events.order_confirmed_event(order=order, user=user)
    manager = get_plugins_manager()
    manager.order_confirmed(order)
    if send_confirmation_email:
        send_order_confirmed.delay(order.pk, user.pk)


def handle_fully_paid_order(order: "Order", user: Optional["User"] = None):
    events.order_fully_paid_event(order=order, user=user)

    if order.get_customer_email():
        events.email_sent_event(
            order=order, user=user, email_type=events.OrderEventsEmails.PAYMENT
        )
        send_payment_confirmation.delay(order.pk)

        if utils.order_needs_automatic_fulfillment(order):
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
def cancel_order(order: "Order", user: Optional["User"]):
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

    send_order_canceled_confirmation(order, user)


def order_refunded(
    order: "Order", user: Optional["User"], amount: "Decimal", payment: "Payment"
):
    events.payment_refunded_event(
        order=order, user=user, amount=amount, payment=payment
    )
    get_plugins_manager().order_updated(order)

    send_order_refunded_confirmation(order, user, amount, payment.currency)


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


def order_authorized(
    order: "Order", user: Optional["User"], amount: "Decimal", payment: "Payment"
):
    events.payment_authorized_event(
        order=order, user=user, amount=amount, payment=payment
    )
    get_plugins_manager().order_updated(order)


def order_captured(
    order: "Order", user: Optional["User"], amount: "Decimal", payment: "Payment"
):
    events.payment_captured_event(
        order=order, user=user, amount=amount, payment=payment
    )
    get_plugins_manager().order_updated(order)
    if order.is_fully_paid():
        handle_fully_paid_order(order, user)


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
def mark_order_as_paid(
    order: "Order", request_user: "User", external_reference: Optional[str] = None
):
    """Mark order as paid.

    Allows to create a payment for an order without actually performing any
    payment by the gateway.
    """

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

    Transaction.objects.create(
        payment=payment,
        action_required=False,
        kind=TransactionKind.EXTERNAL,
        token=external_reference or "",
        is_success=True,
        amount=order.total.gross.amount,
        currency=order.total.gross.currency,
        searchable_key=external_reference or "",
        gateway_response={},
    )
    events.order_manually_marked_as_paid_event(
        order=order, user=request_user, transaction_reference=external_reference
    )
    manager = get_plugins_manager()
    manager.order_fully_paid(order)
    manager.order_updated(order)


def clean_mark_order_as_paid(order: "Order"):
    """Check if an order can be marked as paid."""
    if order.payments.exists():
        raise PaymentError(
            "Orders with payments can not be manually marked as paid.",
        )


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
        fulfillments,
        requester,
        fulfillment_lines,
        notify_customer,
    )
    return fulfillments


def _get_fulfillment_line_if_exists(
    fulfillment_lines: List[FulfillmentLine], order_line_id, stock_id=None
):
    for line in fulfillment_lines:
        if line.order_line_id == order_line_id and line.stock_id == stock_id:
            return line
    return None


def _refund_fulfillment_for_order_lines(
    order_lines_to_refund: List[OrderLine],
    order_lines_quantities_to_refund: List[int],
    already_refunded_lines: List[FulfillmentLine],
    refunded_fulfillment: Fulfillment,
    all_refunded_lines: Dict[int, Tuple[int, OrderLine]],
):
    """Proceed the refund for unfulfilled order lines."""
    fulfillment_lines_to_create: List[FulfillmentLine] = []
    fulfillment_lines_to_update: List[FulfillmentLine] = []
    order_lines_to_update: List[OrderLine] = []
    refund_amount = Decimal(0)

    for line_to_refund, quantity_to_refund in zip(
        order_lines_to_refund, order_lines_quantities_to_refund
    ):
        # Check if refund line for order_line_id and stock_id does not exist in DB.
        refunded_line = _get_fulfillment_line_if_exists(
            already_refunded_lines, line_to_refund.id
        )
        fulfillment_line_existed = True
        if not refunded_line:
            # Create new not saved FulfillmentLine object and assign it to refund
            # fulfillment
            fulfillment_line_existed = False
            refunded_line = FulfillmentLine(
                fulfillment=refunded_fulfillment,
                order_line=line_to_refund,
                quantity=0,
            )

        # calculate the quantity fulfilled/unfulfilled/to refund
        unfulfilled_to_refund = min(
            line_to_refund.quantity_unfulfilled, quantity_to_refund
        )
        quantity_to_refund -= unfulfilled_to_refund
        line_to_refund.quantity_fulfilled += unfulfilled_to_refund
        refunded_line.quantity += unfulfilled_to_refund

        # update current lines with new value of quantity
        order_lines_to_update.append(line_to_refund)

        refund_amount += line_to_refund.unit_price_gross_amount * unfulfilled_to_refund
        if refunded_line.quantity > 0 and not fulfillment_line_existed:
            # If this is new type of (orderl_line, stock) then we create new fulfillment
            # line
            fulfillment_lines_to_create.append(refunded_line)
        elif fulfillment_line_existed:
            # if refund fulfillment already have the same line, we just update the
            # quantity
            fulfillment_lines_to_update.append(refunded_line)

        line_allocations_exists = line_to_refund.allocations.exists()
        if line_allocations_exists:
            try:
                deallocate_stock(line_to_refund, unfulfilled_to_refund)
            except AllocationError:
                logger.warning(
                    f"Unable to deallocate stock for line {line_to_refund.id}"
                )

        # prepare structure which will be used to create new order event.
        all_refunded_lines[line_to_refund.id] = (
            unfulfilled_to_refund,
            line_to_refund,
        )

    # update the fulfillment lines with new calues
    FulfillmentLine.objects.bulk_update(fulfillment_lines_to_update, ["quantity"])
    FulfillmentLine.objects.bulk_create(fulfillment_lines_to_create)
    OrderLine.objects.bulk_update(order_lines_to_update, ["quantity_fulfilled"])
    return refund_amount


def _refund_fulfillment_for_fulfillment_lines(
    fulfillment_lines_to_refund: List[FulfillmentLine],
    fulfillment_lines_quantities_to_refund: List[int],
    already_refunded_lines: List[FulfillmentLine],
    refunded_fulfillment: Fulfillment,
    all_refunded_lines: Dict[int, Tuple[int, OrderLine]],
):
    """Proceed the refund for fulfillment lines."""
    fulfillment_lines_to_create: List[FulfillmentLine] = []
    fulfillment_lines_to_update: List[FulfillmentLine] = []
    empty_fulfillment_lines_to_delete: List[FulfillmentLine] = []
    refund_amount = Decimal(0)

    # fetch order lines before for loop to save DB queries
    order_lines_with_fulfillment = OrderLine.objects.in_bulk(
        [line.order_line_id for line in fulfillment_lines_to_refund]
    )
    for fulfillment_line, quantity_to_refund in zip(
        fulfillment_lines_to_refund, fulfillment_lines_quantities_to_refund
    ):
        # Check if refund line for order_line_id and stock_id does not exist in DB.
        refunded_line = _get_fulfillment_line_if_exists(
            already_refunded_lines,
            fulfillment_line.order_line_id,
            fulfillment_line.stock_id,
        )
        fulfillment_line_existed = True
        if not refunded_line:
            # Create new not saved FulfillmentLine object and assign it to refund
            # fulfillment
            fulfillment_line_existed = False
            refunded_line = FulfillmentLine(
                fulfillment=refunded_fulfillment,
                order_line_id=fulfillment_line.order_line_id,
                stock_id=fulfillment_line.stock_id,
                quantity=0,
            )

        # calculate the quantity fulfilled/unfulfilled/to refund
        fulfilled_to_refund = min(fulfillment_line.quantity, quantity_to_refund)
        quantity_to_refund -= fulfilled_to_refund
        refunded_line.quantity += fulfilled_to_refund
        fulfillment_line.quantity -= fulfilled_to_refund

        order_line: OrderLine = order_lines_with_fulfillment.get(  # type: ignore
            fulfillment_line.order_line_id
        )
        refund_amount += order_line.unit_price_gross_amount * fulfilled_to_refund

        if fulfillment_line.quantity == 0:
            # the fulfillment line without any items will be deleted
            empty_fulfillment_lines_to_delete.append(fulfillment_line)
        else:
            # update with new quantity value
            fulfillment_lines_to_update.append(fulfillment_line)

        if refunded_line.quantity > 0 and not fulfillment_line_existed:
            # If this is new type of (orderl_line, stock) then we create new fulfillment
            # line
            fulfillment_lines_to_create.append(refunded_line)
        elif fulfillment_line_existed:
            # if refund fulfillment already have the same line, we  just update the
            # quantity
            fulfillment_lines_to_update.append(refunded_line)

        # check how many items we already refunded from unfulfilled lines for given
        # order_line.
        data_from_all_refunded_lines = all_refunded_lines.get(order_line.id)
        if data_from_all_refunded_lines:
            quantity, line = data_from_all_refunded_lines
            quantity += fulfilled_to_refund
            all_refunded_lines[order_line.id] = (quantity, line)
        else:
            all_refunded_lines[order_line.id] = (fulfilled_to_refund, order_line)

    # update the fulfillment lines with new calues
    FulfillmentLine.objects.bulk_update(fulfillment_lines_to_update, ["quantity"])
    FulfillmentLine.objects.bulk_create(fulfillment_lines_to_create)

    # Remove the empty fulfillment lines
    FulfillmentLine.objects.filter(
        id__in=[f.id for f in empty_fulfillment_lines_to_delete]
    ).delete()
    return refund_amount


def create_refund_fulfillment(
    requester: Optional["User"],
    order,
    payment,
    order_lines_to_refund: List[OrderLine],
    order_lines_quantities_to_refund: List[int],
    fulfillment_lines_to_refund: List[FulfillmentLine],
    fulfillment_lines_quantities_to_refund: List[int],
    amount=None,
    refund_shipping_costs=False,
):
    """Proceed with all steps required for refunding products.

    Calculate refunds for products based on the order's order lines and fulfillment
    lines.  The logic takes the list of order lines, fulfillment lines, and their
    quantities which is used to create the refund fulfillment. The stock for
    unfulfilled lines will be deallocated. It creates only single refund fulfillment
    for each order. Calling the method N-time will increase the quantity of the already
    refunded line. The refund fulfillment can have assigned lines with the same
    products but with the different stocks.
    """
    with transaction.atomic():
        refunded_fulfillment, _ = Fulfillment.objects.get_or_create(
            status=FulfillmentStatus.REFUNDED, order=order
        )
        already_refunded_lines = list(refunded_fulfillment.lines.all())
        all_refunded_lines: Dict[int, Tuple[int, OrderLine]] = dict()
        refund_order_lines = _refund_fulfillment_for_order_lines(
            order_lines_to_refund=order_lines_to_refund,
            order_lines_quantities_to_refund=order_lines_quantities_to_refund,
            already_refunded_lines=already_refunded_lines,
            refunded_fulfillment=refunded_fulfillment,
            all_refunded_lines=all_refunded_lines,
        )
        refund_fulfillment_lines = _refund_fulfillment_for_fulfillment_lines(
            fulfillment_lines_to_refund=fulfillment_lines_to_refund,
            fulfillment_lines_quantities_to_refund=(
                fulfillment_lines_quantities_to_refund
            ),
            already_refunded_lines=already_refunded_lines,
            refunded_fulfillment=refunded_fulfillment,
            all_refunded_lines=all_refunded_lines,
        )
        refund_amount = refund_order_lines + refund_fulfillment_lines

        Fulfillment.objects.filter(order=order, lines=None).delete()

    if amount is None:
        amount = refund_amount
        # we take into consideration the shipping costs only when amount is not
        # provided.
        if refund_shipping_costs:
            amount += order.shipping_price_gross_amount
    if amount:
        amount = min(payment.captured_amount, amount)
        gateway.refund(payment, amount)
        order_refunded(order, requester, amount, payment)

    fulfillment_refunded_event(
        order=order,
        user=requester,
        refunded_lines=list(all_refunded_lines.values()),
        amount=amount,
        shipping_costs_included=refund_shipping_costs,
    )
    return refunded_fulfillment

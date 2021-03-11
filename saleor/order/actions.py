import logging
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Tuple

from django.contrib.sites.models import Site
from django.db import transaction

from ..account.models import User
from ..core import analytics
from ..core.exceptions import AllocationError, InsufficientStock, InsufficientStockData
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
from ..plugins.manager import PluginsManager, get_plugins_manager
from ..warehouse.management import (
    deallocate_stock,
    deallocate_stock_for_order,
    decrease_stock,
    get_order_lines_with_track_inventory,
)
from ..warehouse.models import Stock
from . import (
    FulfillmentLineData,
    FulfillmentStatus,
    OrderLineData,
    OrderStatus,
    emails,
    events,
    utils,
)
from .emails import (
    send_fulfillment_confirmation_to_customer,
    send_order_canceled_confirmation,
    send_order_refunded_confirmation,
    send_payment_confirmation,
)
from .events import (
    draft_order_created_from_replace_event,
    fulfillment_refunded_event,
    fulfillment_replaced_event,
    order_replacement_created,
    order_returned_event,
)
from .models import Fulfillment, FulfillmentLine, Order, OrderLine
from .utils import (
    order_line_needs_automatic_fulfillment,
    recalculate_order,
    restock_fulfillment_lines,
    update_order_status,
)

if TYPE_CHECKING:
    from ..warehouse.models import Warehouse

logger = logging.getLogger(__name__)


OrderLineIDType = int
QuantityType = int


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
    order: "Order",
    user: Optional["User"],
    amount: "Decimal",
    payment: "Payment",
    manager: Optional["PluginsManager"] = None,
):
    events.payment_refunded_event(
        order=order, user=user, amount=amount, payment=payment
    )
    if not manager:
        manager = get_plugins_manager()
    manager.order_updated(order)

    send_order_refunded_confirmation(order, user, amount, payment.currency)


def order_voided(order: "Order", user: "User", payment: "Payment"):
    events.payment_voided_event(order=order, user=user, payment=payment)
    get_plugins_manager().order_updated(order)


def order_returned(
    order: "Order",
    user: Optional["User"],
    returned_lines: List[Tuple[QuantityType, OrderLine]],
    manager: "PluginsManager",
):
    order_returned_event(order=order, user=user, returned_lines=returned_lines)
    update_order_status(order)
    manager.order_updated(order)


@transaction.atomic
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


@transaction.atomic
def fulfill_order_lines(order_lines_info: Iterable["OrderLineData"]):
    """Fulfill order line with given quantity."""
    lines_to_decrease_stock = get_order_lines_with_track_inventory(order_lines_info)
    if lines_to_decrease_stock:
        decrease_stock(lines_to_decrease_stock)
    order_lines = []
    for line_info in order_lines_info:
        line = line_info.line
        line.quantity_fulfilled += line_info.quantity
        order_lines.append(line)

    OrderLine.objects.bulk_update(order_lines, ["quantity_fulfilled"])


@transaction.atomic
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

    fulfillments = []
    lines_info = []
    for line in digital_lines:
        if not order_line_needs_automatic_fulfillment(line):
            continue
        variant = line.variant
        if variant:
            digital_content = variant.digital_content
            digital_content.urls.create(line=line)
        quantity = line.quantity
        fulfillments.append(
            FulfillmentLine(fulfillment=fulfillment, order_line=line, quantity=quantity)
        )
        warehouse_pk = line.allocations.first().stock.warehouse.pk  # type: ignore
        lines_info.append(
            OrderLineData(
                line=line,
                quantity=quantity,
                variant=line.variant,
                warehouse_pk=warehouse_pk,
            )
        )

    FulfillmentLine.objects.bulk_create(fulfillments)
    fulfill_order_lines(lines_info)

    emails.send_fulfillment_confirmation_to_customer(
        order, fulfillment, user=order.user
    )
    update_order_status(order)


def _create_fulfillment_lines(
    fulfillment: Fulfillment, warehouse_pk: str, lines_data: List[Dict]
) -> List[FulfillmentLine]:
    """Modify stocks and allocations. Return list of unsaved FulfillmentLines.

    Args:
        fulfillment (Fulfillment): Fulfillment to create lines
        warehouse_pk (str): Warehouse to fulfill order.
        lines_data (List[Dict]): List with information from which system
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
    lines = [line_data["order_line"] for line_data in lines_data]
    variants = [line.variant for line in lines]
    stocks = Stock.objects.filter(
        warehouse_id=warehouse_pk, product_variant__in=variants
    ).select_related("product_variant")

    variant_to_stock: Dict[str, List[Stock]] = defaultdict(list)
    for stock in stocks:
        variant_to_stock[stock.product_variant_id].append(stock)

    insufficient_stocks = []
    fulfillment_lines = []
    lines_info = []
    for line in lines_data:
        quantity = line["quantity"]
        order_line = line["order_line"]
        if quantity > 0:
            line_stocks = variant_to_stock.get(order_line.variant_id)
            if line_stocks is None:
                error_data = InsufficientStockData(
                    variant=order_line.variant,
                    order_line=order_line,
                    warehouse_pk=warehouse_pk,
                )
                insufficient_stocks.append(error_data)
                continue
            stock = line_stocks[0]
            lines_info.append(
                OrderLineData(
                    line=order_line,
                    quantity=quantity,
                    variant=order_line.variant,
                    warehouse_pk=warehouse_pk,
                )
            )
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

    if insufficient_stocks:
        raise InsufficientStock(insufficient_stocks)

    if lines_info:
        fulfill_order_lines(lines_info)

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
    transaction.on_commit(
        lambda: order_fulfilled(
            fulfillments,
            requester,
            fulfillment_lines,
            notify_customer,
        )
    )
    return fulfillments


def _get_fulfillment_line_if_exists(
    fulfillment_lines: List[FulfillmentLine], order_line_id, stock_id=None
):
    for line in fulfillment_lines:
        if line.order_line_id == order_line_id and line.stock_id == stock_id:
            return line
    return None


def _get_fulfillment_line(
    target_fulfillment: Fulfillment,
    lines_in_target_fulfillment: List[FulfillmentLine],
    order_line_id: int,
    stock_id: Optional[int] = None,
) -> Tuple[FulfillmentLine, bool]:
    """Get fulfillment line if extists or create new fulfillment line object."""
    # Check if line for order_line_id and stock_id does not exist in DB.
    moved_line = _get_fulfillment_line_if_exists(
        lines_in_target_fulfillment,
        order_line_id,
        stock_id,
    )
    fulfillment_line_existed = True
    if not moved_line:
        # Create new not saved FulfillmentLine object and assign it to target
        # fulfillment
        fulfillment_line_existed = False
        moved_line = FulfillmentLine(
            fulfillment=target_fulfillment,
            order_line_id=order_line_id,
            stock_id=stock_id,
            quantity=0,
        )
    return moved_line, fulfillment_line_existed


@transaction.atomic()
def _move_order_lines_to_target_fulfillment(
    order_lines_to_move: List[OrderLineData],
    lines_in_target_fulfillment: List[FulfillmentLine],
    target_fulfillment: Fulfillment,
):
    """Move order lines with given quantity to the target fulfillment."""
    fulfillment_lines_to_create: List[FulfillmentLine] = []
    fulfillment_lines_to_update: List[FulfillmentLine] = []
    order_lines_to_update: List[OrderLine] = []

    lines_to_dellocate: List[OrderLineData] = []
    for line_data in order_lines_to_move:
        line_to_move = line_data.line
        quantity_to_move = line_data.quantity
        moved_line, fulfillment_line_existed = _get_fulfillment_line(
            target_fulfillment=target_fulfillment,
            lines_in_target_fulfillment=lines_in_target_fulfillment,
            order_line_id=line_to_move.id,
            stock_id=None,
        )

        # calculate the quantity fulfilled/unfulfilled to move
        unfulfilled_to_move = min(line_to_move.quantity_unfulfilled, quantity_to_move)
        quantity_to_move -= unfulfilled_to_move
        line_to_move.quantity_fulfilled += unfulfilled_to_move
        moved_line.quantity += unfulfilled_to_move

        # update current lines with new value of quantity
        order_lines_to_update.append(line_to_move)

        if moved_line.quantity > 0 and not fulfillment_line_existed:
            # If this is new type of (order_line, stock) then we create new fulfillment
            # line
            fulfillment_lines_to_create.append(moved_line)
        elif fulfillment_line_existed:
            # if target fulfillment already have the same line, we just update the
            # quantity
            fulfillment_lines_to_update.append(moved_line)

        line_allocations_exists = line_to_move.allocations.exists()
        if line_allocations_exists:
            lines_to_dellocate.append(
                OrderLineData(line=line_to_move, quantity=unfulfilled_to_move)
            )

    if lines_to_dellocate:
        try:
            deallocate_stock(lines_to_dellocate)
        except AllocationError as e:
            logger.warning(
                f"Unable to deallocate stock for line {', '.join(e.order_lines)}."
            )

    # update the fulfillment lines with new values
    FulfillmentLine.objects.bulk_update(fulfillment_lines_to_update, ["quantity"])
    FulfillmentLine.objects.bulk_create(fulfillment_lines_to_create)
    OrderLine.objects.bulk_update(order_lines_to_update, ["quantity_fulfilled"])


@transaction.atomic()
def _move_fulfillment_lines_to_target_fulfillment(
    fulfillment_lines_to_move: List[FulfillmentLineData],
    lines_in_target_fulfillment: List[FulfillmentLine],
    target_fulfillment: Fulfillment,
):
    """Move fulfillment lines with given quantity to the target fulfillment."""
    fulfillment_lines_to_create: List[FulfillmentLine] = []
    fulfillment_lines_to_update: List[FulfillmentLine] = []
    empty_fulfillment_lines_to_delete: List[FulfillmentLine] = []

    for fulfillment_line_data in fulfillment_lines_to_move:
        fulfillment_line = fulfillment_line_data.line
        quantity_to_move = fulfillment_line_data.quantity

        moved_line, fulfillment_line_existed = _get_fulfillment_line(
            target_fulfillment=target_fulfillment,
            lines_in_target_fulfillment=lines_in_target_fulfillment,
            order_line_id=fulfillment_line.order_line_id,
            stock_id=fulfillment_line.stock_id,
        )

        # calculate the quantity fulfilled/unfulfilled/to move
        fulfilled_to_move = min(fulfillment_line.quantity, quantity_to_move)
        quantity_to_move -= fulfilled_to_move
        moved_line.quantity += fulfilled_to_move
        fulfillment_line.quantity -= fulfilled_to_move

        if fulfillment_line.quantity == 0:
            # the fulfillment line without any items will be deleted
            empty_fulfillment_lines_to_delete.append(fulfillment_line)
        else:
            # update with new quantity value
            fulfillment_lines_to_update.append(fulfillment_line)

        if moved_line.quantity > 0 and not fulfillment_line_existed:
            # If this is new type of (order_line, stock) then we create new fulfillment
            # line
            fulfillment_lines_to_create.append(moved_line)
        elif fulfillment_line_existed:
            # if target fulfillment already have the same line, we  just update the
            # quantity
            fulfillment_lines_to_update.append(moved_line)

    # update the fulfillment lines with new values
    FulfillmentLine.objects.bulk_update(fulfillment_lines_to_update, ["quantity"])
    FulfillmentLine.objects.bulk_create(fulfillment_lines_to_create)

    # Remove the empty fulfillment lines
    FulfillmentLine.objects.filter(
        id__in=[f.id for f in empty_fulfillment_lines_to_delete]
    ).delete()


def create_refund_fulfillment(
    requester: Optional["User"],
    order,
    payment,
    order_lines_to_refund: List[OrderLineData],
    fulfillment_lines_to_refund: List[FulfillmentLineData],
    plugin_manager: "PluginsManager",
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

    _process_refund(
        requester=requester,
        order=order,
        payment=payment,
        order_lines_to_refund=order_lines_to_refund,
        fulfillment_lines_to_refund=fulfillment_lines_to_refund,
        amount=amount,
        refund_shipping_costs=refund_shipping_costs,
        manager=plugin_manager,
    )

    with transaction.atomic():
        refunded_fulfillment, _ = Fulfillment.objects.get_or_create(
            status=FulfillmentStatus.REFUNDED, order=order
        )
        already_refunded_lines = list(refunded_fulfillment.lines.all())
        _move_order_lines_to_target_fulfillment(
            order_lines_to_move=order_lines_to_refund,
            lines_in_target_fulfillment=already_refunded_lines,
            target_fulfillment=refunded_fulfillment,
        )
        _move_fulfillment_lines_to_target_fulfillment(
            fulfillment_lines_to_move=fulfillment_lines_to_refund,
            lines_in_target_fulfillment=already_refunded_lines,
            target_fulfillment=refunded_fulfillment,
        )

        Fulfillment.objects.filter(order=order, lines=None).delete()

    return refunded_fulfillment


def _populate_replace_order_fields(original_order: "Order"):
    replace_order = Order()
    replace_order.status = OrderStatus.DRAFT
    replace_order.user_id = original_order.user_id
    replace_order.language_code = original_order.language_code
    replace_order.user_email = original_order.user_email
    replace_order.currency = original_order.currency
    replace_order.channel = original_order.channel
    replace_order.display_gross_prices = original_order.display_gross_prices
    replace_order.redirect_url = original_order.redirect_url

    if original_order.billing_address:
        original_order.billing_address.pk = None
        replace_order.billing_address = original_order.billing_address
        replace_order.billing_address.save()
    if original_order.shipping_address:
        original_order.shipping_address.pk = None
        replace_order.shipping_address = original_order.shipping_address
        replace_order.shipping_address.save()
    replace_order.save()
    original_order.refresh_from_db()
    return replace_order


@transaction.atomic
def create_replace_order(
    requester: Optional["User"],
    original_order: "Order",
    order_lines_to_replace: List[OrderLineData],
    fulfillment_lines_to_replace: List[FulfillmentLineData],
) -> "Order":
    """Create draft order with lines to replace."""

    replace_order = _populate_replace_order_fields(original_order)
    order_line_to_create: Dict[OrderLineIDType, OrderLine] = dict()

    # iterate over lines without fulfillment to get the items for replace.
    # deepcopy to not lose the refence for lines assigned to original order
    for line_data in deepcopy(order_lines_to_replace):
        order_line = line_data.line
        order_line_id = order_line.pk
        order_line.pk = None
        order_line.order = replace_order
        order_line.quantity = line_data.quantity
        order_line.quantity_fulfilled = 0
        # we set order_line_id as a key to use it for iterating over fulfillment items
        order_line_to_create[order_line_id] = order_line

    order_lines_with_fulfillment = OrderLine.objects.in_bulk(
        [line_data.line.order_line_id for line_data in fulfillment_lines_to_replace]
    )
    for fulfillment_line_data in fulfillment_lines_to_replace:
        fulfillment_line = fulfillment_line_data.line
        order_line_id = fulfillment_line.order_line_id

        # if order_line_id exists in order_line_to_create, it means that we already have
        # prepared new order_line for this fulfillment. In that case we need to increase
        # quantity amount of new order_line by fulfillment_line.quantity
        if order_line_id in order_line_to_create:
            order_line_to_create[
                order_line_id
            ].quantity += fulfillment_line_data.quantity
            continue

        order_line_from_fulfillment = order_lines_with_fulfillment.get(order_line_id)
        order_line = order_line_from_fulfillment  # type: ignore
        order_line_id = order_line.pk
        order_line.pk = None
        order_line.order = replace_order
        order_line.quantity = fulfillment_line_data.quantity
        order_line.quantity_fulfilled = 0
        order_line_to_create[order_line_id] = order_line

    lines_to_create = order_line_to_create.values()
    OrderLine.objects.bulk_create(lines_to_create)

    recalculate_order(replace_order)

    draft_order_created_from_replace_event(
        draft_order=replace_order,
        original_order=original_order,
        user=requester,
        lines=[(line.quantity, line) for line in lines_to_create],
    )
    return replace_order


def _move_lines_to_return_fulfillment(
    order_lines: List[OrderLineData],
    fulfillment_lines: List[FulfillmentLineData],
    fulfillment_status: str,
    order: "Order",
) -> Fulfillment:
    target_fulfillment, _ = Fulfillment.objects.get_or_create(
        status=fulfillment_status, order=order
    )
    lines_in_target_fulfillment = list(target_fulfillment.lines.all())
    _move_order_lines_to_target_fulfillment(
        order_lines_to_move=order_lines,
        lines_in_target_fulfillment=lines_in_target_fulfillment,
        target_fulfillment=target_fulfillment,
    )

    fulfillment_lines_already_refunded = FulfillmentLine.objects.filter(
        fulfillment__order=order, fulfillment__status=FulfillmentStatus.REFUNDED
    ).values_list("id", flat=True)

    refunded_fulfillment_lines_to_return = []
    fulfillment_lines_to_return = []

    for line_data in fulfillment_lines:
        if line_data.line.id in fulfillment_lines_already_refunded:
            # item already refunded should be moved to fulfillment with status
            # REFUNDED_AND_RETURNED
            refunded_fulfillment_lines_to_return.append(line_data)
        else:
            # the rest of the items should be moved to target fulfillment
            fulfillment_lines_to_return.append(line_data)

    _move_fulfillment_lines_to_target_fulfillment(
        fulfillment_lines_to_move=fulfillment_lines_to_return,
        lines_in_target_fulfillment=lines_in_target_fulfillment,
        target_fulfillment=target_fulfillment,
    )

    if refunded_fulfillment_lines_to_return:
        refund_and_return_fulfillment, _ = Fulfillment.objects.get_or_create(
            status=FulfillmentStatus.REFUNDED_AND_RETURNED, order=order
        )
        lines_in_target_fulfillment = list(refund_and_return_fulfillment.lines.all())
        _move_fulfillment_lines_to_target_fulfillment(
            fulfillment_lines_to_move=refunded_fulfillment_lines_to_return,
            lines_in_target_fulfillment=lines_in_target_fulfillment,
            target_fulfillment=refund_and_return_fulfillment,
        )

    return target_fulfillment


def _move_lines_to_replace_fulfillment(
    order_lines_to_replace: List[OrderLineData],
    fulfillment_lines_to_replace: List[FulfillmentLineData],
    order: "Order",
) -> Fulfillment:
    target_fulfillment, _ = Fulfillment.objects.get_or_create(
        status=FulfillmentStatus.REPLACED, order=order
    )
    lines_in_target_fulfillment = list(target_fulfillment.lines.all())
    _move_order_lines_to_target_fulfillment(
        order_lines_to_move=order_lines_to_replace,
        lines_in_target_fulfillment=lines_in_target_fulfillment,
        target_fulfillment=target_fulfillment,
    )
    _move_fulfillment_lines_to_target_fulfillment(
        fulfillment_lines_to_move=fulfillment_lines_to_replace,
        lines_in_target_fulfillment=lines_in_target_fulfillment,
        target_fulfillment=target_fulfillment,
    )
    return target_fulfillment


@transaction.atomic
def create_return_fulfillment(
    requester: Optional["User"],
    order: "Order",
    order_lines: List[OrderLineData],
    fulfillment_lines: List[FulfillmentLineData],
    manager: "PluginsManager",
    refund: bool = False,
) -> Fulfillment:
    status = FulfillmentStatus.RETURNED
    if refund:
        status = FulfillmentStatus.REFUNDED_AND_RETURNED
    with transaction.atomic():
        return_fulfillment = _move_lines_to_return_fulfillment(
            order_lines=order_lines,
            fulfillment_lines=fulfillment_lines,
            fulfillment_status=status,
            order=order,
        )
        returned_lines: Dict[OrderLineIDType, Tuple[QuantityType, OrderLine]] = dict()
        order_lines_with_fulfillment = OrderLine.objects.in_bulk(
            [line_data.line.order_line_id for line_data in fulfillment_lines]
        )
        for line_data in order_lines:
            returned_lines[line_data.line.id] = (line_data.quantity, line_data.line)
        for line_data in fulfillment_lines:
            order_line = order_lines_with_fulfillment.get(line_data.line.order_line_id)
            returned_line = returned_lines.get(order_line.id)  # type: ignore
            if returned_line:
                quantity, line = returned_line
                quantity += line_data.quantity
                returned_lines[order_line.id] = (quantity, line)  # type: ignore
            else:
                returned_lines[order_line.id] = (  # type: ignore
                    line_data.quantity,
                    order_line,
                )
        returned_lines_list = list(returned_lines.values())
        transaction.on_commit(
            lambda: order_returned(
                order,
                user=requester,
                returned_lines=returned_lines_list,
                manager=manager,
            )
        )

    return return_fulfillment


@transaction.atomic
def process_replace(
    requester: Optional["User"],
    order: "Order",
    order_lines: List[OrderLineData],
    fulfillment_lines: List[FulfillmentLineData],
) -> Tuple[Fulfillment, Optional["Order"]]:
    """Create replace fulfillment and new draft order.

    Move all requested lines to fulfillment with status replaced. Based on original
    order create the draft order with all user details, and requested lines.
    """

    replace_fulfillment = _move_lines_to_replace_fulfillment(
        order_lines_to_replace=order_lines,
        fulfillment_lines_to_replace=fulfillment_lines,
        order=order,
    )
    new_order = create_replace_order(
        requester=requester,
        original_order=order,
        order_lines_to_replace=order_lines,
        fulfillment_lines_to_replace=fulfillment_lines,
    )
    replaced_lines = [(line.quantity, line) for line in new_order.lines.all()]
    fulfillment_replaced_event(
        order=order,
        user=requester,
        replaced_lines=replaced_lines,
    )
    order_replacement_created(
        original_order=order,
        replace_order=new_order,
        user=requester,
    )

    return replace_fulfillment, new_order


def create_fulfillments_for_returned_products(
    requester: Optional["User"],
    order: "Order",
    payment: Optional[Payment],
    order_lines: List[OrderLineData],
    fulfillment_lines: List[FulfillmentLineData],
    plugin_manager: PluginsManager,
    refund: bool = False,
    amount: Optional[Decimal] = None,
    refund_shipping_costs=False,
) -> Tuple[Fulfillment, Optional[Fulfillment], Optional[Order]]:
    """Process the request for replacing or returning the products.

    Process the refund when the refund is set to True. The amount of refund will be
    calculated for all lines with statuses different from refunded.  The lines which
    are set to replace will not be included in the refund amount.

    If the amount is provided, the refund will be used for this amount.

    If refund_shipping_costs is True, the calculated refund amount will include
    shipping costs.

    All lines with replace set to True will be used to create a new draft order, with
    the same order details as the original order.  These lines will be moved to
    fulfillment with status replaced. The events with relation to new order will be
    created.

    All lines with replace set to False will be moved to fulfillment with status
    returned/refunded_and_returned - depends on refund flag and current line status.
    If the fulfillment line has refunded status it will be moved to
    returned_and_refunded
    """
    return_order_lines = [data for data in order_lines if not data.replace]
    return_fulfillment_lines = [data for data in fulfillment_lines if not data.replace]
    if refund and payment:
        _process_refund(
            requester=requester,
            order=order,
            payment=payment,
            order_lines_to_refund=return_order_lines,
            fulfillment_lines_to_refund=return_fulfillment_lines,
            amount=amount,
            refund_shipping_costs=refund_shipping_costs,
            manager=plugin_manager,
        )

    with transaction.atomic():
        replace_order_lines = [data for data in order_lines if data.replace]
        replace_fulfillment_lines = [data for data in fulfillment_lines if data.replace]

        replace_fulfillment, new_order = None, None
        if replace_order_lines or replace_fulfillment_lines:
            replace_fulfillment, new_order = process_replace(
                requester=requester,
                order=order,
                order_lines=replace_order_lines,
                fulfillment_lines=replace_fulfillment_lines,
            )
        return_fulfillment = create_return_fulfillment(
            requester=requester,
            order=order,
            order_lines=return_order_lines,
            fulfillment_lines=return_fulfillment_lines,
            manager=plugin_manager,
            refund=refund,
        )
        Fulfillment.objects.filter(order=order, lines=None).delete()
    return return_fulfillment, replace_fulfillment, new_order


def _calculate_refund_amount(
    return_order_lines: List[OrderLineData],
    return_fulfillment_lines: List[FulfillmentLineData],
    lines_to_refund: Dict[OrderLineIDType, Tuple[QuantityType, OrderLine]],
) -> Decimal:
    refund_amount = Decimal(0)
    for line_data in return_order_lines:
        refund_amount += line_data.quantity * line_data.line.unit_price_gross_amount
        lines_to_refund[line_data.line.id] = (line_data.quantity, line_data.line)

    if not return_fulfillment_lines:
        return refund_amount

    order_lines_with_fulfillment = OrderLine.objects.in_bulk(
        [line_data.line.order_line_id for line_data in return_fulfillment_lines]
    )
    for line_data in return_fulfillment_lines:
        # skip lines which were already refunded
        if line_data.line.fulfillment.status == FulfillmentStatus.REFUNDED:
            continue
        order_line = order_lines_with_fulfillment[line_data.line.order_line_id]
        refund_amount += line_data.quantity * order_line.unit_price_gross_amount

        data_from_all_refunded_lines = lines_to_refund.get(order_line.id)
        if data_from_all_refunded_lines:
            quantity, line = data_from_all_refunded_lines
            quantity += line_data.quantity
            lines_to_refund[order_line.id] = (quantity, line)
        else:
            lines_to_refund[order_line.id] = (line_data.quantity, order_line)
    return refund_amount


def _process_refund(
    requester: Optional["User"],
    order: "Order",
    payment: Payment,
    order_lines_to_refund: List[OrderLineData],
    fulfillment_lines_to_refund: List[FulfillmentLineData],
    amount: Optional[Decimal],
    refund_shipping_costs: bool,
    manager: "PluginsManager",
):
    lines_to_refund: Dict[OrderLineIDType, Tuple[QuantityType, OrderLine]] = dict()
    refund_amount = _calculate_refund_amount(
        order_lines_to_refund, fulfillment_lines_to_refund, lines_to_refund
    )
    if amount is None:
        amount = refund_amount
        # we take into consideration the shipping costs only when amount is not
        # provided.
        if refund_shipping_costs:
            amount += order.shipping_price_gross_amount
    if amount:
        amount = min(payment.captured_amount, amount)
        gateway.refund(payment, amount)
        order_refunded(order, requester, amount, payment, manager=manager)

    fulfillment_refunded_event(
        order=order,
        user=requester,
        refunded_lines=list(lines_to_refund.values()),
        amount=amount,
        shipping_costs_included=refund_shipping_costs,
    )

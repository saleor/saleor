from decimal import Decimal
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

from ..account import events as account_events
from ..account.models import User
from ..app.models import App
from ..discount.models import OrderDiscount
from ..order.models import Fulfillment, FulfillmentLine, Order, OrderLine
from ..payment.models import Payment
from . import OrderEvents, OrderEventsEmails
from .models import OrderEvent

if TYPE_CHECKING:
    from uuid import UUID


def _line_per_quantity_to_line_object(quantity, line):
    return {"quantity": quantity, "line_pk": line.pk, "item": str(line)}


def _lines_per_quantity_to_line_object_list(order_lines):
    return [
        _line_per_quantity_to_line_object(line.quantity, line) for line in order_lines
    ]


def _get_payment_data(amount: Optional[Decimal], payment: Payment) -> Dict:
    return {
        "parameters": {
            "amount": amount,
            "payment_id": payment.token,
            "payment_gateway": payment.gateway,
        }
    }


def event_transaction_capture_requested(
    order_id: "UUID",
    reference: str,
    amount: Decimal,
    user: Optional[User],
    app: Optional[App],
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.TRANSACTION_CAPTURE_REQUESTED,
        user=user,
        app=app,
        parameters={
            "amount": amount,
            "reference": reference,
        },
    )


def event_transaction_refund_requested(
    order_id: "UUID",
    reference: str,
    amount: Decimal,
    user: Optional[User],
    app: Optional[App],
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.TRANSACTION_REFUND_REQUESTED,
        user=user,
        app=app,
        parameters={
            "amount": amount,
            "reference": reference,
        },
    )


def event_transaction_void_requested(
    order_id: "UUID", reference: str, user: Optional[User], app: Optional[App]
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.TRANSACTION_VOID_REQUESTED,
        user=user,
        app=app,
        parameters={
            "reference": reference,
        },
    )


def event_order_refunded_notification(
    order_id: "UUID", user_id: Optional[int], app_id: Optional[int], customer_email: str
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.EMAIL_SENT,
        parameters={
            "email": customer_email,
            "email_type": OrderEventsEmails.ORDER_REFUND,
        },
        user_id=user_id,
        app_id=app_id,
    )


def event_order_confirmed_notification(
    order_id: "UUID", user_id: Optional[int], app_id: Optional[int], customer_email: str
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.EMAIL_SENT,
        parameters={
            "email": customer_email,
            "email_type": OrderEventsEmails.CONFIRMED,
        },
        user_id=user_id,
        app_id=app_id,
    )


def event_order_cancelled_notification(
    order_id: "UUID", user_id: Optional[int], app_id: Optional[int], customer_email: str
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.EMAIL_SENT,
        parameters={
            "email": customer_email,
            "email_type": OrderEventsEmails.ORDER_CANCEL,
        },
        user_id=user_id,
        app_id=app_id,
    )


def event_order_confirmation_notification(
    order_id: "UUID", user_id: Optional[int], customer_email: str
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.EMAIL_SENT,
        parameters={
            "email": customer_email,
            "email_type": OrderEventsEmails.ORDER_CONFIRMATION,
        },
        user_id=user_id,
    )


def event_fulfillment_confirmed_notification(
    order_id: "UUID", user_id: Optional[int], app_id: Optional[int], customer_email: str
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.EMAIL_SENT,
        parameters={
            "email": customer_email,
            "email_type": OrderEventsEmails.FULFILLMENT,
        },
        user_id=user_id,
        app_id=app_id,
    )


def event_fulfillment_digital_links_notification(
    order_id: "UUID", user_id: Optional[int], app_id: Optional[int], customer_email: str
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.EMAIL_SENT,
        parameters={
            "email": customer_email,
            "email_type": OrderEventsEmails.DIGITAL_LINKS,
        },
        user_id=user_id,
        app_id=app_id,
    )


def event_payment_confirmed_notification(
    order_id: "UUID", user_id: Optional[int], customer_email: str
):
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.EMAIL_SENT,
        parameters={"email": customer_email, "email_type": OrderEventsEmails.PAYMENT},
        user_id=user_id,
    )


def invoice_requested_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order, app=app, type=OrderEvents.INVOICE_REQUESTED, user=user
    )


def invoice_generated_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    invoice_number: str,
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.INVOICE_GENERATED,
        user=user,
        app=app,
        parameters={"invoice_number": invoice_number},
    )


def invoice_updated_event(
    *,
    order: Order,
    user: Optional[Optional[User]],
    app: Optional[App],
    invoice_number: str,
    url: str,
    status: str
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.INVOICE_UPDATED,
        user=user,
        app=app,
        parameters={"invoice_number": invoice_number, "url": url, "status": status},
    )


def event_invoice_sent_notification(
    *, order_id: "UUID", user_id: Optional[int], app_id: Optional[int], email: str
) -> OrderEvent:
    return OrderEvent.objects.create(
        order_id=order_id,
        type=OrderEvents.INVOICE_SENT,
        user_id=user_id,
        app_id=app_id,
        parameters={"email": email},
    )


def email_resent_event(
    *, order: Order, user: Optional[User], email_type: OrderEventsEmails
) -> OrderEvent:
    raise NotImplementedError


def draft_order_created_event(
    *, order: Order, user: Optional[User], app: Optional[App]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order, type=OrderEvents.DRAFT_CREATED, user=user, app=app
    )


def order_added_products_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    order_lines: List[OrderLine],
    quantity_diff: Optional[int] = None
) -> OrderEvent:
    if quantity_diff:
        lines = [_line_per_quantity_to_line_object(quantity_diff, order_lines[0])]
    else:
        lines = _lines_per_quantity_to_line_object_list(order_lines)

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.ADDED_PRODUCTS,
        user=user,
        app=app,
        parameters={"lines": lines},
    )


def order_removed_products_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    order_lines: List[OrderLine],
    quantity_diff: Optional[int] = None
) -> OrderEvent:
    if quantity_diff:
        lines = [_line_per_quantity_to_line_object(quantity_diff, order_lines[0])]
    else:
        lines = _lines_per_quantity_to_line_object_list(order_lines)

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.REMOVED_PRODUCTS,
        user=user,
        app=app,
        parameters={"lines": lines},
    )


def draft_order_created_from_replace_event(
    *,
    draft_order: Order,
    original_order: Order,
    user: Optional[User],
    app: Optional[App],
    lines: List[OrderLine]
):
    parameters = {
        "related_order_pk": original_order.pk,
        "lines": _lines_per_quantity_to_line_object_list(lines),
    }
    return OrderEvent.objects.create(
        order=draft_order,
        type=OrderEvents.DRAFT_CREATED_FROM_REPLACE,
        user=user,
        app=app,
        parameters=parameters,
    )


def order_created_event(
    *, order: Order, user: Optional[User], app: Optional[App], from_draft=False
) -> OrderEvent:
    if from_draft:
        event_type = OrderEvents.PLACED_FROM_DRAFT
    else:
        event_type = OrderEvents.PLACED
        if user:
            account_events.customer_placed_order_event(
                user=user,
                order=order,
            )

    return OrderEvent.objects.create(order=order, type=event_type, user=user, app=app)


def order_confirmed_event(
    *, order: Order, user: Optional[User], app: Optional[App]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order, type=OrderEvents.CONFIRMED, user=user, app=app
    )


def order_canceled_event(
    *, order: Order, user: Optional[User], app: Optional[App]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order, type=OrderEvents.CANCELED, user=user, app=app
    )


def order_manually_marked_as_paid_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    transaction_reference: Optional[str] = None
) -> OrderEvent:
    parameters = {}
    if transaction_reference:
        parameters = {"transaction_reference": transaction_reference}
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.ORDER_MARKED_AS_PAID,
        user=user,
        app=app,
        parameters=parameters,
    )


def order_fully_paid_event(
    *, order: Order, user: Optional[User], app: Optional[App]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order, type=OrderEvents.ORDER_FULLY_PAID, user=user, app=app
    )


def order_replacement_created(
    *,
    original_order: Order,
    replace_order: Order,
    user: Optional[User],
    app: Optional[App]
) -> OrderEvent:
    parameters = {"related_order_pk": replace_order.pk}
    return OrderEvent.objects.create(
        order=original_order,
        type=OrderEvents.ORDER_REPLACEMENT_CREATED,
        user=user,
        app=app,
        parameters=parameters,
    )


def payment_authorized_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    amount: Decimal,
    payment: Payment
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_AUTHORIZED,
        user=user,
        app=app,
        **_get_payment_data(amount, payment),
    )


def payment_captured_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    amount: Decimal,
    payment: Payment
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_CAPTURED,
        user=user,
        app=app,
        **_get_payment_data(amount, payment),
    )


def payment_refunded_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    amount: Decimal,
    payment: Payment
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_REFUNDED,
        user=user,
        app=app,
        **_get_payment_data(amount, payment),
    )


def payment_voided_event(
    *, order: Order, user: Optional[User], app: Optional[App], payment: Payment
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_VOIDED,
        user=user,
        app=app,
        **_get_payment_data(None, payment),
    )


def payment_failed_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    message: str,
    payment: Payment
) -> OrderEvent:
    parameters = {"message": message}

    if payment:
        parameters.update({"gateway": payment.gateway, "payment_id": payment.token})

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_FAILED,
        user=user,
        app=app,
        parameters=parameters,
    )


def transaction_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    reference: str,
    status: str,
    name: str
) -> OrderEvent:
    parameters = {"message": name, "reference": reference, "status": status}
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.TRANSACTION_EVENT,
        user=user,
        app=app,
        parameters=parameters,
    )


def external_notification_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    message: Optional[str],
    parameters: Optional[dict]
) -> OrderEvent:
    parameters = parameters or {}
    parameters["message"] = message

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.EXTERNAL_SERVICE_NOTIFICATION,
        user=user,
        app=app,
        parameters=parameters,
    )


def fulfillment_canceled_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    fulfillment: Optional[Fulfillment]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_CANCELED,
        user=user,
        app=app,
        parameters={"composed_id": fulfillment.composed_id} if fulfillment else {},
    )


def fulfillment_restocked_items_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    fulfillment: Union[Order, Fulfillment],
    warehouse_pk: Optional["UUID"] = None,
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS,
        user=user,
        app=app,
        parameters={
            "quantity": fulfillment.get_total_quantity(),
            "warehouse": warehouse_pk,
        },
    )


def fulfillment_fulfilled_items_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    fulfillment_lines: List[FulfillmentLine]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_FULFILLED_ITEMS,
        user=user,
        app=app,
        parameters={"fulfilled_items": [line.pk for line in fulfillment_lines]},
    )


def fulfillment_awaits_approval_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    fulfillment_lines: List[FulfillmentLine]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_AWAITS_APPROVAL,
        user=user,
        app=app,
        parameters={"awaiting_fulfillments": [line.pk for line in fulfillment_lines]},
    )


def order_returned_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    returned_lines: List[Tuple[int, OrderLine]],
):
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_RETURNED,
        user=user,
        app=app,
        parameters={
            "lines": [
                _line_per_quantity_to_line_object(quantity, line)
                for quantity, line in returned_lines
            ]
        },
    )


def fulfillment_replaced_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    replaced_lines: List[OrderLine],
):
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_REPLACED,
        user=user,
        app=app,
        parameters={"lines": _lines_per_quantity_to_line_object_list(replaced_lines)},
    )


def fulfillment_refunded_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    refunded_lines: List[Tuple[int, OrderLine]],
    amount: Decimal,
    shipping_costs_included: bool
):
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_REFUNDED,
        user=user,
        app=app,
        parameters={
            "lines": [
                _line_per_quantity_to_line_object(quantity, line)
                for quantity, line in refunded_lines
            ],
            "amount": amount,
            "shipping_costs_included": shipping_costs_included,
        },
    )


def fulfillment_tracking_updated_event(
    *,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    tracking_number: str,
    fulfillment: Fulfillment
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.TRACKING_UPDATED,
        user=user,
        app=app,
        parameters={
            "tracking_number": tracking_number,
            "fulfillment": fulfillment.composed_id,
        },
    )


def order_note_added_event(
    *, order: Order, user: Optional[User], app: Optional[App], message: str
) -> OrderEvent:
    kwargs: Dict[str, Union[Optional[App], Optional[User]]] = {"app": app}
    if user is not None:
        if order.user is not None and order.user.pk == user.pk:
            account_events.customer_added_to_note_order_event(
                user=user, order=order, message=message
            )
        kwargs["user"] = user

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.NOTE_ADDED,
        parameters={"message": message},
        **kwargs,
    )


def _prepare_discount_object(
    order_discount: "OrderDiscount",
    old_order_discount: Optional["OrderDiscount"] = None,
):
    discount_parameters = {
        "value": order_discount.value,
        "amount_value": order_discount.amount_value,
        "currency": order_discount.currency,
        "value_type": order_discount.value_type,
        "reason": order_discount.reason,
    }
    if old_order_discount:
        discount_parameters["old_value"] = old_order_discount.value
        discount_parameters["old_value_type"] = old_order_discount.value_type
        discount_parameters["old_amount_value"] = old_order_discount.amount_value
    return discount_parameters


def order_discount_event(
    *,
    event_type: str,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    order_discount: "OrderDiscount",
    old_order_discount: Optional["OrderDiscount"] = None
) -> OrderEvent:
    discount_parameters = _prepare_discount_object(order_discount, old_order_discount)

    return OrderEvent.objects.create(
        order=order,
        type=event_type,
        user=user,
        app=app,
        parameters={"discount": discount_parameters},
    )


def order_discounts_automatically_updated_event(
    order: Order, changed_order_discounts: List[Tuple["OrderDiscount", "OrderDiscount"]]
):
    for previous_order_discount, current_order_discount in changed_order_discounts:
        order_discount_automatically_updated_event(
            order=order,
            order_discount=current_order_discount,
            old_order_discount=previous_order_discount,
        )


def order_discount_automatically_updated_event(
    order: Order, order_discount: "OrderDiscount", old_order_discount: "OrderDiscount"
):
    return order_discount_event(
        event_type=OrderEvents.ORDER_DISCOUNT_AUTOMATICALLY_UPDATED,
        order=order,
        user=None,
        app=None,
        order_discount=order_discount,
        old_order_discount=old_order_discount,
    )


def order_discount_added_event(
    order: Order,
    user: Optional[User],
    app: Optional[App],
    order_discount: "OrderDiscount",
) -> OrderEvent:
    return order_discount_event(
        event_type=OrderEvents.ORDER_DISCOUNT_ADDED,
        order=order,
        user=user,
        app=app,
        order_discount=order_discount,
    )


def order_discount_updated_event(
    order: Order,
    user: Optional[User],
    app: Optional[App],
    order_discount: "OrderDiscount",
    old_order_discount: Optional["OrderDiscount"] = None,
) -> OrderEvent:
    return order_discount_event(
        event_type=OrderEvents.ORDER_DISCOUNT_UPDATED,
        order=order,
        user=user,
        app=app,
        order_discount=order_discount,
        old_order_discount=old_order_discount,
    )


def order_discount_deleted_event(
    order: Order,
    user: Optional[User],
    app: Optional[App],
    order_discount: "OrderDiscount",
) -> OrderEvent:
    return order_discount_event(
        event_type=OrderEvents.ORDER_DISCOUNT_DELETED,
        order=order,
        user=user,
        app=app,
        order_discount=order_discount,
    )


def order_line_discount_event(
    *,
    event_type: str,
    order: Order,
    user: Optional[User],
    app: Optional[App],
    line: OrderLine,
    line_before_update: Optional["OrderLine"] = None
) -> OrderEvent:
    discount_parameters = {
        "value": line.unit_discount_value,
        "amount_value": line.unit_discount_amount,
        "currency": line.currency,
        "value_type": line.unit_discount_type,
        "reason": line.unit_discount_reason,
    }
    if line_before_update:
        discount_parameters["old_value"] = line_before_update.unit_discount_value
        discount_parameters["old_value_type"] = line_before_update.unit_discount_type
        discount_parameters[
            "old_amount_value"
        ] = line_before_update.unit_discount_amount

    line_data = _line_per_quantity_to_line_object(line.quantity, line)
    line_data["discount"] = discount_parameters
    return OrderEvent.objects.create(
        order=order,
        type=event_type,
        user=user,
        app=app,
        parameters={"lines": [line_data]},
    )


def order_line_discount_updated_event(
    order: Order,
    user: Optional[User],
    app: Optional[App],
    line: OrderLine,
    line_before_update: Optional["OrderLine"] = None,
) -> OrderEvent:
    return order_line_discount_event(
        event_type=OrderEvents.ORDER_LINE_DISCOUNT_UPDATED,
        order=order,
        line=line,
        line_before_update=line_before_update,
        user=user,
        app=app,
    )


def order_line_discount_removed_event(
    order: Order,
    user: Optional[User],
    app: Optional[App],
    line: OrderLine,
) -> OrderEvent:
    return order_line_discount_event(
        event_type=OrderEvents.ORDER_LINE_DISCOUNT_REMOVED,
        order=order,
        line=line,
        user=user,
        app=app,
    )


def order_line_product_removed_event(
    order: Order,
    user: Optional[User],
    app: Optional[App],
    order_lines: List[Tuple[int, OrderLine]],
):
    return OrderEvent.objects.create(
        type=OrderEvents.ORDER_LINE_PRODUCT_DELETED,
        order=order,
        user=user,
        app=app,
        parameters={"lines": _lines_per_quantity_to_line_object_list(order_lines)},
    )


def order_line_variant_removed_event(
    order: Order,
    user: Optional[User],
    app: Optional[App],
    order_lines: List[Tuple[int, OrderLine]],
):
    return OrderEvent.objects.create(
        type=OrderEvents.ORDER_LINE_VARIANT_DELETED,
        order=order,
        user=user,
        app=app,
        parameters={"lines": _lines_per_quantity_to_line_object_list(order_lines)},
    )

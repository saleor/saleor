from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union

from ..account import events as account_events
from ..account.models import User
from ..discount.models import OrderDiscount
from ..order.models import Fulfillment, FulfillmentLine, Order, OrderLine
from ..payment.models import Payment
from . import OrderEvents, OrderEventsEmails
from .models import OrderEvent

UserType = Optional[User]


def _line_per_quantity_to_line_object(quantity, line):
    return {"quantity": quantity, "line_pk": line.pk, "item": str(line)}


def _lines_per_quantity_to_line_object_list(quantities_per_order_line):
    return [
        _line_per_quantity_to_line_object(quantity, line)
        for quantity, line in quantities_per_order_line
    ]


def _get_payment_data(amount: Optional[Decimal], payment: Payment) -> Dict:
    return {
        "parameters": {
            "amount": amount,
            "payment_id": payment.token,
            "payment_gateway": payment.gateway,
        }
    }


def _user_is_valid(user: UserType) -> bool:
    return bool(user and not user.is_anonymous)


def email_sent_event(
    *,
    order: Order,
    user: Optional[UserType],
    email_type: str,  # use "OrderEventsEmails" class
    user_pk: int = None,
) -> OrderEvent:

    if user and not user.is_anonymous:
        kwargs: Dict[str, Union[User, int]] = {"user": user}
    elif user_pk:
        kwargs = {"user_id": user_pk}
    else:
        kwargs = {}

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.EMAIL_SENT,
        parameters={"email": order.get_customer_email(), "email_type": email_type},
        **kwargs,
    )


def invoice_requested_event(
    *,
    order: Order,
    user: Optional[UserType],
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order, type=OrderEvents.INVOICE_REQUESTED, user=user
    )


def invoice_generated_event(
    *,
    order: Order,
    user: Optional[UserType],
    invoice_number: str,
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.INVOICE_GENERATED,
        user=user,
        parameters={"invoice_number": invoice_number},
    )


def invoice_updated_event(
    *,
    order: Order,
    user: Optional[UserType],
    invoice_number: str,
    url: str,
    status: str
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.INVOICE_UPDATED,
        user=user,
        parameters={"invoice_number": invoice_number, "url": url, "status": status},
    )


def invoice_sent_event(
    *,
    order: Order,
    user: Optional[UserType],
    email: str,
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.INVOICE_SENT,
        user=user,
        parameters={"email": email},
    )


def email_resent_event(
    *, order: Order, user: UserType, email_type: OrderEventsEmails
) -> OrderEvent:
    raise NotImplementedError


def draft_order_created_event(*, order: Order, user: UserType) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order, type=OrderEvents.DRAFT_CREATED, user=user
    )


def draft_order_added_products_event(
    *, order: Order, user: UserType, order_lines: List[Tuple[int, OrderLine]]
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.DRAFT_ADDED_PRODUCTS,
        user=user,
        parameters={"lines": _lines_per_quantity_to_line_object_list(order_lines)},
    )


def draft_order_removed_products_event(
    *, order: Order, user: UserType, order_lines: List[Tuple[int, OrderLine]]
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.DRAFT_REMOVED_PRODUCTS,
        user=user,
        parameters={"lines": _lines_per_quantity_to_line_object_list(order_lines)},
    )


def draft_order_created_from_replace_event(
    *,
    draft_order: Order,
    original_order: Order,
    user: UserType,
    lines: List[Tuple[int, OrderLine]]
):
    if not _user_is_valid(user):
        user = None
    parameters = {
        "related_order_pk": original_order.pk,
        "lines": _lines_per_quantity_to_line_object_list(lines),
    }
    return OrderEvent.objects.create(
        order=draft_order,
        type=OrderEvents.DRAFT_CREATED_FROM_REPLACE,
        user=user,
        parameters=parameters,
    )


def order_created_event(
    *, order: Order, user: UserType, from_draft=False
) -> OrderEvent:
    if from_draft:
        event_type = OrderEvents.PLACED_FROM_DRAFT
    else:
        event_type = OrderEvents.PLACED
        account_events.customer_placed_order_event(
            user=user,  # type: ignore
            order=order,
        )

    if not _user_is_valid(user):
        user = None

    return OrderEvent.objects.create(order=order, type=event_type, user=user)


def order_confirmed_event(
    *, order: Order, user: UserType, from_draft=False
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(order=order, type=OrderEvents.CONFIRMED, user=user)


def draft_order_oversold_items_event(
    *, order: Order, user: UserType, oversold_items: List[str]
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.OVERSOLD_ITEMS,
        user=user,
        parameters={"oversold_items": oversold_items},
    )


def order_canceled_event(*, order: Order, user: UserType) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(order=order, type=OrderEvents.CANCELED, user=user)


def order_manually_marked_as_paid_event(
    *, order: Order, user: UserType, transaction_reference: Optional[str] = None
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    parameters = {}  # type: ignore
    if transaction_reference:
        parameters = {"transaction_reference": transaction_reference}
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.ORDER_MARKED_AS_PAID,
        user=user,
        parameters=parameters,
    )


def order_fully_paid_event(*, order: Order, user: UserType) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order, type=OrderEvents.ORDER_FULLY_PAID, user=user
    )


def order_replacement_created(
    *, original_order: Order, replace_order: Order, user: UserType
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    parameters = {"related_order_pk": replace_order.pk}
    return OrderEvent.objects.create(
        order=original_order,
        type=OrderEvents.ORDER_REPLACEMENT_CREATED,
        user=user,
        parameters=parameters,
    )


def payment_authorized_event(
    *, order: Order, user: UserType, amount: Decimal, payment: Payment
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_AUTHORIZED,
        user=user,
        **_get_payment_data(amount, payment),
    )


def payment_captured_event(
    *, order: Order, user: UserType, amount: Decimal, payment: Payment
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_CAPTURED,
        user=user,
        **_get_payment_data(amount, payment),
    )


def payment_refunded_event(
    *, order: Order, user: UserType, amount: Decimal, payment: Payment
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_REFUNDED,
        user=user,
        **_get_payment_data(amount, payment),
    )


def payment_voided_event(
    *, order: Order, user: UserType, payment: Payment
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_VOIDED,
        user=user,
        **_get_payment_data(None, payment),
    )


def payment_failed_event(
    *, order: Order, user: UserType, message: str, payment: Payment
) -> OrderEvent:

    if not _user_is_valid(user):
        user = None
    parameters = {"message": message}

    if payment:
        parameters.update({"gateway": payment.gateway, "payment_id": payment.token})

    return OrderEvent.objects.create(
        order=order, type=OrderEvents.PAYMENT_FAILED, user=user, parameters=parameters
    )


def external_notification_event(
    *, order: Order, user: UserType, message: Optional[str], parameters: Optional[dict]
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    parameters = parameters or {}
    parameters["message"] = message

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.EXTERNAL_SERVICE_NOTIFICATION,
        user=user,
        parameters=parameters,
    )


def fulfillment_canceled_event(
    *, order: Order, user: UserType, fulfillment: Fulfillment
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_CANCELED,
        user=user,
        parameters={"composed_id": fulfillment.composed_id},
    )


def fulfillment_restocked_items_event(
    *,
    order: Order,
    user: UserType,
    fulfillment: Union[Order, Fulfillment],
    warehouse_pk: Optional[int] = None,
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS,
        user=user,
        parameters={
            "quantity": fulfillment.get_total_quantity(),
            "warehouse": warehouse_pk,
        },
    )


def fulfillment_fulfilled_items_event(
    *, order: Order, user: UserType, fulfillment_lines: List[FulfillmentLine]
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_FULFILLED_ITEMS,
        user=user,
        parameters={"fulfilled_items": [line.pk for line in fulfillment_lines]},
    )


def order_returned_event(
    *,
    order: Order,
    user: UserType,
    returned_lines: List[Tuple[int, OrderLine]],
):
    if not _user_is_valid(user):
        user = None

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_RETURNED,
        user=user,
        parameters={"lines": _lines_per_quantity_to_line_object_list(returned_lines)},
    )


def fulfillment_replaced_event(
    *,
    order: Order,
    user: UserType,
    replaced_lines: List[Tuple[int, OrderLine]],
):
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_REPLACED,
        user=user,
        parameters={"lines": _lines_per_quantity_to_line_object_list(replaced_lines)},
    )


def fulfillment_refunded_event(
    *,
    order: Order,
    user: UserType,
    refunded_lines: List[Tuple[int, OrderLine]],
    amount: Decimal,
    shipping_costs_included: bool
):
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_REFUNDED,
        user=user,
        parameters={
            "lines": _lines_per_quantity_to_line_object_list(refunded_lines),
            "amount": amount,
            "shipping_costs_included": shipping_costs_included,
        },
    )


def fulfillment_tracking_updated_event(
    *, order: Order, user: UserType, tracking_number: str, fulfillment: Fulfillment
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.TRACKING_UPDATED,
        user=user,
        parameters={
            "tracking_number": tracking_number,
            "fulfillment": fulfillment.composed_id,
        },
    )


def order_note_added_event(*, order: Order, user: UserType, message: str) -> OrderEvent:
    kwargs = {}
    if user is not None and not user.is_anonymous:
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
    user: UserType,
    order_discount: "OrderDiscount",
    old_order_discount: Optional["OrderDiscount"] = None
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
    discount_parameters = _prepare_discount_object(order_discount, old_order_discount)

    return OrderEvent.objects.create(
        order=order,
        type=event_type,
        user=user,
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
        order_discount=order_discount,
        old_order_discount=old_order_discount,
    )


def order_discount_added_event(
    order: Order, user: UserType, order_discount: "OrderDiscount"
) -> OrderEvent:
    return order_discount_event(
        event_type=OrderEvents.ORDER_DISCOUNT_ADDED,
        order=order,
        user=user,
        order_discount=order_discount,
    )


def order_discount_updated_event(
    order: Order,
    user: UserType,
    order_discount: "OrderDiscount",
    old_order_discount: Optional["OrderDiscount"] = None,
) -> OrderEvent:
    return order_discount_event(
        event_type=OrderEvents.ORDER_DISCOUNT_UPDATED,
        order=order,
        user=user,
        order_discount=order_discount,
        old_order_discount=old_order_discount,
    )


def order_discount_deleted_event(
    order: Order,
    user: UserType,
    order_discount: "OrderDiscount",
) -> OrderEvent:
    return order_discount_event(
        event_type=OrderEvents.ORDER_DISCOUNT_DELETED,
        order=order,
        user=user,
        order_discount=order_discount,
    )


def order_line_discount_event(
    *,
    event_type: str,
    order: Order,
    user: UserType,
    line: OrderLine,
    line_before_update: Optional["OrderLine"] = None
) -> OrderEvent:
    if not _user_is_valid(user):
        user = None
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
        parameters={"lines": [line_data]},
    )


def order_line_discount_updated_event(
    order: Order,
    user: UserType,
    line: OrderLine,
    line_before_update: Optional["OrderLine"] = None,
) -> OrderEvent:
    return order_line_discount_event(
        event_type=OrderEvents.ORDER_LINE_DISCOUNT_UPDATED,
        order=order,
        line=line,
        line_before_update=line_before_update,
        user=user,
    )


def order_line_discount_removed_event(
    order: Order,
    user: UserType,
    line: OrderLine,
) -> OrderEvent:
    return order_line_discount_event(
        event_type=OrderEvents.ORDER_LINE_DISCOUNT_REMOVED,
        order=order,
        line=line,
        user=user,
    )

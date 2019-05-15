from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union

from django.contrib.auth.base_user import AbstractBaseUser

from ..account.models import Address
from ..order.models import Fulfillment, FulfillmentLine, Order, OrderLine
from ..payment.models import Payment
from . import OrderEvents, OrderEventsEmails
from .models import OrderEvent

UserType = AbstractBaseUser


def _lines_per_quantity_to_line_object_list(quantities_per_order_line):
    return [
        {"quantity": quantity, "line_pk": line.pk, "item": str(line)}
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


def _new_event(**data) -> OrderEvent:
    return OrderEvent.objects.create(**data)


def email_sent_event(
    *,
    order: Order,
    user: Optional[UserType],
    email_type: OrderEventsEmails,
    user_pk: int = None,
):

    if user is not None and not user.is_anonymous:
        kwargs = {"user": user}
    elif user_pk:
        kwargs = {"user_id": user_pk}
    else:
        kwargs = {}

    return _new_event(
        order=order,
        type=OrderEvents.EMAIL_SENT,
        parameters={"email": order.get_user_current_email(), "email_type": email_type},
        **kwargs,
    )


def email_resent_event(*, order: Order, user: UserType, email_type: OrderEventsEmails):
    raise NotImplementedError


def draft_order_created_event(*, order: Order, user: UserType):
    return _new_event(order=order, type=OrderEvents.DRAFT_CREATED, user=user)


def draft_order_added_products_event(
    *, order: Order, user: UserType, order_lines: List[Tuple[int, OrderLine]]
):

    return _new_event(
        order=order,
        type=OrderEvents.DRAFT_ADDED_PRODUCTS,
        user=user,
        parameters={"lines": _lines_per_quantity_to_line_object_list(order_lines)},
    )


def draft_order_removed_products_event(
    *, order: Order, user: UserType, order_lines: List[Tuple[int, OrderLine]]
):

    return _new_event(
        order=order,
        type=OrderEvents.DRAFT_REMOVED_PRODUCTS,
        user=user,
        parameters={"lines": _lines_per_quantity_to_line_object_list(order_lines)},
    )


def order_created_event(*, order: Order, user: UserType, from_draft=False):
    event_type = OrderEvents.PLACED_FROM_DRAFT if from_draft else OrderEvents.PLACED

    if user.is_anonymous:
        user = None

    return _new_event(order=order, type=event_type, user=user)


def draft_order_oversold_items_event(
    *, order: Order, user: UserType, oversold_items: List[str]
):
    return _new_event(
        order=order,
        type=OrderEvents.OVERSOLD_ITEMS,
        user=user,
        parameters={"oversold_items": oversold_items},
    )


def order_canceled_event(*, order: Order, user: UserType):
    return _new_event(order=order, type=OrderEvents.CANCELED, user=user)


def order_manually_marked_as_paid_event(*, order: Order, user: UserType):
    return _new_event(order=order, type=OrderEvents.ORDER_MARKED_AS_PAID, user=user)


def order_fully_paid_event(*, order: Order):
    return _new_event(order=order, type=OrderEvents.ORDER_FULLY_PAID)


def payment_captured_event(
    *, order: Order, user: UserType, amount: Decimal, payment: Payment
):
    return _new_event(
        order=order,
        type=OrderEvents.PAYMENT_CAPTURED,
        user=user,
        **_get_payment_data(amount, payment),
    )


def payment_refunded_event(
    *, order: Order, user: UserType, amount: Decimal, payment: Payment
):
    return _new_event(
        order=order,
        type=OrderEvents.PAYMENT_REFUNDED,
        user=user,
        **_get_payment_data(amount, payment),
    )


def payment_voided_event(*, order: Order, user: UserType, payment: Payment):
    return _new_event(
        order=order,
        type=OrderEvents.PAYMENT_VOIDED,
        user=user,
        **_get_payment_data(None, payment),
    )


def payment_failed_event(
    *, order: Order, user: UserType, message: str, payment: Payment
):

    parameters = {"message": message}

    if payment:
        parameters.update({"gateway": payment.gateway, "payment_id": payment.token})

    return _new_event(
        order=order, type=OrderEvents.PAYMENT_FAILED, user=user, parameters=parameters
    )


def fulfillment_canceled_event(
    *, order: Order, user: UserType, fulfillment: Fulfillment
):
    return _new_event(
        order=order,
        type=OrderEvents.FULFILLMENT_CANCELED,
        user=user,
        parameters={"composed_id": fulfillment.composed_id},
    )


def fulfillment_restocked_items_event(
    *, order: Order, user: UserType, fulfillment: Union[Order, Fulfillment]
):
    return _new_event(
        order=order,
        type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS,
        user=user,
        parameters={"quantity": fulfillment.get_total_quantity()},
    )


def fulfillment_fulfilled_items_event(
    *, order: Order, user: UserType, fulfillment_lines: List[FulfillmentLine]
):
    return _new_event(
        order=order,
        type=OrderEvents.FULFILLMENT_FULFILLED_ITEMS,
        user=user,
        parameters={"fulfilled_items": [line.pk for line in fulfillment_lines]},
    )


def fulfillment_tracking_updated_event(
    *, order: Order, user: UserType, tracking_number: str, fulfillment: Fulfillment
):
    return _new_event(
        order=order,
        type=OrderEvents.TRACKING_UPDATED,
        user=user,
        parameters={
            "tracking_number": tracking_number,
            "fulfillment": fulfillment.composed_id,
        },
    )


def order_note_added_event(*, order: Order, user: UserType, message: str):
    return _new_event(
        order=order,
        type=OrderEvents.NOTE_ADDED,
        user=user,
        parameters={"message": message},
    )


def order_updated_address_event(*, order: Order, user: UserType, address: Address):
    return _new_event(
        order=order,
        type=OrderEvents.UPDATED_ADDRESS,
        user=user,
        parameters={"new_address": str(address)},
    )

from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union

from ..account import events as account_events
from ..account.models import Address, User
from ..order.models import Fulfillment, FulfillmentLine, Order, OrderLine
from ..payment.models import Payment
from . import OrderEvents, OrderEventsEmails
from .models import OrderEvent

UserType = User


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


def email_sent_event(
    *,
    order: Order,
    user: Optional[UserType],
    email_type: OrderEventsEmails,
    user_pk: int = None,
) -> OrderEvent:

    if user is not None and not user.is_anonymous:
        kwargs = {"user": user}
    elif user_pk:
        kwargs = {"user_id": user_pk}
    else:
        kwargs = {}

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.EMAIL_SENT,
        parameters={"email": order.get_user_current_email(), "email_type": email_type},
        **kwargs,
    )


def email_resent_event(
    *, order: Order, user: UserType, email_type: OrderEventsEmails
) -> OrderEvent:
    raise NotImplementedError


def draft_order_created_event(*, order: Order, user: UserType) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order, type=OrderEvents.DRAFT_CREATED, user=user
    )


def draft_order_added_products_event(
    *, order: Order, user: UserType, order_lines: List[Tuple[int, OrderLine]]
) -> OrderEvent:

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.DRAFT_ADDED_PRODUCTS,
        user=user,
        parameters={"lines": _lines_per_quantity_to_line_object_list(order_lines)},
    )


def draft_order_removed_products_event(
    *, order: Order, user: UserType, order_lines: List[Tuple[int, OrderLine]]
) -> OrderEvent:

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.DRAFT_REMOVED_PRODUCTS,
        user=user,
        parameters={"lines": _lines_per_quantity_to_line_object_list(order_lines)},
    )


def order_created_event(
    *, order: Order, user: UserType, from_draft=False
) -> OrderEvent:
    if from_draft:
        event_type = OrderEvents.PLACED_FROM_DRAFT
    else:
        event_type = OrderEvents.PLACED
        account_events.customer_placed_order_event(user=user, order=order)

    if user.is_anonymous:
        user = None

    return OrderEvent.objects.create(order=order, type=event_type, user=user)


def draft_order_oversold_items_event(
    *, order: Order, user: UserType, oversold_items: List[str]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.OVERSOLD_ITEMS,
        user=user,
        parameters={"oversold_items": oversold_items},
    )


def order_canceled_event(*, order: Order, user: UserType) -> OrderEvent:
    return OrderEvent.objects.create(order=order, type=OrderEvents.CANCELED, user=user)


def order_manually_marked_as_paid_event(*, order: Order, user: UserType) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order, type=OrderEvents.ORDER_MARKED_AS_PAID, user=user
    )


def order_fully_paid_event(*, order: Order) -> OrderEvent:
    return OrderEvent.objects.create(order=order, type=OrderEvents.ORDER_FULLY_PAID)


def payment_captured_event(
    *, order: Order, user: UserType, amount: Decimal, payment: Payment
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_CAPTURED,
        user=user,
        **_get_payment_data(amount, payment),
    )


def payment_refunded_event(
    *, order: Order, user: UserType, amount: Decimal, payment: Payment
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_REFUNDED,
        user=user,
        **_get_payment_data(amount, payment),
    )


def payment_voided_event(
    *, order: Order, user: UserType, payment: Payment
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.PAYMENT_VOIDED,
        user=user,
        **_get_payment_data(None, payment),
    )


def payment_failed_event(
    *, order: Order, user: UserType, message: str, payment: Payment
) -> OrderEvent:

    parameters = {"message": message}

    if payment:
        parameters.update({"gateway": payment.gateway, "payment_id": payment.token})

    return OrderEvent.objects.create(
        order=order, type=OrderEvents.PAYMENT_FAILED, user=user, parameters=parameters
    )


def fulfillment_canceled_event(
    *, order: Order, user: UserType, fulfillment: Fulfillment
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_CANCELED,
        user=user,
        parameters={"composed_id": fulfillment.composed_id},
    )


def fulfillment_restocked_items_event(
    *, order: Order, user: UserType, fulfillment: Union[Order, Fulfillment]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS,
        user=user,
        parameters={"quantity": fulfillment.get_total_quantity()},
    )


def fulfillment_fulfilled_items_event(
    *, order: Order, user: UserType, fulfillment_lines: List[FulfillmentLine]
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.FULFILLMENT_FULFILLED_ITEMS,
        user=user,
        parameters={"fulfilled_items": [line.pk for line in fulfillment_lines]},
    )


def fulfillment_tracking_updated_event(
    *, order: Order, user: UserType, tracking_number: str, fulfillment: Fulfillment
) -> OrderEvent:
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
    if order.user.pk == user.pk:
        account_events.customer_added_to_note_order_event(
            user=user, order=order, message=message
        )

    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.NOTE_ADDED,
        user=user,
        parameters={"message": message},
    )


def order_updated_address_event(
    *, order: Order, user: UserType, address: Address
) -> OrderEvent:
    return OrderEvent.objects.create(
        order=order,
        type=OrderEvents.UPDATED_ADDRESS,
        user=user,
        parameters={"new_address": str(address)},
    )

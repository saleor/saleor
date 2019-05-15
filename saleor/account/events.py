from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser

from ..order.models import Order, OrderLine
from . import CustomerEvents
from .models import CustomerEvent

UserType = AbstractBaseUser


def customer_placed_order_event(
    *, user: UserType, order: Order
) -> Optional[CustomerEvent]:
    if user.is_anonymous:
        return None

    return CustomerEvent.objects.create(
        user=user, order=order, type=CustomerEvents.PLACED_ORDER
    )


def customer_added_to_note_order_event(
    *, user: UserType, order: Order, message: str
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=user,
        order=order,
        type=CustomerEvents.NOTE_ADDED_TO_ORDER,
        parameters={"message": message},
    )


def customer_downloaded_a_digital_link_event(
    *, user: UserType, order_line: OrderLine
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=user,
        order=order_line.order,
        type=CustomerEvents.DIGITAL_LINK_DOWNLOADED,
        parameters={"order_line_pk": order_line.pk},
    )


def staff_user_deleted_a_customer_event(
    *, staff_user: UserType, deleted_count: int = 1
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=staff_user,
        order=None,
        type=CustomerEvents.CUSTOMER_DELETED,
        parameters={"count": deleted_count},
    )

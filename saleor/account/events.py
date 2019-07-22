from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser

from ..order.models import Order, OrderLine
from . import CustomerEvents
from .models import CustomerEvent

UserType = AbstractBaseUser


def customer_account_created_event(*, user: UserType) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.ACCOUNT_CREATED)


def customer_password_reset_link_sent_event(
    *, user_id: UserType
) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(
        user_id=user_id, type=CustomerEvents.PASSWORD_RESET_LINK_SENT
    )


def customer_password_reset_event(*, user: UserType) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.PASSWORD_RESET)


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


def staff_user_assigned_email_to_a_customer_event(
    *, staff_user: UserType, new_email: str
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=staff_user,
        order=None,
        type=CustomerEvents.EMAIL_ASSIGNED,
        parameters={"message": new_email},
    )


def staff_user_added_note_to_a_customer_event(
    *, staff_user: UserType, note: str
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=staff_user,
        order=None,
        type=CustomerEvents.NOTE_ADDED,
        parameters={"message": note},
    )


def staff_user_assigned_name_to_a_customer_event(
    *, staff_user: UserType, new_name: str
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=staff_user,
        order=None,
        type=CustomerEvents.NAME_ASSIGNED,
        parameters={"message": new_name},
    )

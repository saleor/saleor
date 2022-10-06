from typing import Optional

from ..app.models import App
from ..order.models import Order, OrderLine
from . import CustomerEvents
from .models import CustomerEvent, User

UserType = Optional[User]
AppType = Optional[App]


def customer_account_created_event(*, user: User) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.ACCOUNT_CREATED)


def customer_account_activated_event(
    *, staff_user: UserType, app: AppType, account_id: int
) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        type=CustomerEvents.ACCOUNT_ACTIVATED,
        parameters={"account_id": account_id},
    )


def customer_account_deactivated_event(
    *, staff_user: UserType, app: AppType, account_id: int
) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        type=CustomerEvents.ACCOUNT_DEACTIVATED,
        parameters={"account_id": account_id},
    )


def customer_password_reset_link_sent_event(*, user_id: int) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(
        user_id=user_id, type=CustomerEvents.PASSWORD_RESET_LINK_SENT
    )


def customer_password_reset_event(*, user: User) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.PASSWORD_RESET)


def customer_password_changed_event(*, user: User) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.PASSWORD_CHANGED)


def customer_email_change_request_event(
    *, user_id: int, parameters: dict
) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(
        user_id=user_id, type=CustomerEvents.EMAIL_CHANGE_REQUEST, parameters=parameters
    )


def customer_email_changed_event(
    *, user_id: int, parameters: dict
) -> Optional[CustomerEvent]:
    return CustomerEvent.objects.create(
        user_id=user_id, type=CustomerEvents.EMAIL_CHANGED, parameters=parameters
    )


def customer_placed_order_event(*, user: User, order: Order) -> Optional[CustomerEvent]:
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
    *, user: User, order_line: OrderLine
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=user,
        order=order_line.order,
        type=CustomerEvents.DIGITAL_LINK_DOWNLOADED,
        parameters={"order_line_pk": order_line.pk},
    )


def customer_deleted_event(
    *, staff_user: UserType, app: AppType, deleted_count: int = 1
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        order=None,
        type=CustomerEvents.CUSTOMER_DELETED,
        parameters={"count": deleted_count},
    )


def assigned_email_to_a_customer_event(
    *, staff_user: UserType, app: AppType, new_email: str
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        order=None,
        type=CustomerEvents.EMAIL_ASSIGNED,
        parameters={"message": new_email},
    )


def assigned_name_to_a_customer_event(
    *, staff_user: UserType, app: AppType, new_name: str
) -> CustomerEvent:
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        order=None,
        type=CustomerEvents.NAME_ASSIGNED,
        parameters={"message": new_name},
    )

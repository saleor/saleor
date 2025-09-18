from ..app.models import App
from ..order.models import Order, OrderLine
from . import CustomerEvents
from .models import CustomerEvent, User


def customer_account_created_event(*, user: User) -> CustomerEvent | None:
    """创建客户帐户已创建事件。"""
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.ACCOUNT_CREATED)


def customer_account_activated_event(
    *, staff_user: User | None, app: App | None, account_id: int
) -> CustomerEvent | None:
    """创建客户帐户已激活事件。"""
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        type=CustomerEvents.ACCOUNT_ACTIVATED,
        parameters={"account_id": account_id},
    )


def customer_account_deactivated_event(
    *, staff_user: User | None, app: App | None, account_id: int
) -> CustomerEvent | None:
    """创建客户帐户已停用事件。"""
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        type=CustomerEvents.ACCOUNT_DEACTIVATED,
        parameters={"account_id": account_id},
    )


def customer_password_reset_link_sent_event(*, user_id: int) -> CustomerEvent | None:
    """创建客户密码重置链接已发送事件。"""
    return CustomerEvent.objects.create(
        user_id=user_id, type=CustomerEvents.PASSWORD_RESET_LINK_SENT
    )


def customer_password_reset_event(*, user: User) -> CustomerEvent | None:
    """创建客户密码已重置事件。"""
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.PASSWORD_RESET)


def customer_password_changed_event(*, user: User) -> CustomerEvent | None:
    """创建客户密码已更改事件。"""
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.PASSWORD_CHANGED)


def customer_email_change_request_event(
    *, user_id: int, parameters: dict
) -> CustomerEvent | None:
    """创建客户电子邮件更改请求事件。"""
    return CustomerEvent.objects.create(
        user_id=user_id, type=CustomerEvents.EMAIL_CHANGE_REQUEST, parameters=parameters
    )


def customer_email_changed_event(
    *, user_id: int, parameters: dict
) -> CustomerEvent | None:
    """创建客户电子邮件已更改事件。"""
    return CustomerEvent.objects.create(
        user_id=user_id, type=CustomerEvents.EMAIL_CHANGED, parameters=parameters
    )


def customer_placed_order_event(*, user: User, order: Order) -> CustomerEvent | None:
    """创建客户已下单事件。"""
    return CustomerEvent.objects.create(
        user=user, order=order, type=CustomerEvents.PLACED_ORDER
    )


def customer_added_to_note_order_event(
    *, user: User | None, order: Order, message: str
) -> CustomerEvent:
    """创建客户已向订单添加备注事件。"""
    return CustomerEvent.objects.create(
        user=user,
        order=order,
        type=CustomerEvents.NOTE_ADDED_TO_ORDER,
        parameters={"message": message},
    )


def customer_downloaded_a_digital_link_event(
    *, user: User, order_line: OrderLine
) -> CustomerEvent:
    """创建客户已下载数字链接事件。"""
    return CustomerEvent.objects.create(
        user=user,
        order=order_line.order,
        type=CustomerEvents.DIGITAL_LINK_DOWNLOADED,
        parameters={"order_line_pk": order_line.pk},
    )


def customer_deleted_event(
    *, staff_user: User | None, app: App | None, deleted_count: int = 1
) -> CustomerEvent:
    """创建客户已删除事件。"""
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        order=None,
        type=CustomerEvents.CUSTOMER_DELETED,
        parameters={"count": deleted_count},
    )


def assigned_email_to_a_customer_event(
    *, staff_user: User | None, app: App | None, new_email: str
) -> CustomerEvent:
    """创建已向客户分配电子邮件事件。"""
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        order=None,
        type=CustomerEvents.EMAIL_ASSIGNED,
        parameters={"message": new_email},
    )


def assigned_name_to_a_customer_event(
    *, staff_user: User | None, app: App | None, new_name: str
) -> CustomerEvent:
    """创建已向客户分配姓名事件。"""
    return CustomerEvent.objects.create(
        user=staff_user,
        app=app,
        order=None,
        type=CustomerEvents.NAME_ASSIGNED,
        parameters={"message": new_name},
    )

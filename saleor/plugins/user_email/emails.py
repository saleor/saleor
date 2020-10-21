from ...account.models import User
from .tasks import (
    send_account_confirmation_email_task,
    send_account_delete_confirmation_email_task,
    send_password_reset_email_task,
    send_request_email_change_email_task,
    send_set_user_password_email_task,
    send_user_change_email_notification_task,
)

REQUEST_EMAIL_CHANGE_TEMPLATE = "account/request_email_change"
EMAIL_CHANGED_NOTIFICATION_TEMPLATE = "account/email_changed_notification"
ACCOUNT_DELETE_TEMPLATE = "account/account_delete"
PASSWORD_RESET_TEMPLATE = "account/password_reset"


def get_default_user_payload(user: User):
    return {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_active": user.is_active,
        "private_metadata": user.private_metadata,
        "metadata": user.metadata,
    }


def handle_account_password_reset_event(payload):
    send_password_reset_email_task.delay(
        payload["email"], payload["redirect_url"], payload["id"], payload["token"]
    )


def handle_account_confirmation(payload):
    send_account_confirmation_email_task.delay(
        payload["email"], payload["token"], payload["redirect_url"]
    )


def handle_account_change_email_request(payload):
    send_request_email_change_email_task.delay(
        payload["new_email"],
        payload["old_email"],
        payload["redirect_url"],
        payload["id"],
        payload["token"],
    )


def handle_account_change_email_confirm(payload):
    send_user_change_email_notification_task.delay(payload["old_email"])


def handle_account_delete(payload):
    send_account_delete_confirmation_email_task.delay(
        payload["email"], payload["redirect_url"], payload["token"]
    )


def handle_account_set_customer_password(payload):
    send_set_user_password_email_task.delay(
        payload["email"], payload["redirect_url"], payload["token"]
    )

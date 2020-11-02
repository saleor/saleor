from .tasks import (
    handle_fulfillment_confirmation_task,
    handle_fulfillment_update_task,
    handle_order_canceled_task,
    handle_order_refund_task,
    handle_payment_confirmation_task,
    send_account_confirmation_email_task,
    send_account_delete_confirmation_email_task,
    send_invoice_task,
    send_order_confirmation_task,
    send_password_reset_email_task,
    send_request_email_change_email_task,
    send_set_user_password_email_task,
    send_user_change_email_notification_task,
)


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


def handle_send_invoice(payload):
    send_invoice_task.delay(
        recipient_email=payload["email"],
        invoice_number=payload["number"],
        invoice_download_url=payload["download_url"],
    )


def handle_order_confirmation(payload):
    send_order_confirmation_task(payload=payload)


def handle_fulfillment_confirmation(payload):

    handle_fulfillment_confirmation_task(payload)


def handle_fulfillment_update(payload):
    handle_fulfillment_update_task(payload)


def handle_payment_confirmation(payload):

    handle_payment_confirmation_task(payload)


def handle_order_canceled(payload):
    handle_order_canceled_task.delay(payload)


def handle_order_refund(payload):
    handle_order_refund_task.delay(payload)

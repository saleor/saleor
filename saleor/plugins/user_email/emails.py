from .tasks import (
    send_account_confirmation_email_task,
    send_account_delete_confirmation_email_task,
    send_fulfillment_confirmation_email_task,
    send_fulfillment_update_email_task,
    send_invoice_email_task,
    send_order_canceled_email_task,
    send_order_confirmation_email_task,
    send_order_refund_email_task,
    send_password_reset_email_task,
    send_payment_confirmation_email_task,
    send_request_email_change_email_task,
    send_set_user_password_email_task,
    send_user_change_email_notification_task,
)


def send_account_password_reset_event(payload):
    recipient_email = payload["recipient_email"]
    user_payload = payload.get("user")
    send_password_reset_email_task.delay(
        recipient_email, payload["redirect_url"], user_payload["id"], payload["token"],
    )


def send_account_confirmation(payload):
    recipient_email = payload["recipient_email"]
    send_account_confirmation_email_task.delay(
        recipient_email, payload["token"], payload["redirect_url"]
    )


def send_account_change_email_request(payload):
    recipient_email = payload["recipient_email"]
    user_payload = payload.get("user")
    send_request_email_change_email_task.delay(
        recipient_email,
        payload["old_email"],
        payload["redirect_url"],
        user_payload["id"],
        payload["token"],
    )


def send_account_change_email_confirm(payload):
    recipient_email = payload["recipient_email"]
    send_user_change_email_notification_task.delay(recipient_email)


def send_account_delete(payload):
    recipient_email = payload["recipient_email"]
    send_account_delete_confirmation_email_task.delay(
        recipient_email, payload["redirect_url"], payload["token"]
    )


def send_account_set_customer_password(payload):
    recipient_email = payload["recipient_email"]
    send_set_user_password_email_task.delay(
        recipient_email, payload["redirect_url"], payload["token"]
    )


def send_invoice(payload):
    recipient_email = payload["recipient_email"]
    send_invoice_email_task.delay(
        recipient_email=recipient_email,
        invoice_number=payload["number"],
        invoice_download_url=payload["download_url"],
    )


def send_order_confirmation(payload):
    send_order_confirmation_email_task(payload=payload)


def send_fulfillment_confirmation(payload):
    send_fulfillment_confirmation_email_task(payload)


def send_fulfillment_update(payload):
    send_fulfillment_update_email_task(payload)


def send_payment_confirmation(payload):
    send_payment_confirmation_email_task(payload)


def send_order_canceled(payload):
    send_order_canceled_email_task.delay(payload)


def send_order_refund(payload):
    send_order_refund_email_task.delay(payload)

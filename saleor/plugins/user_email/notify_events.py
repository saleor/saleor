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


def send_account_password_reset_event(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    user_payload = payload["user"]
    send_password_reset_email_task.delay(
        recipient_email,
        payload["redirect_url"],
        user_payload["id"],
        payload["token"],
        config,
    )


def send_account_confirmation(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_account_confirmation_email_task.delay(
        recipient_email, payload["token"], payload["redirect_url"], config
    )


def send_account_change_email_request(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    user_payload = payload["user"]
    send_request_email_change_email_task.delay(
        recipient_email,
        payload["old_email"],
        payload["redirect_url"],
        user_payload["id"],
        payload["token"],
        config,
    )


def send_account_change_email_confirm(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_user_change_email_notification_task.delay(recipient_email, config)


def send_account_delete(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_account_delete_confirmation_email_task.delay(
        recipient_email, payload["redirect_url"], payload["token"], config
    )


def send_account_set_customer_password(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_set_user_password_email_task.delay(
        recipient_email, payload["redirect_url"], payload["token"], config
    )


def send_invoice(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_invoice_email_task.delay(
        recipient_email=recipient_email,
        invoice_number=payload["number"],
        invoice_download_url=payload["download_url"],
        config=config,
    )


def send_order_confirmation(payload: dict, config: dict):
    send_order_confirmation_email_task(payload=payload, config=config)


def send_fulfillment_confirmation(payload: dict, config: dict):
    send_fulfillment_confirmation_email_task(payload, config)


def send_fulfillment_update(payload: dict, config: dict):
    send_fulfillment_update_email_task(payload, config)


def send_payment_confirmation(payload: dict, config: dict):
    send_payment_confirmation_email_task(payload, config)


def send_order_canceled(payload: dict, config: dict):
    send_order_canceled_email_task.delay(payload, config)


def send_order_refund(payload: dict, config: dict):
    send_order_refund_email_task.delay(payload, config)

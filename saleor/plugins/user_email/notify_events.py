from .tasks import (
    send_account_confirmation_email_task,
    send_account_delete_confirmation_email_task,
    send_fulfillment_confirmation_email_task,
    send_fulfillment_update_email_task,
    send_invoice_email_task,
    send_order_canceled_email_task,
    send_order_confirmation_email_task,
    send_order_confirmed_email_task,
    send_order_refund_email_task,
    send_password_reset_email_task,
    send_payment_confirmation_email_task,
    send_request_email_change_email_task,
    send_set_user_password_email_task,
    send_user_change_email_notification_task,
)


def send_account_password_reset_event(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_password_reset_email_task.delay(
        recipient_email,
        payload,
        config,
    )


def send_account_confirmation(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_account_confirmation_email_task.delay(recipient_email, payload, config)


def send_account_change_email_request(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_request_email_change_email_task.delay(
        recipient_email,
        payload,
        config,
    )


def send_account_change_email_confirm(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_user_change_email_notification_task.delay(recipient_email, payload, config)


def send_account_delete(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_account_delete_confirmation_email_task.delay(recipient_email, payload, config)


def send_account_set_customer_password(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_set_user_password_email_task.delay(recipient_email, payload, config)


def send_invoice(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_invoice_email_task.delay(
        recipient_email,
        payload,
        config,
    )


def send_order_confirmation(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_order_confirmation_email_task.delay(recipient_email, payload, config)


def send_fulfillment_confirmation(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_fulfillment_confirmation_email_task.delay(recipient_email, payload, config)


def send_fulfillment_update(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_fulfillment_update_email_task.delay(recipient_email, payload, config)


def send_payment_confirmation(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_payment_confirmation_email_task.delay(recipient_email, payload, config)


def send_order_canceled(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_order_canceled_email_task.delay(recipient_email, payload, config)


def send_order_refund(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_order_refund_email_task.delay(recipient_email, payload, config)


def send_order_confirmed(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_order_confirmed_email_task.delay(recipient_email, payload, config)

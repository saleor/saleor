from .tasks import (
    send_email_with_link_to_download_file_task,
    send_export_failed_email_task,
    send_set_staff_password_email_task,
    send_staff_order_confirmation_email_task,
    send_staff_password_reset_email_task,
)


def send_set_staff_password_email(payload: dict, config: dict):
    recipient_email = payload["recipient_email"]
    send_set_staff_password_email_task.delay(
        recipient_email,
        payload,
        config,
    )


def send_csv_product_export_success(payload: dict, config: dict):
    recipient_email = payload.get("recipient_email")
    if recipient_email:
        send_email_with_link_to_download_file_task.delay(
            recipient_email, payload, config
        )


def send_staff_order_confirmation(payload: dict, config: dict):
    recipient_list = payload.get("recipient_list")
    send_staff_order_confirmation_email_task.delay(recipient_list, payload, config)


def send_csv_export_failed(payload: dict, config: dict):
    recipient_email = payload.get("recipient_email")
    if recipient_email:
        send_export_failed_email_task.delay(recipient_email, payload, config)


def send_staff_reset_password(payload: dict, config: dict):
    recipient_email = payload.get("recipient_email")
    if recipient_email:
        send_staff_password_reset_email_task.delay(recipient_email, payload, config)

from .tasks import (
    send_email_with_link_to_download_file_task,
    send_export_failed_email_task,
    send_set_staff_password_email_task,
    send_staff_order_confirmation_email_task,
)


def send_set_staff_password_email(payload):
    recipient_email = payload["recipient_email"]
    send_set_staff_password_email_task.delay(
        recipient_email, payload["redirect_url"], payload["token"]
    )


def send_csv_product_export_success(payload: dict):
    recipient_email = payload.get("recipient_email")
    if recipient_email:
        send_email_with_link_to_download_file_task.delay(
            recipient_email, payload["csv_link"]
        )


def send_staff_order_confirmation(payload: dict):
    send_staff_order_confirmation_email_task.delay(payload)


def send_csv_export_failed(payload: dict):
    recipient_email = payload.get("recipient_email")
    if recipient_email:
        send_export_failed_email_task.delay(recipient_email)

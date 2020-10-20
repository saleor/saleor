from .tasks import (
    send_email_with_link_to_download_file,
    send_export_failed_info,
    send_set_staff_password_email_task,
)


def handle_account_set_staff_password(payload):
    send_set_staff_password_email_task.delay(
        payload["email"], payload["redirect_url"], payload["token"]
    )


def handle_csv_product_export_success(payload: dict):
    recipient_email = payload.get("user_email")
    if recipient_email:
        send_email_with_link_to_download_file.delay(
            recipient_email, payload["csv_link"]
        )


def handle_csv_export_failed(payload: dict):
    recipient_email = payload.get("user_email")
    if recipient_email:
        send_export_failed_info.delay(recipient_email)

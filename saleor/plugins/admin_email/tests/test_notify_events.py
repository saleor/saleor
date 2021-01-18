from unittest import mock

from ....order.notifications import get_default_order_payload
from ..notify_events import (
    send_csv_export_failed,
    send_csv_product_export_success,
    send_set_staff_password_email,
    send_staff_order_confirmation,
)


@mock.patch(
    "saleor.plugins.admin_email.notify_events.send_set_staff_password_email_task.delay"
)
def test_send_set_staff_password_email(mocked_email_task):
    payload = {
        "recipient_email": "admin@example.com",
        "redirect_url": "http://127.0.0.1:8000/redirect",
        "token": "token123",
    }
    config = {"host": "localhost", "port": "1025"}
    send_set_staff_password_email(
        payload=payload,
        config=config,
    )
    mocked_email_task.assert_called_with(payload["recipient_email"], payload, config)


@mock.patch(
    "saleor.plugins.admin_email.notify_events."
    "send_email_with_link_to_download_file_task.delay"
)
def test_send_csv_product_export_success(mocked_email_task):
    payload = {
        "recipient_email": "admin@example.com",
        "csv_link": "http://127.0.0.1:8000/download/csv",
    }
    config = {"host": "localhost", "port": "1025"}
    send_csv_product_export_success(
        payload=payload,
        config=config,
    )
    mocked_email_task.assert_called_with(payload["recipient_email"], payload, config)


@mock.patch(
    "saleor.plugins.admin_email.notify_events."
    "send_staff_order_confirmation_email_task.delay"
)
def test_send_staff_order_confirmation(mocked_email_task, order):
    order_payload = get_default_order_payload(order)
    payload = {
        "order": order_payload,
        "recipient_list": ["admin@example.com"],
    }
    config = {"host": "localhost", "port": "1025"}
    send_staff_order_confirmation(
        payload=payload,
        config=config,
    )
    mocked_email_task.assert_called_with(payload["recipient_list"], payload, config)


@mock.patch(
    "saleor.plugins.admin_email.notify_events." "send_export_failed_email_task.delay"
)
def test_send_csv_export_failed(mocked_email_task):
    payload = {
        "recipient_email": "admin@example.com",
    }
    config = {"host": "localhost", "port": "1025"}
    send_csv_export_failed(
        payload=payload,
        config=config,
    )
    mocked_email_task.assert_called_with(payload["recipient_email"], payload, config)

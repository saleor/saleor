from unittest import mock

from ....account.notifications import get_default_user_payload
from ....order.notifications import get_default_order_payload
from ..notify_events import (
    send_csv_export_failed,
    send_csv_export_success,
    send_set_staff_password_email,
    send_staff_order_confirmation,
    send_staff_reset_password,
)


@mock.patch(
    "saleor.plugins.admin_email.notify_events.send_staff_password_reset_email_task."
    "delay"
)
def test_send_account_password_reset_event(
    mocked_email_task, customer_user, admin_email_plugin
):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }
    config = {"host": "localhost", "port": "1025"}
    send_staff_reset_password(
        payload=payload, config=config, plugin=admin_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.admin_email.notify_events.send_staff_password_reset_email_task."
    "delay"
)
def test_send_account_password_reset_event_empty_template(
    mocked_email_task, customer_user, admin_email_plugin
):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }
    config = {"host": "localhost", "port": "1025"}
    send_staff_reset_password(
        payload=payload,
        config=config,
        plugin=admin_email_plugin(staff_password_reset_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.admin_email.notify_events.send_set_staff_password_email_task.delay"
)
def test_send_set_staff_password_email(mocked_email_task, admin_email_plugin):
    payload = {
        "recipient_email": "admin@example.com",
        "redirect_url": "http://127.0.0.1:8000/redirect",
        "token": "token123",
    }
    config = {"host": "localhost", "port": "1025"}
    send_set_staff_password_email(
        payload=payload, config=config, plugin=admin_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.admin_email.notify_events.send_set_staff_password_email_task.delay"
)
def test_send_set_staff_password_email_empty_template(
    mocked_email_task, admin_email_plugin
):
    payload = {
        "recipient_email": "admin@example.com",
        "redirect_url": "http://127.0.0.1:8000/redirect",
        "token": "token123",
    }
    config = {"host": "localhost", "port": "1025"}
    send_set_staff_password_email(
        payload=payload,
        config=config,
        plugin=admin_email_plugin(set_staff_password_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.admin_email.notify_events."
    "send_email_with_link_to_download_file_task.delay"
)
def test_send_csv_export_success(mocked_email_task, admin_email_plugin):
    payload = {
        "recipient_email": "admin@example.com",
        "csv_link": "http://127.0.0.1:8000/download/csv",
    }
    config = {"host": "localhost", "port": "1025"}
    send_csv_export_success(payload=payload, config=config, plugin=admin_email_plugin())
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.admin_email.notify_events."
    "send_email_with_link_to_download_file_task.delay"
)
def test_send_csv_product_export_success_empty_template(
    mocked_email_task, admin_email_plugin
):
    payload = {
        "recipient_email": "admin@example.com",
        "csv_link": "http://127.0.0.1:8000/download/csv",
    }
    config = {"host": "localhost", "port": "1025"}
    send_csv_export_success(
        payload=payload, config=config, plugin=admin_email_plugin(csv_product_export="")
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.admin_email.notify_events."
    "send_staff_order_confirmation_email_task.delay"
)
def test_send_staff_order_confirmation(mocked_email_task, order, admin_email_plugin):
    order_payload = get_default_order_payload(order)
    payload = {
        "order": order_payload,
        "recipient_list": ["admin@example.com"],
    }
    config = {"host": "localhost", "port": "1025"}
    send_staff_order_confirmation(
        payload=payload, config=config, plugin=admin_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_list"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.admin_email.notify_events."
    "send_staff_order_confirmation_email_task.delay"
)
def test_send_staff_order_confirmation_empty_template(
    mocked_email_task, order, admin_email_plugin
):
    order_payload = get_default_order_payload(order)
    payload = {
        "order": order_payload,
        "recipient_list": ["admin@example.com"],
    }
    config = {"host": "localhost", "port": "1025"}
    send_staff_order_confirmation(
        payload=payload,
        config=config,
        plugin=admin_email_plugin(staff_order_confirmation=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.admin_email.notify_events.send_export_failed_email_task.delay"
)
def test_send_csv_export_failed(mocked_email_task, admin_email_plugin):
    payload = {
        "recipient_email": "admin@example.com",
    }
    config = {"host": "localhost", "port": "1025"}
    send_csv_export_failed(payload=payload, config=config, plugin=admin_email_plugin())
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.admin_email.notify_events.send_export_failed_email_task.delay"
)
def test_send_csv_export_failed_empty_template(mocked_email_task, admin_email_plugin):
    payload = {
        "recipient_email": "admin@example.com",
    }
    config = {"host": "localhost", "port": "1025"}
    send_csv_export_failed(
        payload=payload,
        config=config,
        plugin=admin_email_plugin(csv_product_export_failed=""),
    )
    assert not mocked_email_task.called

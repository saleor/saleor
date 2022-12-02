from unittest import mock

from ....account.notifications import get_default_user_payload
from ....order.notifications import (
    get_default_fulfillment_payload,
    get_default_order_payload,
)
from ..notify_events import (
    send_account_change_email_confirm,
    send_account_change_email_request,
    send_account_confirmation,
    send_account_delete,
    send_account_password_reset_event,
    send_account_set_customer_password,
    send_fulfillment_confirmation,
    send_fulfillment_update,
    send_invoice,
    send_order_canceled,
    send_order_confirmation,
    send_order_confirmed,
    send_order_refund,
    send_payment_confirmation,
)


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_password_reset_email_task.delay"
)
def test_send_account_password_reset_event(
    mocked_email_task, customer_user, user_email_plugin
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
    send_account_password_reset_event(
        payload=payload, config=config, plugin=user_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_password_reset_email_task.delay"
)
def test_send_account_password_reset_event_with_empty_template(
    mocked_email_task, customer_user, user_email_plugin
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
    send_account_password_reset_event(
        payload=payload,
        config=config,
        plugin=user_email_plugin(password_reset_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_account_confirmation_email_task.delay"
)
def test_send_account_confirmation(mocked_email_task, customer_user, user_email_plugin):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "confirm_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_confirmation(
        payload=payload, config=config, plugin=user_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_account_confirmation_email_task.delay"
)
def test_send_account_confirmation_with_empty_template(
    mocked_email_task, customer_user, user_email_plugin
):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "confirm_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_confirmation(
        payload=payload,
        config=config,
        plugin=user_email_plugin(account_confirmation_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_request_email_change_email_task.delay"
)
def test_send_account_change_email_request(
    mocked_email_task, customer_user, user_email_plugin
):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "redirect_url": f"http://localhost:8000/redirect{token}",
        "old_email": "old.user@example.com",
        "new_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_change_email_request(
        payload=payload, config=config, plugin=user_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_request_email_change_email_task.delay"
)
def test_send_account_change_email_request_empty_template(
    mocked_email_task, customer_user, user_email_plugin
):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "redirect_url": f"http://localhost:8000/redirect{token}",
        "old_email": "old.user@example.com",
        "new_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_change_email_request(
        payload=payload,
        config=config,
        plugin=user_email_plugin(email_change_request_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_user_change_email_notification_task."
    "delay"
)
def test_send_account_change_email_confirm(
    mocked_email_task, customer_user, user_email_plugin
):
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_change_email_confirm(
        payload=payload, config=config, plugin=user_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_user_change_email_notification_task."
    "delay"
)
def test_send_account_change_email_confirm_empty_template(
    mocked_email_task, customer_user, user_email_plugin
):
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_change_email_confirm(
        payload=payload,
        config=config,
        plugin=user_email_plugin(email_change_confirm_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events."
    "send_account_delete_confirmation_email_task.delay"
)
def test_send_account_delete(mocked_email_task, customer_user, user_email_plugin):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "delete_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_delete(payload=payload, config=config, plugin=user_email_plugin())
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events."
    "send_account_delete_confirmation_email_task.delay"
)
def test_send_account_delete_with_empty_template(
    mocked_email_task, customer_user, user_email_plugin
):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "delete_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_delete(
        payload=payload,
        config=config,
        plugin=user_email_plugin(account_delete_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_set_user_password_email_task.delay"
)
def test_send_account_set_customer_password(
    mocked_email_task, customer_user, user_email_plugin
):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "password_set_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_set_customer_password(
        payload=payload, config=config, plugin=user_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_set_user_password_email_task.delay"
)
def test_send_account_set_customer_password_empty_template(
    mocked_email_task, customer_user, user_email_plugin
):
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "password_set_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_account_set_customer_password(
        payload=payload,
        config=config,
        plugin=user_email_plugin(account_set_password_template=""),
    )
    assert not mocked_email_task.called


@mock.patch("saleor.plugins.user_email.notify_events.send_invoice_email_task.delay")
def test_send_invoice(mocked_email_task, user_email_plugin):
    payload = {
        "invoice": {
            "id": 1,
            "number": 999,
            "download_url": "http://localhost:8000/download",
        },
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_invoice(payload=payload, config=config, plugin=user_email_plugin())
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch("saleor.plugins.user_email.notify_events.send_invoice_email_task.delay")
def test_send_invoice_with_empty_template(mocked_email_task, user_email_plugin):
    payload = {
        "invoice": {
            "id": 1,
            "number": 999,
            "download_url": "http://localhost:8000/download",
        },
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_invoice(
        payload=payload,
        config=config,
        plugin=user_email_plugin(invoice_ready_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_order_confirmation_email_task.delay"
)
def test_send_order_confirmation(mocked_email_task, order, user_email_plugin):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_order_confirmation(payload=payload, config=config, plugin=user_email_plugin())
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_order_confirmation_email_task.delay"
)
def test_send_order_confirmation_empty_template(
    mocked_email_task, order, user_email_plugin
):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_order_confirmation(
        payload=payload,
        config=config,
        plugin=user_email_plugin(order_confirmation_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_fulfillment_confirmation_email_task."
    "delay"
)
def test_send_fulfillment_confirmation(
    mocked_email_task, order, fulfillment, user_email_plugin
):
    payload = get_default_fulfillment_payload(order, fulfillment)
    config = {"host": "localhost", "port": "1025"}
    send_fulfillment_confirmation(
        payload=payload, config=config, plugin=user_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_fulfillment_confirmation_email_task."
    "delay"
)
def test_send_fulfillment_confirmation_empty_template(
    mocked_email_task, order, fulfillment, user_email_plugin
):
    payload = get_default_fulfillment_payload(order, fulfillment)
    config = {"host": "localhost", "port": "1025"}
    send_fulfillment_confirmation(
        payload=payload,
        config=config,
        plugin=user_email_plugin(fulfillment_confirmation_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_fulfillment_update_email_task.delay"
)
def test_send_fulfillment_update(
    mocked_email_task, order, fulfillment, user_email_plugin
):
    payload = get_default_fulfillment_payload(order, fulfillment)
    config = {"host": "localhost", "port": "1025"}
    send_fulfillment_update(payload=payload, config=config, plugin=user_email_plugin())
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_fulfillment_update_email_task.delay"
)
def test_send_fulfillment_update_empty_template(
    mocked_email_task, order, fulfillment, user_email_plugin
):
    payload = get_default_fulfillment_payload(order, fulfillment)
    config = {"host": "localhost", "port": "1025"}
    send_fulfillment_update(
        payload=payload,
        config=config,
        plugin=user_email_plugin(fulfillment_update_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_payment_confirmation_email_task.delay"
)
def test_send_payment_confirmation(
    mocked_email_task, order, payment_dummy, user_email_plugin
):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "payment": {
            "created": payment_dummy.created_at,
            "modified": payment_dummy.modified_at,
            "charge_status": payment_dummy.charge_status,
            "total": payment_dummy.total,
            "captured_amount": payment_dummy.captured_amount,
            "currency": payment_dummy.currency,
        },
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_payment_confirmation(
        payload=payload, config=config, plugin=user_email_plugin()
    )
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_payment_confirmation_email_task.delay"
)
def test_send_payment_confirmation_empty_template(
    mocked_email_task, order, payment_dummy, user_email_plugin
):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "payment": {
            "created": payment_dummy.created_at,
            "modified": payment_dummy.modified_at,
            "charge_status": payment_dummy.charge_status,
            "total": payment_dummy.total,
            "captured_amount": payment_dummy.captured_amount,
            "currency": payment_dummy.currency,
        },
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_payment_confirmation(
        payload=payload,
        config=config,
        plugin=user_email_plugin(payment_confirmation_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_order_canceled_email_task.delay"
)
def test_send_order_canceled(mocked_email_task, order, user_email_plugin):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_order_canceled(payload=payload, config=config, plugin=user_email_plugin())
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_order_canceled_email_task.delay"
)
def test_send_order_canceled_empty_template(
    mocked_email_task, order, user_email_plugin
):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_order_canceled(
        payload=payload,
        config=config,
        plugin=user_email_plugin(order_cancel_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_order_refund_email_task.delay"
)
def test_send_order_refund(mocked_email_task, order, user_email_plugin):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "amount": order.total_gross_amount,
        "currency": order.currency,
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_order_refund(payload=payload, config=config, plugin=user_email_plugin())
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_order_refund_email_task.delay"
)
def test_send_order_refund_with_empty_template(
    mocked_email_task, order, user_email_plugin
):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "amount": order.total_gross_amount,
        "currency": order.currency,
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_order_refund(
        payload=payload,
        config=config,
        plugin=user_email_plugin(order_refund_template=""),
    )
    assert not mocked_email_task.called


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_order_confirmed_email_task.delay"
)
def test_send_order_confirmed(mocked_email_task, order, user_email_plugin):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_order_confirmed(payload=payload, config=config, plugin=user_email_plugin())
    mocked_email_task.assert_called_with(
        payload["recipient_email"], payload, config, mock.ANY, mock.ANY
    )


@mock.patch(
    "saleor.plugins.user_email.notify_events.send_order_confirmed_email_task.delay"
)
def test_send_order_confirmed_empty_template(
    mocked_email_task, order, user_email_plugin
):
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    config = {"host": "localhost", "port": "1025"}
    send_order_confirmed(
        payload=payload,
        config=config,
        plugin=user_email_plugin(order_confirmed_template=""),
    )
    assert not mocked_email_task.called

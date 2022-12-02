from dataclasses import asdict
from unittest.mock import Mock, patch

import pytest

from ....account import CustomerEvents
from ....account.models import CustomerEvent
from ....account.notifications import get_default_user_payload
from ....giftcard import GiftCardEvents
from ....giftcard.models import GiftCardEvent
from ....graphql.core.utils import to_global_id_or_none
from ....invoice import InvoiceEvents
from ....invoice.models import Invoice, InvoiceEvent
from ....order import OrderEvents, OrderEventsEmails
from ....order.models import OrderEvent
from ....order.notifications import (
    get_default_fulfillment_payload,
    get_default_order_payload,
)
from ..tasks import (
    send_account_confirmation_email_task,
    send_account_delete_confirmation_email_task,
    send_email,
    send_fulfillment_confirmation_email_task,
    send_fulfillment_update_email_task,
    send_gift_card_email_task,
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


@pytest.fixture
def sample_payload(customer_user):
    token = "token123"
    return {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }


@patch("saleor.plugins.sendgrid.tasks.Mail")
@patch("saleor.plugins.sendgrid.tasks.SendGridAPIClient.send")
def test_send_email(
    mocked_api_client, mocked_mail, sendgrid_email_plugin, sample_payload
):
    plugin = sendgrid_email_plugin(
        sender_name="Sender Name",
        sender_address="sender@example.com",
        api_key="123",
    )
    template_id = "ABC"
    recipient_email = sample_payload["recipient_email"]

    config = plugin.config

    mock_message = Mock()
    mocked_mail.return_value = mock_message

    send_email(config, template_id=template_id, payload=sample_payload)

    mocked_mail.assert_called_with(
        from_email=(config.sender_address, config.sender_name),
        to_emails=recipient_email,
    )

    mock_message.dynamic_template_data = sample_payload
    mock_message.template_id = template_id

    mocked_api_client.assert_called_with(mock_message)


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_account_confirmation_email_task(
    mocked_send_email, customer_user, sendgrid_email_plugin
):
    template_id = "ABC1"
    recipient_email = "admin@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }

    plugin = sendgrid_email_plugin(
        api_key="AB12", account_confirmation_template_id=template_id
    )

    send_account_confirmation_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_password_reset_email_task(
    mocked_send_email, customer_user, sendgrid_email_plugin
):
    template_id = "ABC1"
    recipient_email = "admin@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        account_password_reset_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_password_reset_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )
    event = CustomerEvent.objects.get()
    assert event.type == CustomerEvents.PASSWORD_RESET_LINK_SENT
    assert event.user == customer_user


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_request_email_change_email_task(
    mocked_send_email, customer_user, sendgrid_email_plugin
):
    template_id = "ABC1"
    token = "token123"
    recipient_email = "user@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "redirect_url": f"http://localhost:8000/redirect{token}",
        "old_email": "old.user@example.com",
        "new_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        account_change_email_request_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_request_email_change_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )
    event = CustomerEvent.objects.get()
    assert event.type == CustomerEvents.EMAIL_CHANGE_REQUEST
    assert event.user == customer_user
    assert event.parameters == {
        "old_email": payload["old_email"],
        "new_email": payload["recipient_email"],
    }


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_user_change_email_notification_task(
    mocked_send_email, customer_user, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "old_email": "old.admin@example.com",
        "new_email": recipient_email,
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        account_change_email_confirm_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_user_change_email_notification_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )
    event = CustomerEvent.objects.get()
    assert event.type == CustomerEvents.EMAIL_CHANGED
    assert event.user == customer_user
    assert event.parameters == {
        "old_email": payload["old_email"],
        "new_email": payload["recipient_email"],
    }


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_account_delete_confirmation_email_task(
    mocked_send_email, customer_user, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "delete_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        account_delete_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_account_delete_confirmation_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_set_user_password_email_task(
    mocked_send_email, customer_user, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "password_set_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        account_set_customer_password_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_set_user_password_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_invoice_email_task_by_user(
    mocked_send_email, staff_user, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    invoice = Invoice.objects.create(order=order)
    recipient_email = "user@example.com"
    payload = {
        "invoice": {
            "id": to_global_id_or_none(invoice),
            "order_id": to_global_id_or_none(order),
            "number": 999,
            "download_url": "http://localhost:8000/download",
        },
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": to_global_id_or_none(staff_user),
        "requester_app_id": None,
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        invoice_ready_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_invoice_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )
    invoice_event = InvoiceEvent.objects.get()
    assert invoice_event.type == InvoiceEvents.SENT
    assert not invoice_event.app
    assert invoice_event.user == staff_user

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.INVOICE_SENT
    assert order_event.user == staff_user
    assert not order_event.app


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_invoice_email_task_by_app(
    mocked_send_email, app, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    invoice = Invoice.objects.create(order=order)
    recipient_email = "user@example.com"
    payload = {
        "invoice": {
            "id": to_global_id_or_none(invoice),
            "order_id": to_global_id_or_none(order),
            "number": 999,
            "download_url": "http://localhost:8000/download",
        },
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": None,
        "requester_app_id": to_global_id_or_none(app),
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        invoice_ready_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_invoice_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )
    invoice_event = InvoiceEvent.objects.get()
    assert invoice_event.type == InvoiceEvents.SENT
    assert invoice_event.app == app
    assert not invoice_event.user

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.INVOICE_SENT
    assert order_event.app == app
    assert not order_event.user


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_order_confirmation_email_task(
    mocked_send_email, staff_user, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_confirmation_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_order_confirmation_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert order_event.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.ORDER_CONFIRMATION,
    }


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_fulfillment_confirmation_email_task_by_user(
    mocked_send_email, staff_user, fulfillment, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    payload = get_default_fulfillment_payload(order, fulfillment)
    payload["requester_user_id"] = to_global_id_or_none(staff_user)
    payload["requester_app_id"] = None

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_fulfillment_confirmation_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_fulfillment_confirmation_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert order_event.user == staff_user
    assert not order_event.app
    assert order_event.parameters == {
        "email": order.user_email,
        "email_type": OrderEventsEmails.FULFILLMENT,
    }


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_fulfillment_confirmation_email_task_by_app(
    mocked_send_email, app, fulfillment, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    payload = get_default_fulfillment_payload(order, fulfillment)
    payload["requester_user_id"] = None
    payload["requester_app_id"] = to_global_id_or_none(app)

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_fulfillment_confirmation_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_fulfillment_confirmation_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert not order_event.user
    assert order_event.app == app
    assert order_event.parameters == {
        "email": order.user_email,
        "email_type": OrderEventsEmails.FULFILLMENT,
    }


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_fulfillment_update_email_task(
    mocked_send_email, staff_user, fulfillment, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    payload = get_default_fulfillment_payload(order, fulfillment)

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_fulfillment_update_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_fulfillment_update_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_payment_confirmation_email_task(
    mocked_send_email, payment_dummy, staff_user, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
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

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_payment_confirmation_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_payment_confirmation_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert order_event.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.PAYMENT,
    }


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_order_canceled_email_task_by_user(
    mocked_send_email, staff_user, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": to_global_id_or_none(staff_user),
        "requester_app_id": None,
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_canceled_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_order_canceled_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert order_event.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.ORDER_CANCEL,
    }
    assert not order_event.app
    assert order_event.user == staff_user


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_order_canceled_email_task_by_app(
    mocked_send_email, app, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": None,
        "requester_app_id": to_global_id_or_none(app),
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_canceled_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_order_canceled_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert order_event.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.ORDER_CANCEL,
    }
    assert not order_event.user
    assert order_event.app == app


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_order_refund_email_task_by_user(
    mocked_send_email, staff_user, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "amount": order.total_gross_amount,
        "currency": order.currency,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": to_global_id_or_none(staff_user),
        "requester_app_id": None,
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_refund_confirmation_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_order_refund_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert order_event.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.ORDER_REFUND,
    }
    assert not order_event.app
    assert order_event.user == staff_user


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_order_refund_email_task_by_app(
    mocked_send_email, app, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "amount": order.total_gross_amount,
        "currency": order.currency,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": None,
        "requester_app_id": to_global_id_or_none(app),
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_refund_confirmation_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_order_refund_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert order_event.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.ORDER_REFUND,
    }
    assert not order_event.user
    assert order_event.app == app


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_gift_card_email_task_by_user(
    mocked_send_email, staff_user, gift_card, sendgrid_email_plugin
):
    template_id = "ABC1"
    recipient_email = "user@example.com"

    payload = {
        "user": get_default_user_payload(staff_user),
        "requester_user_id": to_global_id_or_none(staff_user),
        "requester_app_id": None,
        "recipient_email": recipient_email,
        "resending": False,
        "gift_card": {
            "id": to_global_id_or_none(gift_card),
            "code": gift_card.code,
            "balance": gift_card.current_balance_amount,
            "currency": gift_card.currency,
        },
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        send_gift_card_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_gift_card_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    gift_card_event = GiftCardEvent.objects.get()
    assert gift_card_event.type == GiftCardEvents.SENT_TO_CUSTOMER
    assert gift_card_event.parameters == {
        "email": recipient_email,
    }
    assert gift_card_event.user == staff_user
    assert not gift_card_event.app


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_gift_card_email_task_by_user_resending(
    mocked_send_email, staff_user, gift_card, sendgrid_email_plugin
):
    template_id = "ABC1"
    recipient_email = "user@example.com"

    payload = {
        "user": get_default_user_payload(staff_user),
        "requester_user_id": to_global_id_or_none(staff_user),
        "requester_app_id": None,
        "recipient_email": recipient_email,
        "resending": True,
        "gift_card": {
            "id": to_global_id_or_none(gift_card),
            "code": gift_card.code,
            "balance": gift_card.current_balance_amount,
            "currency": gift_card.currency,
        },
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        send_gift_card_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_gift_card_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    gift_card_event = GiftCardEvent.objects.get()
    assert gift_card_event.type == GiftCardEvents.RESENT
    assert gift_card_event.parameters == {
        "email": recipient_email,
    }
    assert gift_card_event.user == staff_user
    assert not gift_card_event.app


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_gift_card_email_task_by_app(
    mocked_send_email, app, gift_card, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "user": None,
        "requester_user_id": None,
        "requester_app_id": to_global_id_or_none(app),
        "recipient_email": recipient_email,
        "resending": False,
        "gift_card": {
            "id": to_global_id_or_none(gift_card),
            "code": gift_card.code,
            "balance": gift_card.current_balance_amount,
            "currency": gift_card.currency,
        },
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        send_gift_card_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_gift_card_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    gift_card_event = GiftCardEvent.objects.get()
    assert gift_card_event.type == GiftCardEvents.SENT_TO_CUSTOMER
    assert gift_card_event.parameters == {
        "email": recipient_email,
    }
    assert not gift_card_event.user
    assert gift_card_event.app == app


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_order_confirmed_email_task_by_user(
    mocked_send_email, staff_user, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "amount": order.total_gross_amount,
        "currency": order.currency,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": to_global_id_or_none(staff_user),
        "requester_app_id": None,
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_confirmed_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_order_confirmed_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert order_event.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.CONFIRMED,
    }
    assert order_event.user == staff_user
    assert not order_event.app


@patch("saleor.plugins.sendgrid.tasks.send_email")
def test_send_order_confirmed_email_task_by_app(
    mocked_send_email, app, order, sendgrid_email_plugin
):
    template_id = "ABC1"

    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "amount": order.total_gross_amount,
        "currency": order.currency,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": None,
        "requester_app_id": to_global_id_or_none(app),
    }

    plugin = sendgrid_email_plugin(
        api_key="A12",
        order_confirmed_template_id=template_id,
        sender_name="Sender Name",
        sender_address="sender@example.com",
    )

    send_order_confirmed_email_task(payload, asdict(plugin.config))

    mocked_send_email.assert_called_with(
        configuration=plugin.config,
        template_id=template_id,
        payload=payload,
    )

    order_event = OrderEvent.objects.get()
    assert order_event.type == OrderEvents.EMAIL_SENT
    assert order_event.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.CONFIRMED,
    }
    assert not order_event.user
    assert order_event.app == app

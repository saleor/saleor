import datetime
import json
from typing import NamedTuple
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils import timezone
from requests import RequestException, TooManyRedirects
from requests_hardened import HTTPSession

from ....app.models import App
from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from ....payment import PaymentError, TransactionKind
from ....payment.interface import PaymentGateway
from ....payment.utils import create_payment_information
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.models import Webhook, WebhookEvent
from ....webhook.transport import signature_for_payload
from ....webhook.transport.payment import (
    parse_list_payment_gateways_response,
    parse_payment_action_response,
)
from ....webhook.transport.synchronous.transport import (
    send_webhook_request_sync,
    trigger_webhook_sync,
)
from ....webhook.transport.utils import (
    from_payment_app_id,
    to_payment_app_id,
)
from .utils import generate_request_headers


@pytest.fixture
def payment_invalid_app(payment_dummy):
    app = App.objects.create(name="Dummy app", is_active=True)
    gateway_id = "credit-card"
    gateway = to_payment_app_id(app, gateway_id)
    payment_dummy.gateway = gateway
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def payment_removed_app(payment_dummy):
    app = App.objects.create(
        name="Dummy app", is_active=True, removed_at=timezone.now()
    )
    gateway_id = "credit-card"
    gateway = to_payment_app_id(app, gateway_id)
    payment_dummy.gateway = gateway
    payment_dummy.save()
    return payment_dummy


class WebhookTestData(NamedTuple):
    secret: str
    event_type: WebhookEventAsyncType
    data: str
    message: bytes


@pytest.fixture
def webhook_data():
    secret = "secret"
    event_type = WebhookEventAsyncType.ANY
    data = json.dumps({"key": "value"})
    message = data.encode("utf-8")
    return WebhookTestData(secret, event_type, data, message)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_webhook_sync(mock_request, payment_app):
    data = '{"key": "value"}'
    trigger_webhook_sync(
        WebhookEventSyncType.PAYMENT_CAPTURE, data, payment_app.webhooks.first(), False
    )
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()


@mock.patch(
    "saleor.webhook.transport.synchronous.transport.create_delivery_for_subscription_sync_event"
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_webhook_sync_with_subscription(
    mock_request,
    mock_delivery_create,
    payment,
    payment_app_with_subscription_webhooks,
):
    payment_app = payment_app_with_subscription_webhooks
    data = '{"key": "value"}'
    fake_delivery = "fake_delivery"
    mock_delivery_create.return_value = fake_delivery
    trigger_webhook_sync(
        WebhookEventSyncType.PAYMENT_CAPTURE,
        data,
        payment_app.webhooks.first(),
        False,
        payment,
    )
    mock_request.assert_called_once_with(fake_delivery)


@mock.patch(
    "saleor.webhook.transport.synchronous.transport.observability.report_event_delivery_attempt"
)
@mock.patch.object(HTTPSession, "request")
def test_send_webhook_request_sync_failed_attempt(
    mock_post, mock_observability, app, event_delivery
):
    # given
    expected_data = {
        "content": '{"key": "response_text"}',
        "headers": {"header_key": "header_val"},
        "status_code": 500,
        "duration": datetime.timedelta(seconds=2),
    }
    mock_post().ok = False
    mock_post().text = expected_data["content"]
    mock_post().headers = expected_data["headers"]
    mock_post().status_code = expected_data["status_code"]
    mock_post().elapsed = expected_data["duration"]
    # when
    response_data = send_webhook_request_sync(event_delivery)
    attempt = EventDeliveryAttempt.objects.first()

    # then
    assert event_delivery.status == EventDeliveryStatus.FAILED
    assert attempt.status == EventDeliveryStatus.FAILED
    assert attempt.duration == expected_data["duration"].total_seconds()
    assert attempt.response == expected_data["content"]
    assert attempt.response_headers == json.dumps(expected_data["headers"])
    assert attempt.response_status_code == expected_data["status_code"]
    assert response_data is None
    mock_observability.assert_called_once_with(attempt)


@mock.patch("saleor.webhook.observability.report_event_delivery_attempt")
@mock.patch.object(HTTPSession, "request")
@mock.patch("saleor.webhook.transport.synchronous.transport.clear_successful_delivery")
def test_send_webhook_request_sync_successful_attempt(
    mock_clear_delivery, mock_post, mock_observability, app, event_delivery
):
    # given
    expected_data = {
        "content": '{"key": "response_text"}',
        "headers": {"header_key": "header_val"},
        "status_code": 200,
        "duration": datetime.timedelta(seconds=2),
    }
    mock_post().ok = True
    mock_post().text = expected_data["content"]
    mock_post().headers = expected_data["headers"]
    mock_post().status_code = expected_data["status_code"]
    mock_post().elapsed = expected_data["duration"]
    # when
    response_data = send_webhook_request_sync(event_delivery)

    # then
    mock_clear_delivery.assert_called_once_with(event_delivery)
    mock_observability.assert_called_once()
    assert not EventDeliveryAttempt.objects.exists()

    attempt = mock_observability.mock_calls[0].args[0]
    assert event_delivery.status == EventDeliveryStatus.SUCCESS
    assert attempt.status == EventDeliveryStatus.SUCCESS
    assert attempt.duration == expected_data["duration"].total_seconds()
    assert attempt.response == expected_data["content"]
    assert attempt.response_headers == json.dumps(expected_data["headers"])
    assert attempt.response_status_code == expected_data["status_code"]
    assert response_data == json.loads(expected_data["content"])
    mock_observability.assert_called_once_with(attempt)


@mock.patch("saleor.webhook.observability.report_event_delivery_attempt")
@mock.patch.object(HTTPSession, "request", side_effect=RequestException)
def test_send_webhook_request_sync_request_exception(
    mock_post, mock_observability, app, event_delivery
):
    # given
    event_payload = event_delivery.payload
    data = event_payload.get_payload()
    webhook = event_delivery.webhook
    domain = Site.objects.get_current().domain
    message = data.encode("utf-8")
    signature = signature_for_payload(message, webhook.secret_key)
    expected_request_headers = generate_request_headers(
        event_delivery.event_type, domain, signature
    )

    # when
    response_data = send_webhook_request_sync(event_delivery)
    attempt = EventDeliveryAttempt.objects.first()

    # then
    assert event_delivery.status == "failed"
    assert attempt.status == "failed"
    assert attempt.duration == 0.0
    assert attempt.response == ""
    assert attempt.response_headers == "null"
    assert attempt.response_status_code is None
    assert json.loads(attempt.request_headers) == expected_request_headers
    assert response_data is None
    mock_observability.assert_called_once_with(attempt)


@mock.patch("saleor.webhook.observability.report_event_delivery_attempt")
@mock.patch.object(HTTPSession, "request")
def test_send_webhook_request_sync_when_exception_with_response(
    mock_post, mock_observability, app, event_delivery
):
    mock_response = mock.Mock()
    mock_response.text = "response_content"
    mock_response.headers = {"response": "headers"}
    mock_response.status_code = 302
    mock_post.side_effect = TooManyRedirects(response=mock_response)
    # when
    send_webhook_request_sync(event_delivery)
    attempt = EventDeliveryAttempt.objects.first()

    # then
    assert attempt.response == "response_content"
    assert attempt.response_headers == '{"response": "headers"}'
    assert attempt.response_status_code == 302
    mock_observability.assert_called_once_with(attempt)


@mock.patch("saleor.webhook.observability.report_event_delivery_attempt")
@mock.patch.object(HTTPSession, "request")
def test_send_webhook_request_sync_json_parsing_error(
    mock_post, mock_observability, app, event_delivery
):
    # given
    expected_data = {
        "incorrect_content": "{key: response}",
        "response_headers": {"header_key": "header_val"},
        "duration": datetime.timedelta(seconds=2),
        "status_code": 200,
    }
    mock_post().text = expected_data["incorrect_content"]
    mock_post().headers = expected_data["response_headers"]
    mock_post().elapsed = expected_data["duration"]
    mock_post().status_code = expected_data["status_code"]

    # when
    response_data = send_webhook_request_sync(event_delivery)
    attempt = EventDeliveryAttempt.objects.first()

    # then
    assert event_delivery.status == "failed"
    assert attempt.status == "failed"
    assert attempt.duration == expected_data["duration"].total_seconds()
    assert attempt.response == expected_data["incorrect_content"]
    assert attempt.response_headers == json.dumps(expected_data["response_headers"])
    assert attempt.response_status_code == expected_data["status_code"]
    assert response_data is None
    mock_observability.assert_called_once_with(attempt)


@mock.patch.object(HTTPSession, "request")
def test_send_webhook_request_with_proper_timeout(mock_post, event_delivery, app):
    mock_post().text = '{"key": "response_text"}'
    mock_post().headers = {"header_key": "header_val"}
    mock_post().elapsed = datetime.timedelta(seconds=1)
    mock_post().status_code = 200
    send_webhook_request_sync(event_delivery)
    assert mock_post.call_args.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT


def test_send_webhook_request_sync_invalid_scheme(webhook, app):
    target_url = "gcpubsub://cloud.google.com/projects/saleor/topics/test"
    event_payload = EventPayload.objects.create_with_payload_file(
        payload="fake_content"
    )
    webhook.target_url = target_url
    webhook.save()
    delivery = EventDelivery.objects.create(
        status="pending",
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )
    with pytest.raises(ValueError, match="Unknown webhook scheme"):
        send_webhook_request_sync(delivery)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_payment_gateways(
    mock_send_request, payment_app, permission_manage_payments, webhook_plugin
):
    # Create second app to test results from multiple apps.
    app_2 = App.objects.create(name="Payment App 2", is_active=True)
    app_2.tokens.create(name="Default")
    app_2.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="payment-webhook-2",
        app=app_2,
        target_url="https://payment-gateway-2.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in WebhookEventSyncType.PAYMENT_EVENTS
        ]
    )

    plugin = webhook_plugin()
    mock_json_response = [
        {
            "id": "credit-card",
            "name": "Credit Card",
            "currencies": ["USD", "EUR"],
            "config": [],
        }
    ]
    mock_send_request.return_value = mock_json_response
    response_data = plugin.get_payment_gateways("USD", None, None, None)
    expected_response_1 = parse_list_payment_gateways_response(
        mock_json_response, payment_app
    )
    expected_response_2 = parse_list_payment_gateways_response(
        mock_json_response, app_2
    )
    assert len(response_data) == 2
    assert response_data[0] == expected_response_1[0]
    assert response_data[1] == expected_response_2[0]


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_payment_gateways_with_transactions(
    mock_send_request, permission_manage_payments, webhook_plugin
):
    # given
    app_name = "Payment App 2"
    app_identifier = "app2"
    app = App.objects.create(name=app_name, is_active=True, identifier=app_identifier)
    app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="payment-webhook-2",
        app=app,
        target_url="https://payment-gateway-2.com/api/",
    )
    WebhookEvent.objects.create(
        event_type=WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION, webhook=webhook
    )

    plugin = webhook_plugin()

    # when
    response_data = plugin.get_payment_gateways("USD", None, None, None)

    # then
    assert len(response_data) == 1
    assert response_data[0] == PaymentGateway(
        id=app_identifier, name=app_name, currencies=["USD"], config=[]
    )
    assert not mock_send_request.called


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_payment_gateways_with_transactions_and_app_without_identifier(
    mock_send_request, permission_manage_payments, webhook_plugin
):
    # given
    app_name = "Payment App 2"
    app_identifier = ""
    app = App.objects.create(name=app_name, is_active=True, identifier=app_identifier)
    app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="payment-webhook-2",
        app=app,
        target_url="https://payment-gateway-2.com/api/",
    )
    WebhookEvent.objects.create(
        event_type=WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION, webhook=webhook
    )

    plugin = webhook_plugin()

    # when
    response_data = plugin.get_payment_gateways("USD", None, None, None)

    # then
    assert len(response_data) == 0


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_payment_gateways_multiple_webhooks_in_the_same_app(
    mock_send_request, payment_app, permission_manage_payments, webhook_plugin
):
    # given
    # create the second webhook with the same event
    webhook = Webhook.objects.create(
        name="payment-webhook-2",
        app=payment_app,
        target_url="https://payment-gateway-2.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in WebhookEventSyncType.PAYMENT_EVENTS
        ]
    )

    plugin = webhook_plugin()
    mock_json_response = [
        {
            "id": "credit-card",
            "name": "Credit Card",
            "currencies": ["USD", "EUR"],
            "config": [],
        }
    ]
    mock_send_request.return_value = mock_json_response

    # when
    response_data = plugin.get_payment_gateways("USD", None, None, None)

    # then
    expected_response_1 = parse_list_payment_gateways_response(
        mock_json_response, payment_app
    )
    expected_response_2 = parse_list_payment_gateways_response(
        mock_json_response, payment_app
    )
    assert len(response_data) == 2
    assert response_data[0] == expected_response_1[0]
    assert response_data[1] == expected_response_2[0]


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_payment_gateways_filters_out_unsupported_currencies(
    mock_send_request, payment_app, webhook_plugin
):
    plugin = webhook_plugin()
    mock_json_response = [
        {
            "id": "credit-card",
            "name": "Credit Card",
            "currencies": ["USD", "EUR"],
            "config": [],
        }
    ]
    mock_send_request.return_value = mock_json_response
    response_data = plugin.get_payment_gateways("PLN", None, None, None)
    assert response_data == []


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch("saleor.plugins.webhook.plugin.generate_list_gateways_payload")
def test_get_payment_gateways_for_checkout(
    mock_generate_payload, mock_send_request, checkout_info, payment_app, webhook_plugin
):
    plugin = webhook_plugin()
    mock_json_response = [
        {
            "id": "credit-card",
            "name": "Credit Card",
            "currencies": ["USD", "EUR"],
            "config": [],
        }
    ]
    mock_send_request.return_value = mock_json_response
    mock_generate_payload.return_value = ""
    plugin.get_payment_gateways("USD", checkout_info, None, None)
    assert mock_generate_payload.call_args[0][1] == checkout_info.checkout


@pytest.mark.parametrize(
    ("txn_kind", "plugin_func_name"),
    [
        (TransactionKind.AUTH, "authorize_payment"),
        (TransactionKind.CAPTURE, "capture_payment"),
        (TransactionKind.REFUND, "refund_payment"),
        (TransactionKind.VOID, "void_payment"),
        (TransactionKind.CONFIRM, "confirm_payment"),
        (TransactionKind.CAPTURE, "process_payment"),
    ],
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_run_payment_webhook(
    mock_send_request,
    txn_kind,
    plugin_func_name,
    payment,
    payment_app,
    webhook_plugin,
):
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment, "token")
    payment_func = getattr(plugin, plugin_func_name)

    mock_json_response = {"transaction_id": f"fake-id-{txn_kind}"}
    mock_send_request.return_value = mock_json_response
    response_data = payment_func(payment_information, None)

    expected_response = parse_payment_action_response(
        payment_information, mock_json_response, txn_kind
    )
    assert response_data == expected_response


def test_run_payment_webhook_invalid_app(payment_invalid_app, webhook_plugin):
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment_invalid_app, "token")
    with pytest.raises(PaymentError):
        plugin._WebhookPlugin__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            None,
        )


def test_run_payment_webhook_removed_app_by_id(payment_removed_app, webhook_plugin):
    # given
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment_removed_app, "token")

    # when
    with pytest.raises(PaymentError):
        plugin._WebhookPlugin__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            None,
        )


def test_run_payment_webhook_removed_app_by_app_identifier(
    payment, payment_app, webhook_plugin
):
    # given
    payment_app.removed_at = timezone.now()
    payment_app.save(update_fields=["removed_at"])
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment, "token")
    payment_data = from_payment_app_id(payment_information.gateway)
    assert payment_data.app_identifier == payment_app.identifier

    # when
    with pytest.raises(PaymentError):
        plugin._WebhookPlugin__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            None,
        )


def test_run_payment_webhook_no_payment_app_data(payment, webhook_plugin):
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment, "token")
    payment_information.gateway = "dummy"
    with pytest.raises(PaymentError):
        plugin._WebhookPlugin__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            None,
        )


def test_run_payment_webhook_inactive_plugin(payment, webhook_plugin):
    plugin = webhook_plugin()
    plugin.active = False
    payment_information = create_payment_information(payment, "token")
    dummy_previous_value = {"key": "dummy"}
    response = plugin._WebhookPlugin__run_payment_webhook(
        WebhookEventSyncType.PAYMENT_AUTHORIZE,
        TransactionKind.AUTH,
        payment_information,
        dummy_previous_value,
    )
    assert response == dummy_previous_value


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_run_payment_webhook_no_response(mock_send_request, payment, webhook_plugin):
    # Should raise and error when response data is None.
    mock_send_request.return_value = None
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment, "token")
    with pytest.raises(PaymentError):
        plugin._WebhookPlugin__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            {},
        )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_run_payment_webhook_empty_response(mock_send_request, payment, webhook_plugin):
    # Empty JSON response "{}"" is accepted; check that it doesn't fail.
    mock_send_request.return_value = {}
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment, "token")
    response = plugin._WebhookPlugin__run_payment_webhook(
        WebhookEventSyncType.PAYMENT_AUTHORIZE,
        TransactionKind.AUTH,
        payment_information,
        {},
    )
    assert response
    assert response.is_success


def test_check_plugin_id(payment_app, webhook_plugin):
    plugin = webhook_plugin()
    assert not plugin.check_plugin_id("dummy")
    valid_id = to_payment_app_id(payment_app, "credit-card")
    assert plugin.check_plugin_id(valid_id)


def test_webhook_plugin_token_is_not_required(webhook_plugin):
    plugin = webhook_plugin()
    assert not plugin.token_is_required_as_payment_input(None)

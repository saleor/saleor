import datetime
import json
from collections import namedtuple
from unittest import mock

import pytest
from django.conf import settings
from requests import RequestException, TooManyRedirects

from ....app.models import App
from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from ....payment import PaymentError, TransactionKind
from ....payment.utils import create_payment_information
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.models import Webhook, WebhookEvent
from ..tasks import send_webhook_request_sync, trigger_webhook_sync
from ..utils import (
    parse_list_payment_gateways_response,
    parse_payment_action_response,
    to_payment_app_id,
)


@pytest.fixture
def payment_invalid_app(payment_dummy):
    app = App.objects.create(name="Dummy app", is_active=True)
    gateway_id = "credit-card"
    gateway = to_payment_app_id(app, gateway_id)
    payment_dummy.gateway = gateway
    payment_dummy.save()
    return payment_dummy


WebhookTestData = namedtuple("WebhookTestData", "secret, event_type, data, message")


@pytest.fixture
def webhook_data():
    secret = "secret"
    event_type = WebhookEventAsyncType.ANY
    data = json.dumps({"key": "value"})
    message = data.encode("utf-8")
    return WebhookTestData(secret, event_type, data, message)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_webhook_sync(mock_request, payment_app):
    data = '{"key": "value"}'
    trigger_webhook_sync(WebhookEventSyncType.PAYMENT_CAPTURE, data, payment_app)
    event_delivery = EventDelivery.objects.first()
    mock_request.assert_called_once_with(payment_app.name, event_delivery)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_webhook_sync_use_first_webhook(mock_request, payment_app):
    webhook_1 = payment_app.webhooks.first()

    # create additional webhook for the same event; check that always the first one will
    # be used if there are multiple webhooks for the same event.
    webhook_2 = Webhook.objects.create(
        app=payment_app,
        name="payment-webhook-2",
        target_url="https://dont-use-this-gateway.com/api/",
    )
    webhook_2.events.create(event_type=WebhookEventSyncType.PAYMENT_CAPTURE)

    data = '{"key": "value"}'
    trigger_webhook_sync(WebhookEventSyncType.PAYMENT_CAPTURE, data, payment_app)
    event_delivery = EventDelivery.objects.first()
    mock_request.assert_called_once_with(payment_app.name, event_delivery)

    assert event_delivery.webhook.target_url == webhook_1.target_url
    assert event_delivery.webhook.secret_key == webhook_1.secret_key


def test_trigger_webhook_sync_no_webhook_available():
    app = App.objects.create(name="Dummy app", is_active=True)
    # should raise an error for app with no payment webhooks
    with pytest.raises(PaymentError):
        trigger_webhook_sync(WebhookEventSyncType.PAYMENT_REFUND, {}, app)


@mock.patch("saleor.plugins.webhook.tasks.observability.report_event_delivery_attempt")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
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
    response_data = send_webhook_request_sync(app.name, event_delivery)
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


@mock.patch("saleor.plugins.webhook.tasks.observability.report_event_delivery_attempt")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
@mock.patch("saleor.plugins.webhook.tasks.clear_successful_delivery")
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
    response_data = send_webhook_request_sync(app.name, event_delivery)

    attempt = EventDeliveryAttempt.objects.first()

    # then
    mock_clear_delivery.assert_called_once_with(event_delivery)
    assert event_delivery.status == EventDeliveryStatus.SUCCESS
    assert attempt.status == EventDeliveryStatus.SUCCESS
    assert attempt.duration == expected_data["duration"].total_seconds()
    assert attempt.response == expected_data["content"]
    assert attempt.response_headers == json.dumps(expected_data["headers"])
    assert attempt.response_status_code == expected_data["status_code"]
    assert response_data == json.loads(expected_data["content"])
    mock_observability.assert_called_once_with(attempt)


@mock.patch("saleor.plugins.webhook.tasks.observability.report_event_delivery_attempt")
@mock.patch("saleor.plugins.webhook.tasks.requests.post", side_effect=RequestException)
def test_send_webhook_request_sync_request_exception(
    mock_post, mock_observability, app, event_delivery
):
    # when
    response_data = send_webhook_request_sync(app.name, event_delivery)
    attempt = EventDeliveryAttempt.objects.first()

    # then
    assert event_delivery.status == "failed"
    assert attempt.status == "failed"
    assert attempt.duration == 0.0
    assert attempt.response == ""
    assert attempt.response_headers == "null"
    assert attempt.response_status_code is None
    assert attempt.request_headers == "null"
    assert response_data is None
    mock_observability.assert_called_once_with(attempt)


@mock.patch("saleor.plugins.webhook.tasks.observability.report_event_delivery_attempt")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
def test_send_webhook_request_sync_when_exception_with_response(
    mock_post, mock_observability, app, event_delivery
):
    mock_response = mock.Mock()
    mock_response.text = "response_content"
    mock_response.headers = {"response": "headers"}
    mock_response.status_code = 302
    mock_post.side_effect = TooManyRedirects(response=mock_response)
    # when
    send_webhook_request_sync(app.name, event_delivery)
    attempt = EventDeliveryAttempt.objects.first()

    # then
    assert attempt.response == "response_content"
    assert attempt.response_headers == '{"response": "headers"}'
    assert attempt.response_status_code == 302
    mock_observability.assert_called_once_with(attempt)


@mock.patch("saleor.plugins.webhook.tasks.observability.report_event_delivery_attempt")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
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
    response_data = send_webhook_request_sync(app.name, event_delivery)
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


@mock.patch("saleor.plugins.webhook.tasks.requests.post")
def test_send_webhook_request_with_proper_timeout(mock_post, event_delivery, app):
    mock_post().text = '{"key": "response_text"}'
    mock_post().headers = {"header_key": "header_val"}
    mock_post().elapsed = datetime.timedelta(seconds=1)
    mock_post().status_code = 200
    send_webhook_request_sync(app.name, event_delivery)
    assert mock_post.call_args.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT


def test_send_webhook_request_sync_invalid_scheme(webhook, app):
    with pytest.raises(ValueError):
        target_url = "gcpubsub://cloud.google.com/projects/saleor/topics/test"
        event_payload = EventPayload.objects.create(payload="fake_content")
        webhook.target_url = target_url
        webhook.save()
        delivery = EventDelivery.objects.create(
            status="pending",
            event_type=WebhookEventAsyncType.ANY,
            payload=event_payload,
            webhook=webhook,
        )
        send_webhook_request_sync(app.name, delivery)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
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
    response_data = plugin.get_payment_gateways("USD", None, None)
    expected_response_1 = parse_list_payment_gateways_response(
        mock_json_response, payment_app
    )
    expected_response_2 = parse_list_payment_gateways_response(
        mock_json_response, app_2
    )
    assert len(response_data) == 2
    assert response_data[0] == expected_response_1[0]
    assert response_data[1] == expected_response_2[0]


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
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
    response_data = plugin.get_payment_gateways("PLN", None, None)
    assert response_data == []


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
@mock.patch("saleor.plugins.webhook.plugin.generate_list_gateways_payload")
def test_get_payment_gateways_for_checkout(
    mock_generate_payload, mock_send_request, checkout, payment_app, webhook_plugin
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
    plugin.get_payment_gateways("USD", checkout, None)
    assert mock_generate_payload.call_args[0][1] == checkout


@pytest.mark.parametrize(
    "txn_kind, plugin_func_name",
    (
        (TransactionKind.AUTH, "authorize_payment"),
        (TransactionKind.CAPTURE, "capture_payment"),
        (TransactionKind.REFUND, "refund_payment"),
        (TransactionKind.VOID, "void_payment"),
        (TransactionKind.CONFIRM, "confirm_payment"),
        (TransactionKind.CAPTURE, "process_payment"),
    ),
)
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
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

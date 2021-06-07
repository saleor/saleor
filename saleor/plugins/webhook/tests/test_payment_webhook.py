import json
from unittest import mock

import pytest

from ....app.models import App
from ....payment import PaymentError, TransactionKind
from ....payment.utils import create_payment_information
from ....webhook.event_types import WebhookEventType
from ....webhook.models import Webhook, WebhookEvent
from ...manager import get_plugins_manager
from ..tasks import (
    send_webhook_request_sync,
    signature_for_payload,
    trigger_webhook_sync,
)
from ..utils import (
    parse_list_payment_gateways_response,
    parse_payment_action_response,
    to_payment_app_id,
)


@pytest.fixture
def payment(payment_dummy, payment_app):
    gateway_id = "credit-card"
    gateway = to_payment_app_id(payment_app, gateway_id)
    payment_dummy.gateway = gateway
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def payment_invalid_app(payment_dummy):
    app = App.objects.create(name="Dummy app", is_active=True)
    gateway_id = "credit-card"
    gateway = to_payment_app_id(app, gateway_id)
    payment_dummy.gateway = gateway
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def webhook_plugin(settings):
    def factory():
        settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
        manager = get_plugins_manager()
        return manager.global_plugins[0]

    return factory


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_webhook_sync(mock_request, payment_app):
    data = {"key": "value"}
    trigger_webhook_sync(WebhookEventType.PAYMENT_CAPTURE, data, payment_app)
    webhook = payment_app.webhooks.first()
    mock_request.assert_called_once_with(
        webhook.target_url,
        webhook.secret_key,
        WebhookEventType.PAYMENT_CAPTURE,
        data,
    )


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
    webhook_2.events.create(event_type=WebhookEventType.PAYMENT_CAPTURE)

    data = {"key": "value"}
    trigger_webhook_sync(WebhookEventType.PAYMENT_CAPTURE, data, payment_app)
    mock_request.assert_called_once_with(
        webhook_1.target_url,
        webhook_1.secret_key,
        WebhookEventType.PAYMENT_CAPTURE,
        data,
    )


def test_trigger_webhook_sync_no_webhook_available():
    app = App.objects.create(name="Dummy app", is_active=True)
    # should raise an error for app with no payment webhooks
    with pytest.raises(PaymentError):
        trigger_webhook_sync(WebhookEventType.PAYMENT_REFUND, {}, app)


@pytest.mark.parametrize(
    "target_url",
    ("http://payment-gateway.com/api/", "https://payment-gateway.com/api/"),
)
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_using_http")
def test_send_webhook_request_sync(mock_send_http, target_url, site_settings):
    secret = "secret"
    event_type = WebhookEventType.PAYMENT_CAPTURE
    data = json.dumps({"key": "value"})
    message = data.encode("utf-8")

    send_webhook_request_sync(target_url, secret, event_type, data)
    mock_send_http.assert_called_once_with(
        target_url,
        message,
        site_settings.site.domain,
        signature_for_payload(message, secret),
        event_type,
    )


def test_send_webhook_request_sync_invalid_scheme():
    with pytest.raises(ValueError):
        target_url = "gcpubsub://cloud.google.com/projects/saleor/topics/test"
        send_webhook_request_sync(target_url, "", "", "")


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
            for event_type in WebhookEventType.PAYMENT_EVENTS
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
            WebhookEventType.PAYMENT_AUTHORIZE,
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
            WebhookEventType.PAYMENT_AUTHORIZE,
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
        WebhookEventType.PAYMENT_AUTHORIZE,
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
            WebhookEventType.PAYMENT_AUTHORIZE,
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
        WebhookEventType.PAYMENT_AUTHORIZE,
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

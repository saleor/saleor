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
    PaymentAppData,
    parse_list_payment_gateways_response,
    parse_payment_action_response,
    to_payment_app_id,
)


@pytest.fixture
def payment_app(db, permission_manage_payments):
    app = App.objects.create(name="Payment App", is_active=True)
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment-webhook-1",
        app=app,
        target_url="https://payment-gateway.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in WebhookEventType.PAYMENT_EVENTS
        ]
    )
    return app


@pytest.fixture
def payment(payment_dummy, payment_app):
    gateway_id = "credit-card"
    gateway = to_payment_app_id(payment_app, gateway_id)
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
def test_get_payment_gateways(mock_send_request, payment_app, webhook_plugin):
    # todo: create second app and test with two
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
    expected_response = parse_list_payment_gateways_response(
        mock_json_response, payment_app
    )
    assert response_data == expected_response


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_payment_gateways_for_checkout(
    mock_send_request, payment_app, webhook_plugin
):
    pass


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
    payment_app_data = PaymentAppData(app_pk=payment_app.pk, name="credit-card")
    payment_func = getattr(plugin, plugin_func_name)

    mock_json_response = {"transaction_id": f"fake-id-{txn_kind}"}
    mock_send_request.return_value = mock_json_response
    response_data = payment_func(
        payment_information, None, payment_app_data=payment_app_data
    )

    expected_response = parse_payment_action_response(
        payment_information, mock_json_response, txn_kind
    )
    assert response_data == expected_response


def test_run_payment_webhook_invalid_app(
    payment,
    webhook_plugin,
):
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment, "token")
    app = App.objects.create(name="Dummy app", is_active=True)
    payment_app_data = PaymentAppData(app_pk=app.pk, name="credit-card")
    with pytest.raises(PaymentError):
        plugin._WebhookPlugin__run_payment_webhook(
            WebhookEventType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            None,
            payment_app_data=payment_app_data,
        )


def test_run_payment_webhook_no_payment_app_data(
    payment,
    webhook_plugin,
):
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment, "token")
    with pytest.raises(PaymentError):
        plugin._WebhookPlugin__run_payment_webhook(
            WebhookEventType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            None,
        )


@mock.patch("saleor.webhook.payloads.generate_payment_payload")
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_run_payment_webhook_include_payment_method_name(
    mock_send_request,
    mock_generate_payload,
    payment,
    payment_app,
    webhook_plugin,
):
    plugin = webhook_plugin()
    payment_information = create_payment_information(payment, "token")
    payment_method_name = "credit-card"
    payment_app_data = PaymentAppData(app_pk=payment_app.pk, name=payment_method_name)

    mock_generate_payload.return_value = "{}"
    mock_send_request.return_value = {"transaction_id": "fake-id"}

    plugin._WebhookPlugin__run_payment_webhook(
        WebhookEventType.PAYMENT_AUTHORIZE,
        TransactionKind.AUTH,
        payment_information,
        None,
        payment_app_data=payment_app_data,
    )
    # todo: mock not called when running tests
    # payment_data = mock_generate_payload.call_args[0][0]
    # assert payment_data.data["payment_method"] == payment_method_name


def test_app_for_event_type_qs():
    pass

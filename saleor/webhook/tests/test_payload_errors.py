import logging

import graphene
import pytest

from ...app.models import AppProblem
from ...core.models import EventDelivery
from ...graphql.webhook.subscription_payload import (
    generate_payload_from_subscription,
    generate_pre_save_payloads,
    initialize_request,
)
from ...tests.utils import get_metric_data, get_metric_data_point
from ..const import WebhookPayloadErrorReason
from ..event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..models import Webhook
from ..payload_errors import (
    get_invalid_subscription_query_problem_key,
    report_payload_generation_error,
)
from ..transport.asynchronous.transport import create_deliveries_for_subscriptions
from ..transport.metrics import METRIC_WEBHOOK_PAYLOAD_ERROR_COUNT
from ..transport.synchronous.transport import (
    create_delivery_for_subscription_sync_event,
)

# Mirrors the production failure: a query that validated when the app was installed and
# no longer does, because the field it selects was removed from the schema.
INVALID_ORDER_CREATED_QUERY = """
    subscription {
      event {
        ... on OrderCreated {
          order { id fieldRemovedInNewerVersion }
        }
      }
    }
"""
INVALID_QUERY_ERROR = (
    '[GraphQLError(\'Cannot query field "fieldRemovedInNewerVersion" '
    'on type "Order".\')]'
)

INVALID_SHIPPING_METHODS_QUERY = """
    subscription {
      event {
        ... on ShippingListMethodsForCheckout {
          checkout { id fieldRemovedInNewerVersion }
        }
      }
    }
"""


@pytest.fixture
def webhook_with_invalid_query(webhook_app):
    webhook = Webhook.objects.create(
        name="Order sync",
        identifier="order-sync",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=INVALID_ORDER_CREATED_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    return webhook


def expected_attributes(webhook, event_type, reason):
    return {
        "saleor.app.id": graphene.Node.to_global_id("App", webhook.app_id),
        "saleor.webhook.id": graphene.Node.to_global_id("Webhook", webhook.pk),
        "saleor.webhook.event_type": event_type,
        "error.type": reason.value,
    }


def recorded_payload_error(metrics_data):
    """Return the dropped-payload metric, or None when nothing at all was recorded."""
    if metrics_data is None:
        return None
    return get_metric_data(metrics_data, METRIC_WEBHOOK_PAYLOAD_ERROR_COUNT)


def expected_problem_message(webhook, event_type, error):
    return (
        f'Webhook "{webhook.name}" (identifier: {webhook.identifier}) has an invalid '
        f"subscription query and is not delivering any of its events. Detected while "
        f"dispatching {event_type}. GraphQL error: {error}"
    )


def test_invalid_subscription_query_drops_event_and_reports_problem(
    webhook_with_invalid_query,
    order,
    get_test_metrics_data,
    django_capture_on_commit_callbacks,
):
    # given
    webhook = webhook_with_invalid_query
    event_type = WebhookEventAsyncType.ORDER_CREATED
    assert AppProblem.objects.exists() is False

    # when
    with django_capture_on_commit_callbacks(execute=True):
        deliveries = create_deliveries_for_subscriptions(event_type, order, [webhook])

    # then
    assert deliveries == []
    assert EventDelivery.objects.exists() is False

    problem = AppProblem.objects.get()
    assert problem.app_id == webhook.app_id
    assert problem.key == get_invalid_subscription_query_problem_key(webhook.pk)
    assert problem.message == expected_problem_message(
        webhook, event_type, INVALID_QUERY_ERROR
    )
    assert problem.is_critical is True
    assert problem.count == 1

    data_point = get_metric_data_point(
        get_test_metrics_data(), METRIC_WEBHOOK_PAYLOAD_ERROR_COUNT
    )
    assert data_point.value == 1
    assert data_point.attributes == expected_attributes(
        webhook, event_type, WebhookPayloadErrorReason.INVALID_SUBSCRIPTION_QUERY
    )


def test_repeated_drops_report_one_problem_but_count_every_event(
    webhook_with_invalid_query,
    order,
    get_test_metrics_data,
    django_capture_on_commit_callbacks,
):
    # given
    webhook = webhook_with_invalid_query
    event_type = WebhookEventAsyncType.ORDER_CREATED

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_deliveries_for_subscriptions(event_type, order, [webhook])
        create_deliveries_for_subscriptions(event_type, order, [webhook])

    # then
    problem = AppProblem.objects.get()
    assert problem.count == 1

    data_point = get_metric_data_point(
        get_test_metrics_data(), METRIC_WEBHOOK_PAYLOAD_ERROR_COUNT
    )
    assert data_point.value == 2


def test_sync_event_with_invalid_query_drops_delivery_and_reports_problem(
    webhook_app,
    checkout_with_item,
    get_test_metrics_data,
    django_capture_on_commit_callbacks,
):
    # given
    event_type = WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    webhook = Webhook.objects.create(
        name="Shipping app",
        identifier="shipping-app",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=INVALID_SHIPPING_METHODS_QUERY,
    )
    webhook.events.create(event_type=event_type)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        delivery = create_delivery_for_subscription_sync_event(
            event_type, checkout_with_item, webhook
        )

    # then
    assert delivery is None
    assert EventDelivery.objects.exists() is False

    problem = AppProblem.objects.get()
    assert problem.key == get_invalid_subscription_query_problem_key(webhook.pk)
    assert problem.is_critical is True

    data_point = get_metric_data_point(
        get_test_metrics_data(), METRIC_WEBHOOK_PAYLOAD_ERROR_COUNT
    )
    assert data_point.value == 1
    assert data_point.attributes == expected_attributes(
        webhook, event_type, WebhookPayloadErrorReason.INVALID_SUBSCRIPTION_QUERY
    )


def test_empty_payload_records_metric_without_raising_problem(
    webhook_with_invalid_query,
    get_test_metrics_data,
    django_capture_on_commit_callbacks,
):
    """An empty payload can be a filterable subscription legitimately resolving to nothing."""
    # given
    webhook = webhook_with_invalid_query
    event_type = WebhookEventAsyncType.ORDER_CREATED

    # when
    with django_capture_on_commit_callbacks(execute=True):
        report_payload_generation_error(
            webhook, event_type, WebhookPayloadErrorReason.EMPTY_PAYLOAD
        )

    # then
    assert AppProblem.objects.exists() is False

    data_point = get_metric_data_point(
        get_test_metrics_data(), METRIC_WEBHOOK_PAYLOAD_ERROR_COUNT
    )
    assert data_point.value == 1
    assert data_point.attributes == expected_attributes(
        webhook, event_type, WebhookPayloadErrorReason.EMPTY_PAYLOAD
    )


def test_manually_triggered_webhook_does_not_report(
    webhook_with_invalid_query,
    order,
    get_test_metrics_data,
    django_capture_on_commit_callbacks,
):
    # given
    webhook = webhook_with_invalid_query
    event_type = WebhookEventAsyncType.ORDER_CREATED

    # when
    with django_capture_on_commit_callbacks(execute=True):
        deliveries = create_deliveries_for_subscriptions(
            event_type, order, [webhook], report_dropped_payloads=False
        )

    # then
    assert deliveries == []
    assert AppProblem.objects.exists() is False
    assert recorded_payload_error(get_test_metrics_data()) is None


def test_pre_save_payload_generation_does_not_report(
    webhook_with_invalid_query,
    order,
    settings,
    get_test_metrics_data,
    django_capture_on_commit_callbacks,
):
    # given
    settings.ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS = True
    webhook = webhook_with_invalid_query
    event_type = WebhookEventAsyncType.ORDER_CREATED

    # when
    with django_capture_on_commit_callbacks(execute=True):
        payloads = generate_pre_save_payloads(
            [webhook], [order], event_type, None, order.created_at
        )

    # then
    assert list(payloads.values()) == [None]
    assert AppProblem.objects.exists() is False
    assert recorded_payload_error(get_test_metrics_data()) is None


def test_payload_generation_without_webhook_does_not_report(
    webhook_app,
    order,
    get_test_metrics_data,
    django_capture_on_commit_callbacks,
):
    """The webhookDryRun path: a raw query, no webhook and no lost delivery."""
    # given
    event_type = WebhookEventAsyncType.ORDER_CREATED
    request = initialize_request(app=webhook_app, event_type=event_type)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        payload = generate_payload_from_subscription(
            event_type, order, INVALID_ORDER_CREATED_QUERY, request
        )

    # then
    assert payload is None
    assert AppProblem.objects.exists() is False
    assert recorded_payload_error(get_test_metrics_data()) is None


def test_dropped_payload_log_identifies_app_and_webhook_by_global_id(
    webhook_with_invalid_query,
    order,
    caplog,
    django_capture_on_commit_callbacks,
):
    """The log feeds the operator dashboard, so it must use the same ids as the metric."""
    # given
    webhook = webhook_with_invalid_query
    event_type = WebhookEventAsyncType.ORDER_CREATED
    caplog.set_level(
        logging.WARNING, logger="saleor.graphql.webhook.subscription_payload"
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_deliveries_for_subscriptions(event_type, order, [webhook])

    # then
    record = next(
        record
        for record in caplog.records
        if record.msg.startswith("Unable to build a payload for subscription.")
    )
    assert record.app == graphene.Node.to_global_id("App", webhook.app_id)
    assert record.webhook_id == graphene.Node.to_global_id("Webhook", webhook.pk)
    assert record.event_type == event_type
    # The query is deliberately absent: it is unbounded and repeats on every drop.
    assert hasattr(record, "query") is False

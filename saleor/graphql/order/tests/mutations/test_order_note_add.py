from unittest.mock import ANY, patch

import graphene
import pytest
from django.test import override_settings

from .....account.models import CustomerEvent
from .....core.models import EventDelivery
from .....order import OrderStatus
from .....order import events as order_events
from .....order.actions import call_order_event
from .....order.error_codes import OrderNoteAddErrorCode
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_NOTE_ADD_MUTATION = """
    mutation addNote($id: ID!, $message: String!) {
        orderNoteAdd(order: $id, input: {message: $message}) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
            event {
                user {
                    email
                }
                app {
                    name
                }
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_note_add_as_staff_user(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    staff_user,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    assert not order.events.all()
    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "nuclear note"
    variables = {"id": order_id, "message": message}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_ADD_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteAdd"]

    assert data["order"]["id"] == order_id
    assert data["event"]["user"]["email"] == staff_user.email
    assert data["event"]["message"] == message
    order_updated_webhook_mock.assert_called_once_with(order, webhooks=set())

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED

    # Ensure the correct order event was created
    event = order.events.get()
    assert event.type == order_events.OrderEvents.NOTE_ADDED
    assert event.user == staff_user
    assert event.parameters == {"message": message}

    # Ensure no customer events were created as it was a staff action
    assert not CustomerEvent.objects.exists()


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_note_add_fail_on_empty_message(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    message,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id, "message": message}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_ADD_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteAdd"]
    assert data["errors"][0]["field"] == "message"
    assert data["errors"][0]["code"] == OrderNoteAddErrorCode.REQUIRED.name
    order_updated_webhook_mock.assert_not_called()


def test_order_add_note_as_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    order_with_lines,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    order = order_with_lines
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "nuclear note"
    variables = {"id": order_id, "message": message}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_ADD_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_add_note_by_app(
    order_updated_webhook_mock,
    app_api_client,
    permission_manage_orders,
    order_with_lines,
):
    # given
    order = order_with_lines
    assert not order.events.all()
    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "nuclear note"
    variables = {"id": order_id, "message": message}

    # when
    response = app_api_client.post_graphql(
        ORDER_NOTE_ADD_MUTATION, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteAdd"]

    assert data["order"]["id"] == order_id
    assert data["event"]["user"] is None
    assert data["event"]["app"]["name"] == app_api_client.app.name
    assert data["event"]["message"] == message
    order_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


def test_order_note_add_fail_on_missing_permission(staff_api_client, order):
    # given
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "message": "a note"}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_ADD_MUTATION, variables)

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    ("status", "webhook_event"),
    [
        (OrderStatus.DRAFT, WebhookEventAsyncType.DRAFT_ORDER_UPDATED),
        (OrderStatus.UNCONFIRMED, WebhookEventAsyncType.ORDER_UPDATED),
    ],
)
@patch(
    "saleor.graphql.order.mutations.utils.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_note_add_user_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    settings,
    status,
    webhook_event,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.should_refresh_prices = True
    order.status = status
    order.save(update_fields=["status", "should_refresh_prices"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "new note"
    variables = {"id": order_id, "message": message}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_ADD_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderNoteAdd"]["errors"]

    # confirm that event delivery was generated for each async webhook.
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id, "telemetry_context": ANY},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(webhook_id=order_webhook.id).exists()

    tax_delivery_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )

    assert wrapped_call_order_event.called

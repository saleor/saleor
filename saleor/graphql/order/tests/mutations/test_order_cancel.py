from unittest.mock import ANY, call, patch

import graphene
from django.test import override_settings

from .....core.models import EventDelivery
from .....giftcard import GiftCardEvents
from .....giftcard.events import gift_cards_bought_event
from .....order import OrderStatus
from .....order.actions import cancel_order
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.transport.asynchronous.transport import generate_deferred_payloads
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_ORDER_CANCEL = """
mutation cancelOrder($id: ID!) {
    orderCancel(id: $id) {
        order {
            status
        }
        errors{
            field
            code
            message
        }
    }
}
"""


@patch("saleor.graphql.order.mutations.order_cancel.cancel_order", wraps=cancel_order)
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel(
    mock_clean_order_cancel,
    mock_cancel_order,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    mock_clean_order_cancel.return_value = order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(MUTATION_ORDER_CANCEL, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(
        order=order, user=staff_api_client.user, app=None, manager=ANY
    )


@patch("saleor.graphql.order.mutations.order_cancel.cancel_order")
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel_as_app(
    mock_clean_order_cancel,
    mock_cancel_order,
    app_api_client,
    permission_manage_orders,
    order_with_lines,
):
    order = order_with_lines
    mock_clean_order_cancel.return_value = order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(
        order=order, user=None, app=app_api_client.app, manager=ANY
    )


@patch("saleor.graphql.order.mutations.order_cancel.cancel_order")
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel_with_bought_gift_cards(
    mock_clean_order_cancel,
    mock_cancel_order,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    gift_card,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    mock_clean_order_cancel.return_value = order
    gift_cards_bought_event([gift_card], order, staff_api_client.user, None)
    assert gift_card.is_active is True
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(MUTATION_ORDER_CANCEL, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(
        order=order, user=staff_api_client.user, app=None, manager=ANY
    )

    gift_card.refresh_from_db()
    assert gift_card.is_active is False
    assert gift_card.events.filter(type=GiftCardEvents.DEACTIVATED)


def test_order_cancel_no_channel_access(
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
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(MUTATION_ORDER_CANCEL, variables)

    # then
    assert_no_permission(response)


@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async",
    wraps=generate_deferred_payloads.apply_async,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@override_settings(WEBHOOK_DEFERRED_PAYLOAD_QUEUE_NAME="deferred_queue")
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel_skip_trigger_webhooks(
    mock_clean_order_cancel,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_generate_deferred_payloads,
    setup_order_webhooks,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    settings,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [WebhookEventAsyncType.ORDER_UPDATED, WebhookEventAsyncType.ORDER_CANCELLED]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.should_refresh_prices = True
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status", "should_refresh_prices"])
    mock_clean_order_cancel.return_value = order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(MUTATION_ORDER_CANCEL, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    # confirm that event delivery was generated for each webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    order_cancelled_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_CANCELLED,
    )
    order_deliveries = [
        order_cancelled_delivery,
        order_updated_delivery,
    ]
    tax_delivery = EventDelivery.objects.filter(webhook_id=tax_webhook.id).first()
    filter_shipping_delivery = EventDelivery.objects.filter(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    ).first()

    assert not tax_delivery
    assert not filter_shipping_delivery

    wrapped_generate_deferred_payloads.assert_has_calls(
        [
            call(
                kwargs={
                    "event_delivery_ids": [delivery.id],
                    "deferred_payload_data": {
                        "model_name": "order.order",
                        "object_id": order.pk,
                        "requestor_model_name": "account.user",
                        "requestor_object_id": staff_api_client.user.pk,
                        "request_time": None,
                    },
                    "send_webhook_queue": settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                    "telemetry_context": ANY,
                },
                queue=settings.WEBHOOK_DEFERRED_PAYLOAD_QUEUE_NAME,
                MessageGroupId="example.com",
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )
    assert wrapped_generate_deferred_payloads.call_count == len(order_deliveries)
    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id, "telemetry_context": ANY},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                MessageGroupId="example.com:saleorappadditional",
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )
    assert not mocked_send_webhook_request_sync.called

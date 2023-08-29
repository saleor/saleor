from unittest.mock import ANY, patch

import graphene
import pytest

from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import assert_no_permission, get_graphql_content

FULFILLMENT_UPDATE_TRACKING_QUERY = """
    mutation updateFulfillment(
        $id: ID!
        $tracking: String
        $notifyCustomer: Boolean
    ) {
        orderFulfillmentUpdateTracking(
            id: $id
            input: { trackingNumber: $tracking, notifyCustomer: $notifyCustomer }
        ) {
            fulfillment {
                trackingNumber
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_fulfillment_update_tracking(
    send_fulfillment_update_mock,
    staff_api_client,
    fulfillment,
    permission_group_manage_orders,
):
    query = FULFILLMENT_UPDATE_TRACKING_QUERY
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    tracking = "stationary tracking"
    variables = {"id": fulfillment_id, "tracking": tracking}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentUpdateTracking"]["fulfillment"]
    assert data["trackingNumber"] == tracking
    send_fulfillment_update_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_fulfillment_update_tracking_by_user_no_channel_access(
    send_fulfillment_update_mock,
    staff_api_client,
    fulfillment,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
):
    # given
    query = FULFILLMENT_UPDATE_TRACKING_QUERY
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    order = fulfillment.order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    tracking = "stationary tracking"
    variables = {"id": fulfillment_id, "tracking": tracking}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_fulfillment_update_tracking_by_app(
    send_fulfillment_update_mock, app_api_client, fulfillment, permission_manage_orders
):
    # given
    query = FULFILLMENT_UPDATE_TRACKING_QUERY
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    tracking = "stationary tracking"
    variables = {"id": fulfillment_id, "tracking": tracking}

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentUpdateTracking"]["fulfillment"]
    assert data["trackingNumber"] == tracking
    send_fulfillment_update_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.tracking_number_updated")
@patch(
    "saleor.graphql.order.mutations.fulfillment_update_tracking.send_fulfillment_update"
)
def test_fulfillment_update_tracking_send_notification_true(
    send_fulfillment_update_mock,
    mocked_tracking_number_updated_event,
    staff_api_client,
    fulfillment,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    tracking = "stationary tracking"
    variables = {"id": fulfillment_id, "tracking": tracking, "notifyCustomer": True}
    response = staff_api_client.post_graphql(
        FULFILLMENT_UPDATE_TRACKING_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentUpdateTracking"]["fulfillment"]
    assert data["trackingNumber"] == tracking
    send_fulfillment_update_mock.assert_called_once_with(
        fulfillment.order, fulfillment, ANY
    )
    mocked_tracking_number_updated_event.assert_called_once_with(fulfillment)


@patch("saleor.plugins.manager.PluginsManager.tracking_number_updated")
@patch("saleor.order.notifications.send_fulfillment_update")
def test_fulfillment_update_tracking_send_notification_false(
    send_fulfillment_update_mock,
    mocked_tracking_number_updated_event,
    staff_api_client,
    fulfillment,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    tracking = "stationary tracking"
    variables = {"id": fulfillment_id, "tracking": tracking, "notifyCustomer": False}
    response = staff_api_client.post_graphql(
        FULFILLMENT_UPDATE_TRACKING_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentUpdateTracking"]["fulfillment"]
    assert data["trackingNumber"] == tracking
    send_fulfillment_update_mock.assert_not_called()
    mocked_tracking_number_updated_event.assert_called_once_with(fulfillment)


@pytest.mark.parametrize("notify_customer", [True, False])
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_fulfillment_tracking_number_updated_event_triggered(
    mocked_webhooks,
    notify_customer,
    permission_group_manage_orders,
    fulfillment,
    settings,
    subscription_fulfillment_tracking_number_updated,
    staff_api_client,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {
        "id": fulfillment_id,
        "tracking": "tracking",
        "notifyCustomer": notify_customer,
    }

    # when
    staff_api_client.post_graphql(FULFILLMENT_UPDATE_TRACKING_QUERY, variables)

    # then
    mocked_webhooks.assert_called_once()
    assert mocked_webhooks.call_args[0][1] == (
        WebhookEventAsyncType.FULFILLMENT_TRACKING_NUMBER_UPDATED
    )

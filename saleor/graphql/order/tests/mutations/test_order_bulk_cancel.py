from unittest.mock import ANY, call, patch

import graphene

from .....order.models import OrderLine
from .....product.models import ProductVariant
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_ORDER_BULK_CANCEL = """
mutation CancelManyOrders($ids: [ID!]!) {
    orderBulkCancel(ids: $ids) {
        count
        errors{
            field
            code
        }
    }
}
"""


@patch("saleor.graphql.order.bulk_mutations.order_bulk_cancel.get_webhooks_for_event")
@patch("saleor.graphql.order.bulk_mutations.order_bulk_cancel.cancel_order")
def test_order_bulk_cancel(
    mock_cancel_order,
    mocked_get_webhooks_for_event,
    staff_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_group_manage_orders,
    address,
    any_webhook,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = staff_api_client.post_graphql(MUTATION_ORDER_BULK_CANCEL, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["errors"]

    calls = [
        call(
            order=order,
            user=staff_api_client.user,
            app=None,
            manager=ANY,
            webhooks_cancelled=[any_webhook],
            webhooks_updated=[any_webhook],
        )
        for order in orders
    ]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    mock_cancel_order.call_count == expected_count


def test_order_bulk_cancel_by_user_no_channel_access(
    staff_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    orders = order_list
    order_in_PLN = orders[0]
    order_in_PLN.channel = channel_PLN
    order_in_PLN.save(update_fields=["channel"])

    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }

    # when
    response = staff_api_client.post_graphql(MUTATION_ORDER_BULK_CANCEL, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_bulk_cancel_with_back_in_stock_webhook(
    product_variant_back_in_stock_webhook_mock,
    staff_api_client,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "ids": [
            graphene.Node.to_global_id(
                "Order", fulfilled_order_with_all_cancelled_fulfillments.id
            )
        ]
    }
    staff_api_client.post_graphql(MUTATION_ORDER_BULK_CANCEL, variables)

    product_variant_back_in_stock_webhook_mock.assert_called_once()


@patch("saleor.graphql.order.bulk_mutations.order_bulk_cancel.get_webhooks_for_event")
@patch("saleor.graphql.order.bulk_mutations.order_bulk_cancel.cancel_order")
def test_order_bulk_cancel_as_app(
    mock_cancel_order,
    mocked_get_webhooks_for_event,
    app_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
    address,
    any_webhook,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = app_api_client.post_graphql(
        MUTATION_ORDER_BULK_CANCEL, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["errors"]

    calls = [
        call(
            order=order,
            user=None,
            app=app_api_client.app,
            manager=ANY,
            webhooks_cancelled=[any_webhook],
            webhooks_updated=[any_webhook],
        )
        for order in orders
    ]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    assert mock_cancel_order.call_count == expected_count


@patch("saleor.graphql.order.bulk_mutations.order_bulk_cancel.get_webhooks_for_event")
@patch("saleor.graphql.order.bulk_mutations.order_bulk_cancel.cancel_order")
def test_order_bulk_cancel_without_sku(
    mock_cancel_order,
    mocked_get_webhooks_for_event,
    staff_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_group_manage_orders,
    address,
    any_webhook,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    ProductVariant.objects.update(sku=None)
    OrderLine.objects.update(product_sku=None)

    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = staff_api_client.post_graphql(MUTATION_ORDER_BULK_CANCEL, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["errors"]

    calls = [
        call(
            order=order,
            user=staff_api_client.user,
            app=None,
            manager=ANY,
            webhooks_cancelled=[any_webhook],
            webhooks_updated=[any_webhook],
        )
        for order in orders
    ]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    assert mock_cancel_order.call_count == expected_count

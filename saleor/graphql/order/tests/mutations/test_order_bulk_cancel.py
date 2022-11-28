from unittest.mock import ANY, call, patch

import graphene

from .....order.models import OrderLine
from .....product.models import ProductVariant
from ....tests.utils import get_graphql_content

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


@patch("saleor.graphql.order.bulk_mutations.orders.cancel_order")
def test_order_bulk_cancel(
    mock_cancel_order,
    staff_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
    address,
):
    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = staff_api_client.post_graphql(
        MUTATION_ORDER_BULK_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["errors"]

    calls = [
        call(order=order, user=staff_api_client.user, app=None, manager=ANY)
        for order in orders
    ]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    mock_cancel_order.call_count == expected_count


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_bulk_cancel_with_back_in_stock_webhook(
    product_variant_back_in_stock_webhook_mock,
    staff_api_client,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
):
    variables = {
        "ids": [
            graphene.Node.to_global_id(
                "Order", fulfilled_order_with_all_cancelled_fulfillments.id
            )
        ]
    }
    staff_api_client.post_graphql(
        MUTATION_ORDER_BULK_CANCEL, variables, permissions=[permission_manage_orders]
    )

    product_variant_back_in_stock_webhook_mock.assert_called_once()


@patch("saleor.graphql.order.bulk_mutations.orders.cancel_order")
def test_order_bulk_cancel_as_app(
    mock_cancel_order,
    app_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
    address,
):
    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = app_api_client.post_graphql(
        MUTATION_ORDER_BULK_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["errors"]

    calls = [
        call(order=order, user=None, app=app_api_client.app, manager=ANY)
        for order in orders
    ]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    assert mock_cancel_order.call_count == expected_count


@patch("saleor.graphql.order.bulk_mutations.orders.cancel_order")
def test_order_bulk_cancel_without_sku(
    mock_cancel_order,
    staff_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
    address,
):
    ProductVariant.objects.update(sku=None)
    OrderLine.objects.update(product_sku=None)

    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = staff_api_client.post_graphql(
        MUTATION_ORDER_BULK_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["errors"]

    calls = [
        call(order=order, user=staff_api_client.user, app=None, manager=ANY)
        for order in orders
    ]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    mock_cancel_order.call_count == expected_count

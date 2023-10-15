from unittest.mock import patch

import graphene
import pytest

from ....tests.utils import get_graphql_content

ORDER_FULFILL_QUERY = """
    mutation fulfillOrder(
        $order: ID, $input: OrderFulfillInput!
    ) {
        orderFulfill(
            order: $order,
            input: $input
        ) {
            errors {
                field
                code
                message
                warehouse
                orderLines
            }
        }
    }
"""


@pytest.mark.count_queries(autouse=False)
@patch("saleor.graphql.order.mutations.order_fulfill.create_fulfillments")
def test_order_fulfill(
    mock_create_fulfillments,
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    warehouse,
    count_queries,
):
    order = order_with_lines
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line, order_line2 = order.lines.all()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    order_line2_id = graphene.Node.to_global_id("OrderLine", order_line2.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": True,
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 3, "warehouse": warehouse_id}],
                },
                {
                    "orderLineId": order_line2_id,
                    "stocks": [{"quantity": 2, "warehouse": warehouse_id}],
                },
            ],
        },
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert not data["errors"]


@pytest.mark.count_queries(autouse=False)
@patch("saleor.giftcard.utils.send_gift_card_notification")
@patch("saleor.graphql.order.mutations.order_fulfill.create_fulfillments")
def test_order_fulfill_with_gift_cards(
    mock_create_fulfillments,
    mock_send_notification,
    staff_api_client,
    order,
    gift_card_non_shippable_order_line,
    gift_card_shippable_order_line,
    permission_group_manage_orders,
    warehouse,
    count_queries,
):
    query = ORDER_FULFILL_QUERY
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line, order_line2 = (
        gift_card_non_shippable_order_line,
        gift_card_shippable_order_line,
    )

    order_line2.quantity = 10
    order_line2.save(update_fields=["quantity"])

    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    order_line2_id = graphene.Node.to_global_id("OrderLine", order_line2.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": True,
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 1, "warehouse": warehouse_id}],
                },
                {
                    "orderLineId": order_line2_id,
                    "stocks": [{"quantity": 10, "warehouse": warehouse_id}],
                },
            ],
        },
    }
    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert not data["errors"]

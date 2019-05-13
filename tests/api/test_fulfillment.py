from unittest.mock import patch

import graphene
import pytest

from .utils import assert_read_only_mode

CREATE_FULFILLMENT_QUERY = """
    mutation fulfillOrder(
        $order: ID, $lines: [FulfillmentLineInput]!, $tracking: String,
        $notify: Boolean
    ) {
        orderFulfillmentCreate(
            order: $order,
            input: {
                lines: $lines, trackingNumber: $tracking,
                notifyCustomer: $notify}
        ) {
            errors {
                field
                message
            }
            fulfillment {
                fulfillmentOrder
                status
                trackingNumber
            lines {
                id
            }
        }
    }
}
"""


@patch(
    "saleor.graphql.order.mutations.fulfillments."
    "send_fulfillment_confirmation_to_customer"
)
def test_create_fulfillment(
    mock_email_fulfillment,
    staff_api_client,
    order_with_lines,
    staff_user,
    permission_manage_orders,
):
    order = order_with_lines
    query = CREATE_FULFILLMENT_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line = order.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    tracking = "Flames tracking"
    variables = {
        "order": order_id,
        "lines": [{"orderLineId": order_line_id, "quantity": 1}],
        "tracking": tracking,
        "notify": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


@patch(
    "saleor.graphql.order.mutations.fulfillments."
    "send_fulfillment_confirmation_to_customer"
)
def test_create_fulfillment_with_empty_quantity(
    mock_send_fulfillment_confirmation,
    staff_api_client,
    order_with_lines,
    staff_user,
    permission_manage_orders,
):
    order = order_with_lines
    query = CREATE_FULFILLMENT_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_lines = order.lines.all()
    order_line_ids = [
        graphene.Node.to_global_id("OrderLine", order_line.id)
        for order_line in order_lines
    ]
    tracking = "Flames tracking"
    assert not order.events.all()
    variables = {
        "order": order_id,
        "lines": [
            {"orderLineId": order_line_id, "quantity": 1}
            for order_line_id in order_line_ids
        ],
        "tracking": tracking,
        "notify": True,
    }
    variables["lines"][0]["quantity"] = 0
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


@pytest.mark.parametrize(
    "quantity, error_message, error_field",
    (
        (0, "Total quantity must be larger than 0.", "lines"),
        (100, "Only 3 items remaining to fulfill:", "orderLineId"),
    ),
)
def test_create_fulfillment_not_sufficient_quantity(
    staff_api_client,
    order_with_lines,
    staff_user,
    quantity,
    error_message,
    error_field,
    permission_manage_orders,
):
    query = CREATE_FULFILLMENT_QUERY
    order_line = order_with_lines.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    variables = {
        "order": graphene.Node.to_global_id("Order", order_with_lines.id),
        "lines": [{"orderLineId": order_line_id, "quantity": quantity}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


def test_create_fulfillment_with_invalid_input(
    staff_api_client, order_with_lines, permission_manage_orders
):
    query = CREATE_FULFILLMENT_QUERY
    variables = {
        "order": graphene.Node.to_global_id("Order", order_with_lines.id),
        "lines": [{"orderLineId": "fake-orderline-id", "quantity": 1}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


def test_fulfillment_update_tracking(
    staff_api_client, fulfillment, permission_manage_orders
):
    query = """
    mutation updateFulfillment($id: ID!, $tracking: String) {
            orderFulfillmentUpdateTracking(
                id: $id, input: {trackingNumber: $tracking}) {
                    fulfillment {
                        trackingNumber
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    tracking = "stationary tracking"
    variables = {"id": fulfillment_id, "tracking": tracking}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


def test_cancel_fulfillment_restock_items(
    staff_api_client, fulfillment, staff_user, permission_manage_orders
):
    query = """
    mutation cancelFulfillment($id: ID!, $restock: Boolean) {
            orderFulfillmentCancel(id: $id, input: {restock: $restock}) {
                    fulfillment {
                        status
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "restock": True}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


def test_cancel_fulfillment(
    staff_api_client, fulfillment, staff_user, permission_manage_orders
):
    query = """
    mutation cancelFulfillment($id: ID!, $restock: Boolean) {
            orderFulfillmentCancel(id: $id, input: {restock: $restock}) {
                    fulfillment {
                        status
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "restock": False}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


@patch(
    "saleor.graphql.order.mutations.fulfillments."
    "send_fulfillment_confirmation_to_customer"
)
def test_create_digital_fulfillment(
    mock_email_fulfillment,
    digital_content,
    staff_api_client,
    order_with_lines,
    staff_user,
    permission_manage_orders,
):
    order = order_with_lines
    query = CREATE_FULFILLMENT_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line = order.lines.first()
    order_line.variant = digital_content.product_variant
    order_line.save()

    second_line = order.lines.last()
    first_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    second_line_id = graphene.Node.to_global_id("OrderLine", second_line.id)

    tracking = "Flames tracking"
    variables = {
        "order": order_id,
        "lines": [
            {"orderLineId": first_line_id, "quantity": 1},
            {"orderLineId": second_line_id, "quantity": 1},
        ],
        "tracking": tracking,
        "notify": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)

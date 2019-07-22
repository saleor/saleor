from unittest.mock import patch

import graphene
import pytest

from saleor.order.events import OrderEvents
from saleor.order.models import FulfillmentStatus
from tests.api.utils import get_graphql_content

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
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCreate"]["fulfillment"]
    assert data["fulfillmentOrder"] == 1
    assert data["status"] == FulfillmentStatus.FULFILLED.upper()
    assert data["trackingNumber"] == tracking
    assert len(data["lines"]) == 1

    assert mock_email_fulfillment.call_count == 1


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
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCreate"]["fulfillment"]
    assert data["fulfillmentOrder"] == 1
    assert data["status"] == FulfillmentStatus.FULFILLED.upper()

    assert mock_send_fulfillment_confirmation.called


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
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCreate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == error_field
    assert error_message in data["errors"][0]["message"]


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
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCreate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "lines"
    assert data["errors"][0]["message"] == (
        "Could not resolve to a node with the global id list"
        " of '['fake-orderline-id']'."
    )


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
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentUpdateTracking"]["fulfillment"]
    assert data["trackingNumber"] == tracking


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
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCancel"]["fulfillment"]
    assert data["status"] == FulfillmentStatus.CANCELED.upper()
    event_cancelled, event_restocked_items = fulfillment.order.events.all()
    assert event_cancelled.type == (OrderEvents.FULFILLMENT_CANCELED)
    assert event_cancelled.parameters == {"composed_id": fulfillment.composed_id}
    assert event_cancelled.user == staff_user

    assert event_restocked_items.type == (OrderEvents.FULFILLMENT_RESTOCKED_ITEMS)
    assert event_restocked_items.parameters == {
        "quantity": fulfillment.get_total_quantity()
    }
    assert event_restocked_items.user == staff_user


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
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCancel"]["fulfillment"]
    assert data["status"] == FulfillmentStatus.CANCELED.upper()
    event_cancel_fulfillment = fulfillment.order.events.get()
    assert event_cancel_fulfillment.type == (OrderEvents.FULFILLMENT_CANCELED)
    assert event_cancel_fulfillment.parameters == {
        "composed_id": fulfillment.composed_id
    }
    assert event_cancel_fulfillment.user == staff_user


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
    get_graphql_content(response)

    assert mock_email_fulfillment.call_count == 1

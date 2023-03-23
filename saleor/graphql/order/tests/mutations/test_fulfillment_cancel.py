from unittest.mock import patch

import graphene

from .....order import FulfillmentStatus, OrderEvents, OrderStatus
from .....order.error_codes import OrderErrorCode
from .....order.models import Fulfillment
from .....warehouse.models import Allocation, Stock
from ....tests.utils import get_graphql_content

CANCEL_FULFILLMENT_MUTATION = """
    mutation cancelFulfillment($id: ID!, $warehouseId: ID) {
        orderFulfillmentCancel(id: $id, input: {warehouseId: $warehouseId}) {
            fulfillment {
                status
            }
            order {
                status
            }
            errors {
                code
                field
            }
        }
    }
"""


def test_cancel_fulfillment(
    staff_api_client, fulfillment, staff_user, permission_manage_orders, warehouse
):
    query = CANCEL_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"id": fulfillment_id, "warehouseId": warehouse_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCancel"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.CANCELED.upper()
    assert data["order"]["status"] == OrderStatus.UNFULFILLED.upper()
    event_cancelled, event_restocked_items = fulfillment.order.events.all()
    assert event_cancelled.type == (OrderEvents.FULFILLMENT_CANCELED)
    assert event_cancelled.parameters == {"composed_id": fulfillment.composed_id}
    assert event_cancelled.user == staff_user

    assert event_restocked_items.type == (OrderEvents.FULFILLMENT_RESTOCKED_ITEMS)
    assert event_restocked_items.parameters == {
        "quantity": fulfillment.get_total_quantity(),
        "warehouse": str(warehouse.pk),
    }
    assert event_restocked_items.user == staff_user
    assert Fulfillment.objects.filter(
        pk=fulfillment.pk, status=FulfillmentStatus.CANCELED
    ).exists()


def test_cancel_fulfillment_for_order_with_gift_card_lines(
    staff_api_client,
    fulfillment,
    gift_card_shippable_order_line,
    staff_user,
    permission_manage_orders,
    warehouse,
):
    query = CANCEL_FULFILLMENT_MUTATION
    order = gift_card_shippable_order_line.order
    order_fulfillment = order.fulfillments.first()
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", order_fulfillment.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"id": fulfillment_id, "warehouseId": warehouse_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCancel"]
    assert not data["fulfillment"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == OrderErrorCode.CANNOT_CANCEL_FULFILLMENT.name
    assert data["errors"][0]["field"] == "fulfillment"


def test_cancel_fulfillment_no_warehouse_id(
    staff_api_client, fulfillment, permission_manage_orders
):
    query = """
        mutation cancelFulfillment($id: ID!) {
            orderFulfillmentCancel(id: $id) {
                fulfillment {
                    status
                }
                order {
                    status
                }
                errors {
                    code
                    field
                }
            }
        }
    """
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["orderFulfillmentCancel"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "warehouseId"
    assert error["code"] == OrderErrorCode.REQUIRED.name


@patch("saleor.order.actions.restock_fulfillment_lines")
def test_cancel_fulfillment_awaiting_approval(
    mock_restock_lines, staff_api_client, fulfillment, permission_manage_orders
):
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
    query = CANCEL_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCancel"]
    assert data["fulfillment"] is None
    mock_restock_lines.assert_not_called()
    event_cancelled = fulfillment.order.events.get()
    assert event_cancelled.type == (OrderEvents.FULFILLMENT_CANCELED)
    assert event_cancelled.parameters == {}
    assert event_cancelled.user == staff_api_client.user
    assert not Fulfillment.objects.filter(pk=fulfillment.pk).exists()


@patch("saleor.order.actions.restock_fulfillment_lines")
def test_cancel_fulfillment_awaiting_approval_warehouse_specified(
    mock_restock_lines,
    staff_api_client,
    fulfillment,
    permission_manage_orders,
    warehouse,
):
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
    query = CANCEL_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"id": fulfillment_id, "warehouseId": warehouse_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentCancel"]
    assert data["fulfillment"] is None
    mock_restock_lines.assert_not_called()
    event_cancelled = fulfillment.order.events.get()
    assert event_cancelled.type == (OrderEvents.FULFILLMENT_CANCELED)
    assert event_cancelled.parameters == {}
    assert event_cancelled.user == staff_api_client.user
    assert not Fulfillment.objects.filter(pk=fulfillment.pk).exists()


def test_cancel_fulfillment_canceled_state(
    staff_api_client, fulfillment, permission_manage_orders, warehouse
):
    query = CANCEL_FULFILLMENT_MUTATION
    fulfillment.status = FulfillmentStatus.CANCELED
    fulfillment.save(update_fields=["status"])
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"id": fulfillment_id, "warehouseId": warehouse_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["orderFulfillmentCancel"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "fulfillment"
    assert error["code"] == OrderErrorCode.CANNOT_CANCEL_FULFILLMENT.name


def test_cancel_fulfillment_warehouse_without_stock(
    order_line, warehouse, staff_api_client, permission_manage_orders, staff_user
):
    query = CANCEL_FULFILLMENT_MUTATION
    order = order_line.order
    fulfillment = order.fulfillments.create(tracking_number="123")
    fulfillment.lines.create(order_line=order_line, quantity=order_line.quantity)
    order.status = OrderStatus.FULFILLED
    order.save(update_fields=["status"])

    assert not Stock.objects.filter(
        warehouse=warehouse, product_variant=order_line.variant
    )
    assert not Allocation.objects.filter(order_line=order_line)

    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"id": fulfillment_id, "warehouseId": warehouse_id}
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
        "quantity": fulfillment.get_total_quantity(),
        "warehouse": str(warehouse.pk),
    }
    assert event_restocked_items.user == staff_user

    stock = Stock.objects.filter(
        warehouse=warehouse, product_variant=order_line.variant
    ).first()
    assert stock.quantity == order_line.quantity
    allocation = order_line.allocations.filter(stock=stock).first()
    assert allocation.quantity_allocated == order_line.quantity

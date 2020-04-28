from unittest.mock import patch

import graphene
import pytest

from saleor.core.exceptions import InsufficientStock
from saleor.core.permissions import OrderPermissions
from saleor.order import OrderStatus
from saleor.order.error_codes import OrderErrorCode
from saleor.order.events import OrderEvents
from saleor.order.models import FulfillmentStatus
from saleor.warehouse.models import Allocation, Stock
from tests.api.utils import assert_no_permission, get_graphql_content

ORDER_FULFILL_QUERY = """
mutation fulfillOrder(
    $order: ID, $input: OrderFulfillInput!
) {
    orderFulfill(
        order: $order,
        input: $input
    ) {
        orderErrors {
            field
            code
            message
            warehouse
            orderLine
        }
    }
}
"""


@patch("saleor.graphql.order.mutations.fulfillments.create_fulfillments")
def test_order_fulfill(
    mock_create_fulfillments,
    staff_api_client,
    staff_user,
    order_with_lines,
    permission_manage_orders,
    warehouse,
):
    order = order_with_lines
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
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert not data["orderErrors"]

    fulfillment_lines_for_warehouses = {
        str(warehouse.pk): [
            {"order_line": order_line, "quantity": 3},
            {"order_line": order_line2, "quantity": 2},
        ]
    }
    mock_create_fulfillments.assert_called_once_with(
        staff_user, order, fulfillment_lines_for_warehouses, True
    )


@patch("saleor.graphql.order.mutations.fulfillments.create_fulfillments")
def test_order_fulfill_many_warehouses(
    mock_create_fulfillments,
    staff_api_client,
    staff_user,
    order_with_lines,
    permission_manage_orders,
    warehouses,
):
    order = order_with_lines
    query = ORDER_FULFILL_QUERY

    warehouse1, warehouse2 = warehouses
    order_line1, order_line2 = order.lines.all()

    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line1_id = graphene.Node.to_global_id("OrderLine", order_line1.id)
    order_line2_id = graphene.Node.to_global_id("OrderLine", order_line2.id)
    warehouse1_id = graphene.Node.to_global_id("Warehouse", warehouse1.pk)
    warehouse2_id = graphene.Node.to_global_id("Warehouse", warehouse2.pk)

    variables = {
        "order": order_id,
        "input": {
            "lines": [
                {
                    "orderLineId": order_line1_id,
                    "stocks": [{"quantity": 3, "warehouse": warehouse1_id}],
                },
                {
                    "orderLineId": order_line2_id,
                    "stocks": [
                        {"quantity": 1, "warehouse": warehouse1_id},
                        {"quantity": 1, "warehouse": warehouse2_id},
                    ],
                },
            ],
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert not data["orderErrors"]

    fulfillment_lines_for_warehouses = {
        str(warehouse1.pk): [
            {"order_line": order_line1, "quantity": 3},
            {"order_line": order_line2, "quantity": 1},
        ],
        str(warehouse2.pk): [{"order_line": order_line2, "quantity": 1}],
    }

    mock_create_fulfillments.assert_called_once_with(
        staff_user, order, fulfillment_lines_for_warehouses, True
    )


@patch("saleor.graphql.order.mutations.fulfillments.create_fulfillments")
def test_order_fulfill_without_notification(
    mock_create_fulfillments,
    staff_api_client,
    staff_user,
    order_with_lines,
    permission_manage_orders,
    warehouse,
):
    order = order_with_lines
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line = order.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": False,
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 1, "warehouse": warehouse_id}],
                }
            ],
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert not data["orderErrors"]

    fulfillment_lines_for_warehouses = {
        str(warehouse.pk): [{"order_line": order_line, "quantity": 1}]
    }
    mock_create_fulfillments.assert_called_once_with(
        staff_user, order, fulfillment_lines_for_warehouses, False
    )


@patch("saleor.graphql.order.mutations.fulfillments.create_fulfillments")
def test_order_fulfill_lines_with_empty_quantity(
    mock_create_fulfillments,
    staff_api_client,
    staff_user,
    order_with_lines,
    permission_manage_orders,
    warehouse,
    warehouse_no_shipping_zone,
):
    order = order_with_lines
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line, order_line2 = order.lines.all()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    order_line2_id = graphene.Node.to_global_id("OrderLine", order_line2.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    warehouse2_id = graphene.Node.to_global_id(
        "Warehouse", warehouse_no_shipping_zone.pk
    )
    assert not order.events.all()
    variables = {
        "order": order_id,
        "input": {
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [
                        {"quantity": 0, "warehouse": warehouse_id},
                        {"quantity": 0, "warehouse": warehouse2_id},
                    ],
                },
                {
                    "orderLineId": order_line2_id,
                    "stocks": [
                        {"quantity": 2, "warehouse": warehouse_id},
                        {"quantity": 0, "warehouse": warehouse2_id},
                    ],
                },
            ],
        },
    }
    variables["input"]["lines"][0]["stocks"][0]["quantity"] = 0
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert not data["orderErrors"]

    fulfillment_lines_for_warehouses = {
        str(warehouse.pk): [{"order_line": order_line2, "quantity": 2}]
    }
    mock_create_fulfillments.assert_called_once_with(
        staff_user, order, fulfillment_lines_for_warehouses, True
    )


@patch("saleor.graphql.order.mutations.fulfillments.create_fulfillments")
def test_order_fulfill_zero_quantity(
    mock_create_fulfillments,
    staff_api_client,
    staff_user,
    order_with_lines,
    permission_manage_orders,
    warehouse,
):
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    order_line = order_with_lines.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "order": order_id,
        "input": {
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 0, "warehouse": warehouse_id}],
                }
            ]
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert data["orderErrors"]
    error = data["orderErrors"][0]
    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.ZERO_QUANTITY.name
    assert not error["orderLine"]
    assert not error["warehouse"]

    mock_create_fulfillments.assert_not_called()


@patch("saleor.graphql.order.mutations.fulfillments.create_fulfillments")
def test_order_fulfill_fulfilled_order(
    mock_create_fulfillments,
    staff_api_client,
    staff_user,
    order_with_lines,
    permission_manage_orders,
    warehouse,
):
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    order_line = order_with_lines.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "order": order_id,
        "input": {
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 100, "warehouse": warehouse_id}],
                }
            ]
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert data["orderErrors"]
    error = data["orderErrors"][0]
    assert error["field"] == "orderLineId"
    assert error["code"] == OrderErrorCode.FULFILL_ORDER_LINE.name
    assert error["orderLine"] == order_line_id
    assert not error["warehouse"]

    mock_create_fulfillments.assert_not_called()


@patch("saleor.graphql.order.mutations.fulfillments.create_fulfillments", autospec=True)
def test_order_fulfill_warehouse_with_insufficient_stock_exception(
    mock_create_fulfillments,
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
    warehouse_no_shipping_zone,
):
    order = order_with_lines
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line = order.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id(
        "Warehouse", warehouse_no_shipping_zone.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 1, "warehouse": warehouse_id}],
                }
            ]
        },
    }

    error_context = {
        "order_line": order_line,
        "warehouse_pk": str(warehouse_no_shipping_zone.pk),
    }
    mock_create_fulfillments.side_effect = InsufficientStock(
        order_line.variant, error_context
    )

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert data["orderErrors"]
    error = data["orderErrors"][0]
    assert error["field"] == "stocks"
    assert error["code"] == OrderErrorCode.INSUFFICIENT_STOCK.name
    assert error["orderLine"] == order_line_id
    assert error["warehouse"] == warehouse_id


@patch("saleor.graphql.order.mutations.fulfillments.create_fulfillments", autospec=True)
def test_order_fulfill_warehouse_duplicated_warehouse_id(
    mock_create_fulfillments,
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
    warehouse,
):
    order = order_with_lines
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line = order.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "order": order_id,
        "input": {
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [
                        {"quantity": 1, "warehouse": warehouse_id},
                        {"quantity": 2, "warehouse": warehouse_id},
                    ],
                }
            ]
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert data["orderErrors"]
    error = data["orderErrors"][0]
    assert error["field"] == "warehouse"
    assert error["code"] == OrderErrorCode.DUPLICATED_INPUT_ITEM.name
    assert not error["orderLine"]
    assert error["warehouse"] == warehouse_id
    mock_create_fulfillments.assert_not_called()


@patch("saleor.graphql.order.mutations.fulfillments.create_fulfillments", autospec=True)
def test_order_fulfill_warehouse_duplicated_order_line_id(
    mock_create_fulfillments,
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
    warehouse,
):
    order = order_with_lines
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line = order.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "order": order_id,
        "input": {
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 3, "warehouse": warehouse_id}],
                },
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 3, "warehouse": warehouse_id}],
                },
            ]
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert data["orderErrors"]
    error = data["orderErrors"][0]
    assert error["field"] == "orderLineId"
    assert error["code"] == OrderErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["orderLine"] == order_line_id
    assert not error["warehouse"]
    mock_create_fulfillments.assert_not_called()


@patch("saleor.order.emails.send_fulfillment_update.delay")
def test_fulfillment_update_tracking(
    send_fulfillment_update_mock,
    staff_api_client,
    fulfillment,
    permission_manage_orders,
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
    send_fulfillment_update_mock.assert_not_called()


FULFILLMENT_UPDATE_TRACKING_WITH_SEND_NOTIFICATION_QUERY = """
    mutation updateFulfillment($id: ID!, $tracking: String, $notifyCustomer: Boolean) {
            orderFulfillmentUpdateTracking(
                id: $id
                input: {trackingNumber: $tracking, notifyCustomer: $notifyCustomer}) {
                    fulfillment {
                        trackingNumber
                    }
                }
        }
    """


@patch("saleor.order.emails.send_fulfillment_update.delay")
def test_fulfillment_update_tracking_send_notification_true(
    send_fulfillment_update_mock,
    staff_api_client,
    fulfillment,
    permission_manage_orders,
):
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    tracking = "stationary tracking"
    variables = {"id": fulfillment_id, "tracking": tracking, "notifyCustomer": True}
    response = staff_api_client.post_graphql(
        FULFILLMENT_UPDATE_TRACKING_WITH_SEND_NOTIFICATION_QUERY,
        variables,
        permissions=[permission_manage_orders],
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentUpdateTracking"]["fulfillment"]
    assert data["trackingNumber"] == tracking
    send_fulfillment_update_mock.assert_called_once_with(
        fulfillment.order.pk, fulfillment.pk
    )


@patch("saleor.order.emails.send_fulfillment_update.delay")
def test_fulfillment_update_tracking_send_notification_false(
    send_fulfillment_update_mock,
    staff_api_client,
    fulfillment,
    permission_manage_orders,
):
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    tracking = "stationary tracking"
    variables = {"id": fulfillment_id, "tracking": tracking, "notifyCustomer": False}
    response = staff_api_client.post_graphql(
        FULFILLMENT_UPDATE_TRACKING_WITH_SEND_NOTIFICATION_QUERY,
        variables,
        permissions=[permission_manage_orders],
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentUpdateTracking"]["fulfillment"]
    assert data["trackingNumber"] == tracking
    send_fulfillment_update_mock.assert_not_called()


CANCEL_FULFILLMENT_MUTATION = """
    mutation cancelFulfillment($id: ID!, $warehouseId: ID!) {
            orderFulfillmentCancel(id: $id, input: {warehouseId: $warehouseId}) {
                    fulfillment {
                        status
                    }
                    order {
                        status
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


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_create_digital_fulfillment(
    mock_email_fulfillment,
    digital_content,
    staff_api_client,
    order_with_lines,
    warehouse,
    permission_manage_orders,
):
    order = order_with_lines
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line = order.lines.first()
    order_line.variant = digital_content.product_variant
    order_line.save()
    order_line.allocations.all().delete()

    stock = digital_content.product_variant.stocks.get(warehouse=warehouse)
    Allocation.objects.create(
        order_line=order_line, stock=stock, quantity_allocated=order_line.quantity
    )

    second_line = order.lines.last()
    first_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    second_line_id = graphene.Node.to_global_id("OrderLine", second_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": True,
            "lines": [
                {
                    "orderLineId": first_line_id,
                    "stocks": [{"quantity": 1, "warehouse": warehouse_id}],
                },
                {
                    "orderLineId": second_line_id,
                    "stocks": [{"quantity": 1, "warehouse": warehouse_id}],
                },
            ],
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)

    assert mock_email_fulfillment.call_count == 1


@pytest.fixture
def update_metadata_mutation():
    return """
        mutation UpdateMeta($id: ID!, $input: MetaInput!){
            orderFulfillmentUpdateMeta(id: $id, input: $input) {
                errors {
                    field
                    message
                }
            }
        }
    """


@pytest.fixture
def update_private_metadata_mutation():
    return """
        mutation UpdatePrivateMeta($id: ID!, $input: MetaInput!){
            orderFulfillmentUpdatePrivateMeta(id: $id, input: $input) {
                errors {
                    field
                    message
                }
            }
        }
    """


@pytest.fixture
def clear_metadata_mutation():
    return """
        mutation fulfillmentClearMeta($id: ID!, $input: MetaPath!) {
            orderFulfillmentClearMeta(id: $id, input: $input) {
                errors {
                    message
                }
            }
        }
    """


@pytest.fixture
def clear_private_metadata_mutation():
    return """
        mutation fulfillmentClearPrivateMeta($id: ID!, $input: MetaPath!) {
            orderFulfillmentClearPrivateMeta(id: $id, input: $input) {
                errors {
                    message
                }
            }
        }
    """


@pytest.fixture
def clear_meta_variables(fulfillment):
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    return {
        "id": fulfillment_id,
        "input": {"namespace": "", "clientName": "", "key": "foo"},
    }


@pytest.fixture
def update_metadata_variables(staff_user, fulfillment):
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    return {
        "id": fulfillment_id,
        "input": {
            "namespace": "",
            "clientName": "",
            "key": str(staff_user),
            "value": "bar",
        },
    }


def test_fulfillment_update_metadata_user_has_no_permision(
    staff_api_client, staff_user, update_metadata_mutation, update_metadata_variables
):
    assert not staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)

    response = staff_api_client.post_graphql(
        update_metadata_mutation,
        update_metadata_variables,
        permissions=[],
        check_no_permissions=False,
    )
    assert_no_permission(response)


def test_fulfillment_update_metadata_user_has_permission(
    staff_api_client,
    staff_user,
    permission_manage_orders,
    fulfillment,
    update_metadata_mutation,
    update_metadata_variables,
):
    staff_user.user_permissions.add(permission_manage_orders)
    assert staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    response = staff_api_client.post_graphql(
        update_metadata_mutation,
        update_metadata_variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )
    assert response.status_code == 200
    content = get_graphql_content(response)
    errors = content["data"]["orderFulfillmentUpdateMeta"]["errors"]
    assert len(errors) == 0
    fulfillment.refresh_from_db()
    assert fulfillment.metadata == {str(staff_user): "bar"}


def test_fulfillment_update_private_metadata_user_has_no_permission(
    staff_api_client,
    staff_user,
    update_private_metadata_mutation,
    update_metadata_variables,
):
    assert not staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)

    response = staff_api_client.post_graphql(
        update_private_metadata_mutation,
        update_metadata_variables,
        permissions=[],
        check_no_permissions=False,
    )
    assert_no_permission(response)


def test_fulfillment_update_private_metadata_user_has_permission(
    staff_api_client,
    staff_user,
    permission_manage_orders,
    fulfillment,
    update_private_metadata_mutation,
    update_metadata_variables,
):
    staff_user.user_permissions.add(permission_manage_orders)
    assert staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    response = staff_api_client.post_graphql(
        update_private_metadata_mutation,
        update_metadata_variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )
    assert response.status_code == 200
    content = get_graphql_content(response)
    errors = content["data"]["orderFulfillmentUpdatePrivateMeta"]["errors"]
    assert len(errors) == 0
    fulfillment.refresh_from_db()
    assert fulfillment.private_metadata == {str(staff_user): "bar"}


def test_fulfillment_clear_meta_user_has_no_permission(
    staff_api_client,
    staff_user,
    fulfillment,
    clear_meta_variables,
    clear_metadata_mutation,
):
    assert not staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    fulfillment.store_value_in_metadata(items={"foo": "bar"})
    fulfillment.save()
    response = staff_api_client.post_graphql(
        clear_metadata_mutation, clear_meta_variables
    )
    assert_no_permission(response)


def test_fulfillment_clear_meta_user_has_permission(
    staff_api_client,
    staff_user,
    permission_manage_orders,
    fulfillment,
    clear_meta_variables,
    clear_metadata_mutation,
):
    staff_user.user_permissions.add(permission_manage_orders)
    assert staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    fulfillment.store_value_in_metadata(items={"foo": "bar"})
    fulfillment.save()
    fulfillment.refresh_from_db()
    response = staff_api_client.post_graphql(
        clear_metadata_mutation, clear_meta_variables
    )
    assert response.status_code == 200
    content = get_graphql_content(response)
    assert content.get("errors") is None
    fulfillment.refresh_from_db()
    assert not fulfillment.get_value_from_metadata(key="foo")


def test_fulfillment_clear_private_meta_user_has_no_permission(
    staff_api_client,
    staff_user,
    fulfillment,
    clear_meta_variables,
    clear_private_metadata_mutation,
):
    assert not staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    fulfillment.store_value_in_private_metadata(items={"foo": "bar"})
    fulfillment.save()
    response = staff_api_client.post_graphql(
        clear_private_metadata_mutation, clear_meta_variables
    )
    assert_no_permission(response)


def test_fulfillment_clear_private_meta_user_has_permission(
    staff_api_client,
    staff_user,
    permission_manage_orders,
    fulfillment,
    clear_meta_variables,
    clear_private_metadata_mutation,
):
    staff_user.user_permissions.add(permission_manage_orders)
    assert staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    fulfillment.store_value_in_private_metadata(items={"foo": "bar"})
    fulfillment.save()
    fulfillment.refresh_from_db()
    response = staff_api_client.post_graphql(
        clear_private_metadata_mutation, clear_meta_variables
    )
    assert response.status_code == 200
    content = get_graphql_content(response)
    assert content.get("errors") is None
    fulfillment.refresh_from_db()
    assert not fulfillment.get_value_from_private_metadata(key="foo")


QUERY_FULFILLMENT = """
query fulfillment($id: ID!){
    order(id: $id){
        fulfillments{
            id
            fulfillmentOrder
            status
            trackingNumber
            warehouse{
                id
            }
            lines{
                orderLine{
                    id
                }
                quantity
            }
        }
    }
}
"""


def test_fulfillment_query(
    staff_api_client, fulfilled_order, warehouse, permission_manage_orders,
):
    order = fulfilled_order
    order_line_1, order_line_2 = order.lines.all()
    order_id = graphene.Node.to_global_id("Order", order.pk)
    order_line_1_id = graphene.Node.to_global_id("OrderLine", order_line_1.pk)
    order_line_2_id = graphene.Node.to_global_id("OrderLine", order_line_2.pk)
    warehose_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        QUERY_FULFILLMENT, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["order"]["fulfillments"]
    assert len(data) == 1
    fulfillment_data = data[0]

    assert fulfillment_data["fulfillmentOrder"] == 1
    assert fulfillment_data["status"] == FulfillmentStatus.FULFILLED.upper()
    assert fulfillment_data["trackingNumber"] == "123"
    assert fulfillment_data["warehouse"]["id"] == warehose_id
    assert len(fulfillment_data["lines"]) == 2
    assert {
        "orderLine": {"id": order_line_1_id},
        "quantity": order_line_1.quantity,
    } in fulfillment_data["lines"]
    assert {
        "orderLine": {"id": order_line_2_id},
        "quantity": order_line_2.quantity,
    } in fulfillment_data["lines"]

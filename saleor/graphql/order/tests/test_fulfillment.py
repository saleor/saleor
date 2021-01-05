from decimal import Decimal
from unittest.mock import patch

import graphene
from django.contrib.auth.models import AnonymousUser
from prices import Money, TaxedMoney

from ....core.exceptions import InsufficientStock
from ....core.prices import quantize_price
from ....order import OrderStatus
from ....order.error_codes import OrderErrorCode
from ....order.events import OrderEvents
from ....order.models import FulfillmentStatus
from ....payment import ChargeStatus
from ....warehouse.models import Allocation, Stock
from ...tests.utils import assert_no_permission, get_graphql_content

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
def test_order_fulfill_as_app(
    mock_create_fulfillments,
    app_api_client,
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
    response = app_api_client.post_graphql(
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
        AnonymousUser(), order, fulfillment_lines_for_warehouses, True
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
    staff_api_client,
    fulfilled_order,
    warehouse,
    permission_manage_orders,
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


QUERY_ORDER_FULFILL_DATA = """
query OrderFulfillData($id: ID!) {
    order(id: $id) {
        id
        lines {
            variant {
                stocks {
                    warehouse {
                        id
                    }
                    quantity
                    quantityAllocated
                }
            }
        }
    }
}
"""


def test_staff_can_query_order_fulfill_data(
    staff_api_client, order_with_lines, permission_manage_orders
):
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        QUERY_ORDER_FULFILL_DATA, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["order"]["lines"]
    assert len(data) == 2
    assert data[0]["variant"]["stocks"][0]["quantity"] == 5
    assert data[0]["variant"]["stocks"][0]["quantityAllocated"] == 3
    assert data[1]["variant"]["stocks"][0]["quantity"] == 2
    assert data[1]["variant"]["stocks"][0]["quantityAllocated"] == 2


def test_staff_can_query_order_fulfill_data_without_permission(
    staff_api_client, order_with_lines
):
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(QUERY_ORDER_FULFILL_DATA, variables)
    assert_no_permission(response)


ORDER_FULFILL_REFUND_MUTATION = """
mutation OrderFulfillmentRefundProducts(
    $order: ID!, $input: OrderRefundProductsInput!
) {
    orderFulfillmentRefundProducts(
        order: $order,
        input: $input
    ) {
        fulfillment{
            id
            status
            lines{
                id
                quantity
                orderLine{
                    id
                }
            }
        }
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


def test_fulfillment_refund_products_order_without_payment(
    staff_api_client, permission_manage_orders, fulfilled_order
):
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {"order": order_id, "input": {"amountToRefund": "11.00"}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    fulfillment = data["fulfillment"]
    errors = data["orderErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "order"
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_amount_and_shipping_costs(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    amount_to_refund = Decimal("11.00")
    variables = {
        "order": order_id,
        "input": {"amountToRefund": amount_to_refund, "includeShippingCosts": True},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)

    mocked_refund.assert_called_with(
        payment_dummy, quantize_price(amount_to_refund, fulfilled_order.currency)
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
):
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 2}]},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["orderErrors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2
    mocked_refund.assert_called_with(
        payment_dummy, line_to_refund.unit_price_gross_amount * 2
    )


def test_fulfillment_refund_products_order_lines_quantity_bigger_than_total(
    staff_api_client, permission_manage_orders, order_with_lines, payment_dummy
):
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 200}]},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["orderErrors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "orderLineId"
    assert errors[0]["code"] == OrderErrorCode.INVALID_REFUND_QUANTITY.name
    assert refund_fulfillment is None


def test_fulfillment_refund_products_order_lines_quantity_bigger_than_unfulfilled(
    staff_api_client, permission_manage_orders, order_with_lines, payment_dummy
):
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    line_to_refund.quantity = 3
    line_to_refund.quantity_fulfilled = 3
    line_to_refund.save()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 1}]},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["orderErrors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "orderLineId"
    assert errors[0]["code"] == OrderErrorCode.INVALID_REFUND_QUANTITY.name
    assert refund_fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    order_line_id = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_refund.order_line.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ]
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["orderErrors"]

    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2
    mocked_refund.assert_called_with(
        payment_dummy, fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2
    )


def test_fulfillment_refund_products_fulfillment_lines_quantity_bigger_than_total(
    staff_api_client, permission_manage_orders, fulfilled_order, payment_dummy
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 200}
            ]
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]

    errors = data["orderErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "fulfillmentLineId"
    assert errors[0]["code"] == OrderErrorCode.INVALID_REFUND_QUANTITY.name
    assert refund_fulfillment is None


def test_fulfillment_refund_products_amount_bigger_than_captured_amount(
    staff_api_client, permission_manage_orders, fulfilled_order, payment_dummy
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "amountToRefund": "1000.00",
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]

    errors = data["orderErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amountToRefund"
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert refund_fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines_include_shipping_costs(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    order_line_id = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_refund.order_line.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "includeShippingCosts": True,
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["orderErrors"]

    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2
    amount = fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2
    amount += fulfilled_order.shipping_price_gross_amount
    mocked_refund.assert_called_with(payment_dummy, amount)


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines_include_shipping_costs(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
):
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {
            "includeShippingCosts": True,
            "orderLines": [{"orderLineId": line_id, "quantity": 2}],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["orderErrors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2
    amount = line_to_refund.unit_price_gross_amount * 2
    amount += order_with_lines.shipping_price_gross_amount
    mocked_refund.assert_called_with(payment_dummy, amount)


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines_custom_amount(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    amount_to_refund = Decimal("10.99")
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    order_line_id = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_refund.order_line.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "amountToRefund": amount_to_refund,
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["orderErrors"]

    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2
    mocked_refund.assert_called_with(payment_dummy, amount_to_refund)


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines_custom_amount(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
):
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    amount_to_refund = Decimal("10.99")
    line_to_refund = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {
            "amountToRefund": amount_to_refund,
            "orderLines": [{"orderLineId": line_id, "quantity": 2}],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["orderErrors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2
    mocked_refund.assert_called_with(payment_dummy, amount_to_refund)


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines_and_order_lines(
    mocked_refund,
    warehouse,
    variant,
    channel_USD,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
    collection,
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)

    net = variant.get_price(
        variant.product, [collection], channel_USD, variant_channel_listing, []
    )
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    variant.track_inventory = False
    variant.save()
    quantity = 5
    total_price = TaxedMoney(net=net * quantity, gross=gross * quantity)
    order_line = fulfilled_order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        quantity_fulfilled=2,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        total_price=total_price,
        tax_rate=Decimal("0.23"),
    )
    fulfillment = fulfilled_order.fulfillments.get()
    fulfillment.lines.create(order_line=order_line, quantity=2, stock=stock)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    order_line_from_fulfillment_line = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_refund.order_line.pk
    )
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)
    variables = {
        "order": order_id,
        "input": {
            "orderLines": [{"orderLineId": order_line_id, "quantity": 2}],
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["orderErrors"]

    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 2
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] in [
        order_line_id,
        order_line_from_fulfillment_line,
    ]
    assert refund_fulfillment["lines"][0]["quantity"] == 2

    assert refund_fulfillment["lines"][1]["orderLine"]["id"] in [
        order_line_id,
        order_line_from_fulfillment_line,
    ]
    assert refund_fulfillment["lines"][1]["quantity"] == 2
    amount = fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2
    amount += order_line.unit_price_gross_amount * 2
    amount = quantize_price(amount, fulfilled_order.currency)
    mocked_refund.assert_called_with(payment_dummy, amount)

from decimal import Decimal

import graphene

from .....order import FulfillmentStatus
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_FULFILLMENT = """
    query fulfillment($id: ID!) {
        order(id: $id) {
            fulfillments {
                id
                fulfillmentOrder
                status
                trackingNumber
                warehouse {
                    id
                }
                shippingRefundedAmount {
                    amount
                }
                totalRefundedAmount {
                    amount
                }
                lines {
                    orderLine {
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
    # given
    order = fulfilled_order
    order_line_1, order_line_2 = order.lines.all()
    order_id = graphene.Node.to_global_id("Order", order.pk)
    order_line_1_id = graphene.Node.to_global_id("OrderLine", order_line_1.pk)
    order_line_2_id = graphene.Node.to_global_id("OrderLine", order_line_2.pk)
    warehose_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_orders)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(QUERY_FULFILLMENT, variables)

    # then
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


def test_fulfillment_with_refund_details(
    staff_api_client,
    fulfilled_order,
    warehouse,
    permission_manage_orders,
):
    # given
    order = fulfilled_order
    order_id = graphene.Node.to_global_id("Order", order.pk)
    fulfillment = order.fulfillments.first()
    shipping_refund_amount = Decimal("10")
    total_refund_amount = Decimal("15")
    fulfillment.shipping_refund_amount = shipping_refund_amount
    fulfillment.total_refund_amount = total_refund_amount
    fulfillment.save()

    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_orders)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(QUERY_FULFILLMENT, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["order"]["fulfillments"]
    assert len(data) == 1
    fulfillment_data = data[0]

    assert (
        fulfillment_data["shippingRefundedAmount"]["amount"] == shipping_refund_amount
    )
    assert fulfillment_data["totalRefundedAmount"]["amount"] == total_refund_amount

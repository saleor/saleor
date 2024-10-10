from collections import namedtuple

import graphene
import pytest

from ....models import FulfillmentLine, FulfillmentStatus, OrderLine


@pytest.fixture
def fulfillment(fulfilled_order):
    return fulfilled_order.fulfillments.first()


@pytest.fixture
def fulfillment_awaiting_approval(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])

    quantity = 1
    fulfillment_lines_to_update = []
    order_lines_to_update = []
    for f_line in fulfillment.lines.all():
        f_line.quantity = quantity
        fulfillment_lines_to_update.append(f_line)

        order_line = f_line.order_line
        order_line.quantity_fulfilled = quantity
        order_lines_to_update.append(order_line)

    FulfillmentLine.objects.bulk_update(fulfillment_lines_to_update, ["quantity"])
    OrderLine.objects.bulk_update(order_lines_to_update, ["quantity_fulfilled"])

    return fulfillment


@pytest.fixture
def order_fulfill_data(order_with_lines, warehouse, checkout):
    FulfillmentData = namedtuple("FulfillmentData", "order variables warehouse")
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line, order_line2 = order.lines.all()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    order_line2_id = graphene.Node.to_global_id("OrderLine", order_line2.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": False,
            "allowStockToBeExceeded": True,
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

    return FulfillmentData(order, variables, warehouse)

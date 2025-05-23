from typing import NamedTuple

import graphene
import pytest

from ....warehouse.models import Stock, Warehouse
from ...models import FulfillmentLine, FulfillmentStatus, Order, OrderLine


@pytest.fixture
def fulfillment(fulfilled_order):
    return fulfilled_order.fulfillments.first()


@pytest.fixture
def full_fulfillment_awaiting_approval(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])

    fulfillment_lines_to_update = []
    order_lines_to_update = []
    for f_line in fulfillment.lines.all():
        order_line = f_line.order_line
        f_line.stock.quantity = order_line.quantity
        f_line.quantity = order_line.quantity
        fulfillment_lines_to_update.append(f_line)

        order_line.quantity_fulfilled = order_line.quantity
        order_lines_to_update.append(order_line)

    Stock.objects.bulk_update(
        [line.stock for line in fulfillment_lines_to_update], ["quantity"]
    )
    FulfillmentLine.objects.bulk_update(fulfillment_lines_to_update, ["quantity"])
    OrderLine.objects.bulk_update(order_lines_to_update, ["quantity_fulfilled"])

    return fulfillment


@pytest.fixture
def partial_fulfillment_awaiting_approval(full_fulfillment_awaiting_approval):
    fulfillment = full_fulfillment_awaiting_approval
    quantity = 1
    fulfillment_lines_to_update = []
    order_lines_to_update = []
    for f_line in fulfillment.lines.all():
        f_line.stock.quantity = quantity
        f_line.quantity = quantity
        fulfillment_lines_to_update.append(f_line)

        order_line = f_line.order_line
        order_line.quantity_fulfilled = quantity
        order_lines_to_update.append(order_line)

    Stock.objects.bulk_update(
        [line.stock for line in fulfillment_lines_to_update], ["quantity"]
    )
    FulfillmentLine.objects.bulk_update(fulfillment_lines_to_update, ["quantity"])
    OrderLine.objects.bulk_update(order_lines_to_update, ["quantity_fulfilled"])

    return fulfillment


@pytest.fixture
def order_fulfill_data(order_with_lines, warehouse, checkout):
    class FulfillmentData(NamedTuple):
        order: Order
        variables: dict
        warehouse: Warehouse

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

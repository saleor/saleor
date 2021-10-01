import graphene

from saleor.order import OrderStatus


def assert_order_and_payment_ids(content, payment):
    data = content["data"]["orderByToken"]
    expected_order_id = graphene.Node.to_global_id("Order", payment.order.pk)
    assert data["id"] == expected_order_id

    expected_payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    assert data["payments"][0]["id"] == expected_payment_id


def assert_order_fulfilled(order):
    assert order.status == OrderStatus.FULFILLED

    order_lines = order.lines.all()
    assert order_lines[0].quantity_fulfilled == 3
    assert order_lines[0].quantity_unfulfilled == 0

    assert order_lines[1].quantity_fulfilled == 2
    assert order_lines[1].quantity_unfulfilled == 0


def assert_order_not_fulfilled(order):
    assert not order.status == OrderStatus.FULFILLED

    order_lines = order.lines.all()
    assert order_lines[0].quantity_fulfilled == 0
    assert order_lines[0].quantity_unfulfilled == 3

    assert order_lines[1].quantity_fulfilled == 0
    assert order_lines[1].quantity_unfulfilled == 2

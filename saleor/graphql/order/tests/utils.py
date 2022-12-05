import graphene

from ....order import OrderStatus


def assert_order_and_payment_ids(content, payment):
    data = content["data"]["orderByToken"]
    expected_order_id = graphene.Node.to_global_id("Order", payment.order.pk)
    assert data["id"] == expected_order_id

    expected_payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    assert data["payments"][0]["id"] == expected_payment_id


def assert_proper_webhook_called_once(order, status, draft_mock, order_mock):
    if status == OrderStatus.DRAFT:
        draft_mock.assert_called_once_with(order)
        order_mock.assert_not_called()
    else:
        draft_mock.assert_not_called()
        order_mock.assert_called_once_with(order)

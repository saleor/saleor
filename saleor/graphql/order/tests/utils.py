import graphene


def assert_order_and_payment_ids(content, payment):
    data = content["data"]["orderByToken"]
    expected_order_id = graphene.Node.to_global_id("Order", payment.order.pk)
    assert data["id"] == expected_order_id

    expected_payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    assert data["payments"][0]["id"] == expected_payment_id

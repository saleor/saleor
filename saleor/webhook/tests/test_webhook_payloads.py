import json

import graphene

from ..payloads import ORDER_FIELDS, generate_order_payload


def test_generate_order_payload(
    order_with_lines, fulfilled_order, payment_txn_captured
):
    order_with_lines.discount_name = "Test discount"
    order_with_lines.translated_discount_name = "Translated discount"
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    payload = json.loads(generate_order_payload(order_with_lines))[0]

    assert order_id == payload["id"]
    for field in ORDER_FIELDS:
        assert payload.get(field) is not None

    assert payload.get("payments")
    assert payload.get("shipping_method")
    assert payload.get("lines")
    assert payload.get("payments")
    assert payload.get("shipping_address")
    assert payload.get("billing_address")
    assert payload.get("fulfillments")

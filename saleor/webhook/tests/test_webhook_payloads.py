import json
from decimal import Decimal

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
    assert payload.get("shipping_tax_rate")
    assert payload.get("lines")
    assert payload.get("payments")
    assert payload.get("shipping_address")
    assert payload.get("billing_address")
    assert payload.get("fulfillments")


def test_order_lines_have_all_required_fields(order, order_line_with_one_allocation):
    order.lines.add(order_line_with_one_allocation)
    line = order_line_with_one_allocation
    payload = json.loads(generate_order_payload(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    line_payload = lines_payload[0]
    unit_net_amount = line.unit_price_net_amount.quantize(Decimal("0.001"))
    unit_gross_amount = line.unit_price_gross_amount.quantize(Decimal("0.001"))
    total_line = line.total_price
    assert line_payload == {
        "id": line_id,
        "type": "OrderLine",
        "product_name": line.product_name,
        "variant_name": line.variant_name,
        "translated_product_name": line.translated_product_name,
        "translated_variant_name": line.translated_variant_name,
        "product_sku": line.product_sku,
        "quantity": line.quantity,
        "currency": line.currency,
        "unit_price_net_amount": str(unit_net_amount),
        "unit_price_gross_amount": str(unit_gross_amount),
        "total_price_net_amount": str(total_line.net.amount.quantize(Decimal("0.001"))),
        "total_price_gross_amount": str(
            total_line.gross.amount.quantize(Decimal("0.001"))
        ),
        "tax_rate": str(line.tax_rate.quantize(Decimal("0.0001"))),
    }

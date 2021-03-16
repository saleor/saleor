import json
from decimal import Decimal
from itertools import chain
from unittest.mock import ANY

import graphene

from ...discount import DiscountValueType, OrderDiscountType
from ...product.models import ProductVariant
from ..payloads import (
    ORDER_FIELDS,
    PRODUCT_VARIANT_FIELDS,
    generate_order_payload,
    generate_product_variant_payload,
)


def test_generate_order_payload(
    order_with_lines, fulfilled_order, payment_txn_captured
):
    order_with_lines.discounts.create(
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("20"),
        amount_value=Decimal("33.0"),
        reason="Discount from staff",
    )
    order_with_lines.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("10"),
        amount_value=Decimal("16.5"),
        name="Voucher",
    )

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
    assert payload.get("discounts")


def test_order_lines_have_all_required_fields(order, order_line_with_one_allocation):
    order.lines.add(order_line_with_one_allocation)
    line = order_line_with_one_allocation
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.save()

    payload = json.loads(generate_order_payload(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    line_payload = lines_payload[0]
    unit_net_amount = line.unit_price_net_amount.quantize(Decimal("0.001"))
    unit_gross_amount = line.unit_price_gross_amount.quantize(Decimal("0.001"))
    unit_discount_amount = line.unit_discount_amount.quantize(Decimal("0.001"))

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
        "unit_discount_amount": str(unit_discount_amount),
        "unit_discount_type": line.unit_discount_type,
        "unit_discount_reason": line.unit_discount_reason,
        "unit_price_net_amount": str(unit_net_amount),
        "unit_price_gross_amount": str(unit_gross_amount),
        "total_price_net_amount": str(total_line.net.amount.quantize(Decimal("0.001"))),
        "total_price_gross_amount": str(
            total_line.gross.amount.quantize(Decimal("0.001"))
        ),
        "tax_rate": str(line.tax_rate.quantize(Decimal("0.0001"))),
    }


def test_generate_product_variant_payload(
    product_with_variant_with_two_attributes, product_with_images
):
    variant = product_with_variant_with_two_attributes.variants.first()
    payload = json.loads(generate_product_variant_payload(variant))[0]
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )

    for field in payload_fields:
        assert payload.get(field) is not None

    assert variant_id is not None
    assert payload["sku"] == "prodVar1"
    assert len(payload["attributes"]) == 2
    assert len(payload["channel_listings"]) == 1
    assert payload["channel_listings"][0] == {
        "cost_price_amount": "1.000",
        "currency": "USD",
        "id": ANY,
        "price_amount": "10.000",
        "type": "ProductVariantChannelListing",
    }
    assert len(payload.keys()) == len(payload_fields)


def test_generate_product_variant_with_external_media_payload(
    product_with_variant_with_external_media,
):
    variant = product_with_variant_with_external_media.variants.first()
    payload = json.loads(generate_product_variant_payload(variant))[0]
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )

    for field in payload_fields:
        assert payload.get(field) is not None

    assert variant_id is not None
    assert payload["sku"] == "prodVar1"
    assert payload["media"] == [
        {"alt": "video_1", "url": "https://www.youtube.com/watch?v=di8_dJ3Clyo"}
    ]
    assert len(payload["attributes"]) == 2
    assert len(payload["channel_listings"]) == 1
    assert payload["channel_listings"][0] == {
        "cost_price_amount": "1.000",
        "currency": "USD",
        "id": ANY,
        "price_amount": "10.000",
        "type": "ProductVariantChannelListing",
    }
    assert len(payload.keys()) == len(payload_fields)


def test_generate_product_variant_deleted_payload(
    product_with_variant_with_two_attributes,
):
    variant = product_with_variant_with_two_attributes.variants.prefetch_related(
        "channel_listings",
        "attributes__values",
        "variant_media",
    ).first()
    ProductVariant.objects.filter(id=variant.id).delete()
    payload = json.loads(generate_product_variant_payload(variant))[0]
    [_, payload_variant_id] = graphene.Node.from_global_id(payload["id"])
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )
    for field in payload_fields:
        assert payload.get(field) is not None

    assert payload_variant_id != "None"
    assert payload["sku"] == "prodVar1"
    assert len(payload["attributes"]) == 2
    assert len(payload["channel_listings"]) == 1
    assert len(payload.keys()) == len(payload_fields)

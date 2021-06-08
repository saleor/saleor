import json
from dataclasses import asdict
from decimal import Decimal
from itertools import chain
from unittest import mock
from unittest.mock import ANY

import graphene

from ...core.utils.json_serializer import CustomJsonEncoder
from ...discount import DiscountValueType, OrderDiscountType
from ...order import OrderLineData, OrderOrigin
from ...order.actions import fulfill_order_lines
from ...order.models import Order
from ...plugins.webhook.utils import from_payment_app_id
from ...product.models import ProductVariant
from ..payloads import (
    ORDER_FIELDS,
    PRODUCT_VARIANT_FIELDS,
    generate_checkout_payload,
    generate_fulfillment_lines_payload,
    generate_invoice_payload,
    generate_list_gateways_payload,
    generate_order_payload,
    generate_payment_payload,
    generate_product_variant_payload,
)


@mock.patch("saleor.webhook.payloads.generate_fulfillment_lines_payload")
def test_generate_order_payload(
    mocked_fulfillment_lines, order_with_lines, fulfilled_order, payment_txn_captured
):
    mocked_fulfillment_lines.return_value = "{}"

    payment_txn_captured.psp_reference = "123"
    payment_txn_captured.save(update_fields=["psp_reference"])

    new_order = Order.objects.create(
        channel=order_with_lines.channel,
        billing_address=order_with_lines.billing_address,
    )
    order_with_lines.origin = OrderOrigin.REISSUE
    order_with_lines.original = new_order
    order_with_lines.save(update_fields=["origin", "original"])

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

    assert fulfilled_order.fulfillments.count() == 1
    fulfillment = fulfilled_order.fulfillments.first()

    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    payload = json.loads(generate_order_payload(order_with_lines))[0]

    assert order_id == payload["id"]
    for field in ORDER_FIELDS:
        assert payload.get(field) is not None

    assert payload.get("shipping_method")
    assert payload.get("shipping_tax_rate")
    assert payload.get("lines")
    assert payload.get("shipping_address")
    assert payload.get("billing_address")
    assert payload.get("fulfillments")
    assert payload.get("discounts")
    assert payload.get("original") == graphene.Node.to_global_id("Order", new_order.pk)
    assert payload.get("payments")
    assert len(payload.get("payments")) == 1
    payments_data = payload.get("payments")[0]
    assert payments_data == {
        "id": graphene.Node.to_global_id("Payment", payment_txn_captured.pk),
        "gateway": payment_txn_captured.gateway,
        "payment_method_type": payment_txn_captured.payment_method_type,
        "cc_brand": payment_txn_captured.cc_brand,
        "is_active": payment_txn_captured.is_active,
        "created": ANY,
        "modified": ANY,
        "charge_status": payment_txn_captured.charge_status,
        "psp_reference": payment_txn_captured.psp_reference,
        "total": str(payment_txn_captured.total),
        "type": "Payment",
        "captured_amount": str(payment_txn_captured.captured_amount),
        "currency": payment_txn_captured.currency,
        "billing_email": payment_txn_captured.billing_email,
        "billing_first_name": payment_txn_captured.billing_first_name,
        "billing_last_name": payment_txn_captured.billing_last_name,
        "billing_company_name": payment_txn_captured.billing_company_name,
        "billing_address_1": payment_txn_captured.billing_address_1,
        "billing_address_2": payment_txn_captured.billing_address_2,
        "billing_city": payment_txn_captured.billing_city,
        "billing_city_area": payment_txn_captured.billing_city_area,
        "billing_postal_code": payment_txn_captured.billing_postal_code,
        "billing_country_code": payment_txn_captured.billing_country_code,
        "billing_country_area": payment_txn_captured.billing_country_area,
    }

    mocked_fulfillment_lines.assert_called_with(fulfillment)


def test_generate_fulfillment_lines_payload(order_with_lines):
    fulfillment = order_with_lines.fulfillments.create(tracking_number="123")
    line = order_with_lines.lines.first()
    stock = line.allocations.get().stock
    warehouse_pk = stock.warehouse.pk
    fulfillment_line = fulfillment.lines.create(
        order_line=line, quantity=line.quantity, stock=stock
    )
    fulfill_order_lines(
        [
            OrderLineData(line=line, quantity=line.quantity, warehouse_pk=warehouse_pk),
        ]
    )
    payload = json.loads(generate_fulfillment_lines_payload(fulfillment))[0]

    assert payload == {
        "currency": "USD",
        "product_name": line.product_name,
        "variant_name": line.variant_name,
        "product_sku": line.product_sku,
        "id": graphene.Node.to_global_id("FulfillmentLine", fulfillment_line.id),
        "product_type": "Default Type",
        "quantity": fulfillment_line.quantity,
        "total_price_gross_amount": str(
            line.unit_price.gross.amount * fulfillment_line.quantity
        ),
        "total_price_net_amount": str(
            line.unit_price.net.amount * fulfillment_line.quantity
        ),
        "type": "FulfillmentLine",
        "undiscounted_unit_price_gross": str(line.undiscounted_unit_price.gross.amount),
        "undiscounted_unit_price_net": str(line.undiscounted_unit_price.net.amount),
        "unit_price_gross": str(line.unit_price.gross.amount),
        "unit_price_net": str(line.unit_price.net.amount),
        "weight": 0.0,
        "weight_unit": "gram",
        "warehouse_id": graphene.Node.to_global_id(
            "Warehouse", fulfillment_line.stock.warehouse_id
        ),
    }


def test_order_lines_have_all_required_fields(order, order_line_with_one_allocation):
    order.lines.add(order_line_with_one_allocation)
    line = order_line_with_one_allocation
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.undiscounted_unit_price = line.unit_price + line.unit_discount
    line.undiscounted_total_price = line.undiscounted_unit_price * line.quantity
    line.save()

    payload = json.loads(generate_order_payload(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    line_payload = lines_payload[0]
    unit_net_amount = line.unit_price_net_amount.quantize(Decimal("0.001"))
    unit_gross_amount = line.unit_price_gross_amount.quantize(Decimal("0.001"))
    unit_discount_amount = line.unit_discount_amount.quantize(Decimal("0.001"))
    allocation = line.allocations.first()
    undiscounted_unit_price_net_amount = (
        line.undiscounted_unit_price.net.amount.quantize(Decimal("0.001"))
    )
    undiscounted_unit_price_gross_amount = (
        line.undiscounted_unit_price.gross.amount.quantize(Decimal("0.001"))
    )
    undiscounted_total_price_net_amount = (
        line.undiscounted_total_price.net.amount.quantize(Decimal("0.001"))
    )
    undiscounted_total_price_gross_amount = (
        line.undiscounted_total_price.gross.amount.quantize(Decimal("0.001"))
    )

    total_line = line.total_price
    global_warehouse_id = graphene.Node.to_global_id(
        "Warehouse", allocation.stock.warehouse_id
    )
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
        "allocations": [
            {
                "warehouse_id": global_warehouse_id,
                "quantity_allocated": allocation.quantity_allocated,
            }
        ],
        "undiscounted_unit_price_net_amount": str(undiscounted_unit_price_net_amount),
        "undiscounted_unit_price_gross_amount": str(
            undiscounted_unit_price_gross_amount
        ),
        "undiscounted_total_price_net_amount": str(undiscounted_total_price_net_amount),
        "undiscounted_total_price_gross_amount": str(
            undiscounted_total_price_gross_amount
        ),
    }


def test_generate_product_variant_payload(
    product_with_variant_with_two_attributes, product_with_images, channel_USD
):
    variant = product_with_variant_with_two_attributes.variants.first()
    payload = json.loads(generate_product_variant_payload([variant]))[0]
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
        "channel_slug": channel_USD.slug,
        "price_amount": "10.000",
        "type": "ProductVariantChannelListing",
    }
    assert len(payload.keys()) == len(payload_fields)


def test_generate_product_variant_with_external_media_payload(
    product_with_variant_with_external_media, channel_USD
):
    variant = product_with_variant_with_external_media.variants.first()
    payload = json.loads(generate_product_variant_payload([variant]))[0]
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
        "channel_slug": channel_USD.slug,
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
    payload = json.loads(generate_product_variant_payload([variant]))[0]
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


def test_generate_invoice_payload(fulfilled_order):
    fulfilled_order.origin = OrderOrigin.CHECKOUT
    fulfilled_order.save(update_fields=["origin"])
    invoice = fulfilled_order.invoices.first()
    payload = json.loads(generate_invoice_payload(invoice))[0]

    assert payload == {
        "type": "Invoice",
        "id": graphene.Node.to_global_id("Invoice", invoice.id),
        "order": {
            "type": "Order",
            "id": graphene.Node.to_global_id("Order", invoice.order.id),
            "private_metadata": {},
            "metadata": {},
            "created": ANY,
            "status": "fulfilled",
            "origin": OrderOrigin.CHECKOUT,
            "user_email": "test@example.com",
            "shipping_method_name": "DHL",
            "shipping_price_net_amount": "10.000",
            "shipping_price_gross_amount": "12.300",
            "shipping_tax_rate": "0.0000",
            "total_net_amount": "80.000",
            "total_gross_amount": "98.400",
            "weight": "0.0:g",
            "undiscounted_total_net_amount": str(
                fulfilled_order.undiscounted_total_net_amount
            ),
            "undiscounted_total_gross_amount": str(
                fulfilled_order.undiscounted_total_gross_amount
            ),
        },
        "number": "01/12/2020/TEST",
        "created": ANY,
        "external_url": "http://www.example.com/invoice.pdf",
    }


def test_generate_list_gateways_payload(checkout):
    currency = "USD"
    payload = generate_list_gateways_payload(currency, checkout)
    data = json.loads(payload)
    assert data["checkout"] == json.loads(generate_checkout_payload(checkout))[0]
    assert data["currency"] == currency


def test_generate_payment_payload(dummy_webhook_app_payment_data):
    payload = generate_payment_payload(dummy_webhook_app_payment_data)
    expected_payload = asdict(dummy_webhook_app_payment_data)
    expected_payload["payment_method"] = from_payment_app_id(
        dummy_webhook_app_payment_data.gateway
    ).name
    assert payload == json.dumps(expected_payload, cls=CustomJsonEncoder)

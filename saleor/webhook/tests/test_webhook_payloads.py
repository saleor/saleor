import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from itertools import chain
from unittest import mock
from unittest.mock import ANY

import graphene
from django.utils import timezone
from freezegun import freeze_time

from ... import __version__
from ...core.utils.json_serializer import CustomJsonEncoder
from ...discount import DiscountValueType, OrderDiscountType
from ...graphql.utils import get_user_or_app_from_context
from ...order import OrderOrigin
from ...order.actions import fulfill_order_lines
from ...order.fetch import OrderLineInfo
from ...order.models import Order
from ...plugins.manager import get_plugins_manager
from ...plugins.webhook.utils import from_payment_app_id
from ...product.models import ProductVariant
from ...warehouse import WarehouseClickAndCollectOption
from ..payloads import (
    ORDER_FIELDS,
    PRODUCT_VARIANT_FIELDS,
    generate_checkout_payload,
    generate_collection_payload,
    generate_customer_payload,
    generate_fulfillment_lines_payload,
    generate_invoice_payload,
    generate_list_gateways_payload,
    generate_meta,
    generate_order_payload,
    generate_payment_payload,
    generate_product_variant_payload,
    generate_product_variant_with_stock_payload,
    generate_requestor,
    generate_sale_payload,
    generate_translation_payload,
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

    line_without_sku = order_with_lines.lines.last()
    line_without_sku.product_sku = None
    line_without_sku.save()

    assert fulfilled_order.fulfillments.count() == 1
    fulfillment = fulfilled_order.fulfillments.first()

    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    payload = json.loads(generate_order_payload(order_with_lines))[0]

    assert order_id == payload["id"]
    non_empty_fields = [f for f in ORDER_FIELDS if f != "collection_point_name"]
    for field in non_empty_fields:
        assert payload.get(field) is not None

    assert payload["collection_point_name"] is None
    assert payload.get("token") == order_with_lines.token
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
        "total": str(payment_txn_captured.total.quantize(Decimal("0.01"))),
        "type": "Payment",
        "captured_amount": str(
            payment_txn_captured.captured_amount.quantize(Decimal("0.01"))
        ),
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
    line.sale_id = graphene.Node.to_global_id("Sale", 1)
    line.voucher_code = "code"
    line.save()
    stock = line.allocations.get().stock
    warehouse_pk = stock.warehouse.pk
    fulfillment_line = fulfillment.lines.create(
        order_line=line, quantity=line.quantity, stock=stock
    )
    fulfill_order_lines(
        [OrderLineInfo(line=line, quantity=line.quantity, warehouse_pk=warehouse_pk)],
        get_plugins_manager(),
    )
    payload = json.loads(generate_fulfillment_lines_payload(fulfillment))[0]

    undiscounted_unit_price_gross = line.undiscounted_unit_price.gross.amount.quantize(
        Decimal("0.01")
    )
    undiscounted_unit_price_net = line.undiscounted_unit_price.net.amount.quantize(
        Decimal("0.01")
    )
    unit_price_gross = line.unit_price.gross.amount.quantize(Decimal("0.01"))
    unit_price_net = line.unit_price.net.amount.quantize(Decimal("0.01"))

    assert payload == {
        "currency": "USD",
        "product_name": line.product_name,
        "variant_name": line.variant_name,
        "product_sku": line.product_sku,
        "product_variant_id": line.product_variant_id,
        "id": graphene.Node.to_global_id("FulfillmentLine", fulfillment_line.id),
        "product_type": "Default Type",
        "quantity": fulfillment_line.quantity,
        "total_price_gross_amount": str(unit_price_gross * fulfillment_line.quantity),
        "total_price_net_amount": str(unit_price_net * fulfillment_line.quantity),
        "type": "FulfillmentLine",
        "undiscounted_unit_price_gross": str(undiscounted_unit_price_gross),
        "undiscounted_unit_price_net": str(undiscounted_unit_price_net),
        "unit_price_gross": str(unit_price_gross),
        "unit_price_net": str(unit_price_net),
        "weight": 0.0,
        "weight_unit": "gram",
        "warehouse_id": graphene.Node.to_global_id(
            "Warehouse", fulfillment_line.stock.warehouse_id
        ),
        "sale_id": line.sale_id,
        "voucher_code": line.voucher_code,
    }


def test_generate_fulfillment_lines_payload_deleted_variant(order_with_lines):
    # given
    fulfillment = order_with_lines.fulfillments.create(tracking_number="123")
    line = order_with_lines.lines.first()
    stock = line.allocations.get().stock
    warehouse_pk = stock.warehouse.pk
    fulfillment.lines.create(order_line=line, quantity=line.quantity, stock=stock)
    fulfill_order_lines(
        [OrderLineInfo(line=line, quantity=line.quantity, warehouse_pk=warehouse_pk)],
        get_plugins_manager(),
    )

    # when
    line.variant.delete()
    payload = json.loads(generate_fulfillment_lines_payload(fulfillment))[0]

    # then
    assert payload["product_type"] is None
    assert payload["weight"] is None


def test_order_lines_have_all_required_fields(order, order_line_with_one_allocation):
    order.lines.add(order_line_with_one_allocation)
    line = order_line_with_one_allocation
    line.voucher_code = "Voucher001"
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.undiscounted_unit_price = line.unit_price + line.unit_discount
    line.undiscounted_total_price = line.undiscounted_unit_price * line.quantity
    line.sale_id = graphene.Node.to_global_id("Sale", 1)
    line.save()

    payload = json.loads(generate_order_payload(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    line_payload = lines_payload[0]
    unit_net_amount = line.unit_price_net_amount.quantize(Decimal("0.01"))
    unit_gross_amount = line.unit_price_gross_amount.quantize(Decimal("0.01"))
    unit_discount_amount = line.unit_discount_amount.quantize(Decimal("0.01"))
    allocation = line.allocations.first()
    undiscounted_unit_price_net_amount = (
        line.undiscounted_unit_price.net.amount.quantize(Decimal("0.01"))
    )
    undiscounted_unit_price_gross_amount = (
        line.undiscounted_unit_price.gross.amount.quantize(Decimal("0.01"))
    )
    undiscounted_total_price_net_amount = (
        line.undiscounted_total_price.net.amount.quantize(Decimal("0.01"))
    )
    undiscounted_total_price_gross_amount = (
        line.undiscounted_total_price.gross.amount.quantize(Decimal("0.01"))
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
        "product_variant_id": line.product_variant_id,
        "quantity": line.quantity,
        "currency": line.currency,
        "unit_discount_amount": str(unit_discount_amount),
        "unit_discount_type": line.unit_discount_type,
        "unit_discount_reason": line.unit_discount_reason,
        "unit_price_net_amount": str(unit_net_amount),
        "unit_price_gross_amount": str(unit_gross_amount),
        "total_price_net_amount": str(total_line.net.amount.quantize(Decimal("0.01"))),
        "total_price_gross_amount": str(
            total_line.gross.amount.quantize(Decimal("0.01"))
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
        "voucher_code": line.voucher_code,
        "sale_id": line.sale_id,
    }


def test_order_line_without_sku_still_has_id(order, order_line_with_one_allocation):
    order.lines.add(order_line_with_one_allocation)
    line = order_line_with_one_allocation
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.undiscounted_unit_price = line.unit_price + line.unit_discount
    line.undiscounted_total_price = line.undiscounted_unit_price * line.quantity
    line.product_sku = None
    line.save()

    payload = json.loads(generate_order_payload(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1

    line_payload = lines_payload[0]
    assert line_payload["product_sku"] is None
    assert line_payload["product_variant_id"] == line.product_variant_id


def test_generate_collection_payload(collection):
    payload = json.loads(generate_collection_payload(collection))
    expected_payload = [
        {
            "type": "Collection",
            "id": graphene.Node.to_global_id("Collection", collection.id),
            "name": collection.name,
            "description": collection.description,
            "background_image": None,
            "background_image_alt": "",
            "private_metadata": {},
            "metadata": {},
            "meta": {
                "issued_at": ANY,
                "version": __version__,
                "issuing_principal": {"id": None, "type": None},
            },
        }
    ]

    assert payload == expected_payload


def test_generate_base_product_variant_payload(product_with_two_variants):
    stocks_to_serialize = [
        variant.stocks.first() for variant in product_with_two_variants.variants.all()
    ]
    first_stock, second_stock = stocks_to_serialize
    payload = json.loads(
        generate_product_variant_with_stock_payload(stocks_to_serialize)
    )
    expected_payload = [
        {
            "type": "Stock",
            "id": graphene.Node.to_global_id("Stock", first_stock.id),
            "product_id": graphene.Node.to_global_id(
                "Product", first_stock.product_variant.product_id
            ),
            "product_variant_id": graphene.Node.to_global_id(
                "ProductVariant", first_stock.product_variant_id
            ),
            "warehouse_id": graphene.Node.to_global_id(
                "Warehouse", first_stock.warehouse_id
            ),
            "product_slug": "test-product-with-two-variant",
            "meta": {
                "issuing_principal": {"id": None, "type": None},
                "issued_at": ANY,
                "version": __version__,
            },
        },
        {
            "type": "Stock",
            "id": graphene.Node.to_global_id("Stock", second_stock.id),
            "product_id": graphene.Node.to_global_id(
                "Product", second_stock.product_variant.product_id
            ),
            "product_variant_id": graphene.Node.to_global_id(
                "ProductVariant", second_stock.product_variant_id
            ),
            "warehouse_id": graphene.Node.to_global_id(
                "Warehouse", second_stock.warehouse_id
            ),
            "product_slug": "test-product-with-two-variant",
            "meta": {
                "issuing_principal": {"id": None, "type": None},
                "issued_at": ANY,
                "version": __version__,
            },
        },
    ]
    assert payload == expected_payload


def test_generate_product_variant_payload(
    product_with_variant_with_two_attributes,
    product_with_images,
    channel_USD,
    staff_user,
):
    variant = product_with_variant_with_two_attributes.variants.first()
    payload = json.loads(generate_product_variant_payload([variant], staff_user))[0]
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media", "meta"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )

    for field in payload_fields:
        assert payload.get(field) is not None

    assert variant_id is not None
    assert payload["id"] == variant_id
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
    assert payload["meta"] == {
        "issuing_principal": generate_requestor(staff_user),
        "issued_at": ANY,
        "version": __version__,
    }
    assert len(payload.keys()) == len(payload_fields)


def test_generate_product_variant_with_external_media_payload(
    product_with_variant_with_external_media, channel_USD
):
    variant = product_with_variant_with_external_media.variants.first()
    payload = json.loads(generate_product_variant_payload([variant]))[0]
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media", "meta"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )
    for field in payload_fields:
        assert payload.get(field) is not None

    assert variant_id is not None
    assert payload["id"] == variant_id
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


def test_generate_product_variant_without_sku_payload(
    product_with_variant_with_two_attributes, product_with_images, channel_USD
):
    variant = product_with_variant_with_two_attributes.variants.first()
    variant.sku = None
    variant.save()
    payload = json.loads(generate_product_variant_payload([variant]))[0]
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media", "meta"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )
    assert variant_id is not None
    assert payload["id"] == variant_id
    assert payload["sku"] is None
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
    extra_dict_data = ["attributes", "product_id", "media", "meta"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )
    for field in payload_fields:
        assert payload.get(field) is not None

    assert payload_variant_id != "None"
    assert payload["id"] == variant.get_global_id()
    assert payload["sku"] == "prodVar1"
    assert len(payload["attributes"]) == 2
    assert len(payload["channel_listings"]) == 1
    assert len(payload.keys()) == len(payload_fields)


@freeze_time("1914-06-28 10:50")
def test_generate_invoice_payload(fulfilled_order):
    fulfilled_order.origin = OrderOrigin.CHECKOUT
    fulfilled_order.save(update_fields=["origin"])
    invoice = fulfilled_order.invoices.first()
    payload = json.loads(generate_invoice_payload(invoice))[0]
    undiscounted_total_net = fulfilled_order.undiscounted_total_net_amount.quantize(
        Decimal("0.01")
    )
    undiscounted_total_gross = fulfilled_order.undiscounted_total_gross_amount.quantize(
        Decimal("0.01")
    )
    timestamp = timezone.make_aware(
        datetime.strptime("1914-06-28 10:50", "%Y-%m-%d %H:%M"), timezone.utc
    ).isoformat()

    assert payload == {
        "type": "Invoice",
        "id": graphene.Node.to_global_id("Invoice", invoice.id),
        "meta": {
            "issued_at": timestamp,
            "issuing_principal": {"id": None, "type": None},
            "version": __version__,
        },
        "order": {
            "type": "Order",
            "token": invoice.order.token,
            "id": graphene.Node.to_global_id("Order", invoice.order.id),
            "private_metadata": {},
            "metadata": {},
            "created": ANY,
            "status": "fulfilled",
            "origin": OrderOrigin.CHECKOUT,
            "user_email": "test@example.com",
            "shipping_method_name": "DHL",
            "collection_point_name": None,
            "shipping_price_net_amount": "10.00",
            "shipping_price_gross_amount": "12.30",
            "shipping_tax_rate": "0.0000",
            "total_net_amount": "80.00",
            "total_gross_amount": "98.40",
            "weight": "0.0:g",
            "undiscounted_total_net_amount": str(undiscounted_total_net),
            "undiscounted_total_gross_amount": str(undiscounted_total_gross),
        },
        "number": "01/12/2020/TEST",
        "created": ANY,
        "external_url": "http://www.example.com/invoice.pdf",
    }


@freeze_time("1914-06-28 10:50")
def test_generate_list_gateways_payload(checkout):
    currency = "USD"
    payload = generate_list_gateways_payload(currency, checkout)
    data = json.loads(payload)
    assert data["checkout"] == json.loads(generate_checkout_payload(checkout))[0]
    assert data["currency"] == currency


@freeze_time("1914-06-28 10:50")
def test_generate_payment_payload(dummy_webhook_app_payment_data):
    payload = generate_payment_payload(dummy_webhook_app_payment_data)
    expected_payload = asdict(dummy_webhook_app_payment_data)
    expected_payload["amount"] = Decimal(expected_payload["amount"]).quantize(
        Decimal("0.01")
    )
    expected_payload["payment_method"] = from_payment_app_id(
        dummy_webhook_app_payment_data.gateway
    ).name
    expected_payload["meta"] = generate_meta(requestor_data=generate_requestor())

    assert payload == json.dumps(expected_payload, cls=CustomJsonEncoder)


def test_generate_checkout_lines_payload(checkout_with_single_item):
    payload = json.loads(generate_checkout_payload(checkout_with_single_item))[0]
    assert payload.get("lines")

    variant = checkout_with_single_item.lines.first().variant
    line = payload["lines"][0]
    assert line["sku"] == variant.sku
    assert line["variant_id"] == variant.get_global_id()


def test_generate_product_translation_payload(product_translation_fr):
    payload = generate_translation_payload(product_translation_fr)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "Product", product_translation_fr.product_id
    )
    assert data["language_code"] == product_translation_fr.language_code
    assert "product_id" not in data.keys()
    assert "product_variant_id" not in data.keys()
    assert "attribute_id" not in data.keys()
    assert "page_id" not in data.keys()

    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["name"] == product_translation_fr.name
    assert translation_keys["description"] == product_translation_fr.description


def test_generate_product_variant_translation_payload(variant_translation_fr):
    payload = generate_translation_payload(variant_translation_fr)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "ProductVariant", variant_translation_fr.product_variant_id
    )
    assert data["language_code"] == variant_translation_fr.language_code
    assert "product_id" not in data.keys()
    assert "product_variant_id" not in data.keys()
    assert "attribute_id" not in data.keys()
    assert "page_id" not in data.keys()

    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["name"] == variant_translation_fr.name


def test_generate_choices_attribute_value_translation_payload(
    translated_attribute_value, color_attribute
):
    payload = generate_translation_payload(translated_attribute_value)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "AttributeValue", translated_attribute_value.attribute_value_id
    )
    assert data["language_code"] == translated_attribute_value.language_code
    assert data["product_id"] is None
    assert data["product_variant_id"] is None
    assert data["attribute_id"] == graphene.Node.to_global_id(
        "Attribute", color_attribute.id
    )
    assert data["page_id"] is None

    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["name"] == translated_attribute_value.name


def test_generate_unique_product_attribute_value_translation_payload(
    translated_product_unique_attribute_value, product, rich_text_attribute
):
    translated_attribute_value = translated_product_unique_attribute_value
    payload = generate_translation_payload(translated_attribute_value)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "AttributeValue", translated_attribute_value.attribute_value_id
    )
    assert data["language_code"] == translated_attribute_value.language_code
    assert data["product_id"] == graphene.Node.to_global_id("Product", product.id)
    assert data["product_variant_id"] is None
    assert data["attribute_id"] == graphene.Node.to_global_id(
        "Attribute", rich_text_attribute.id
    )
    assert data["page_id"] is None
    assert data["page_type_id"] is None
    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["rich_text"] == translated_attribute_value.rich_text


def test_generate_unique_variant_attribute_value_translation_payload(
    translated_variant_unique_attribute_value, variant, rich_text_attribute
):
    translated_attribute_value = translated_variant_unique_attribute_value
    payload = generate_translation_payload(translated_attribute_value)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "AttributeValue", translated_attribute_value.attribute_value_id
    )
    assert data["language_code"] == translated_attribute_value.language_code
    assert data["product_id"] == graphene.Node.to_global_id(
        "Product", variant.product_id
    )
    assert data["product_variant_id"] == graphene.Node.to_global_id(
        "ProductVariant", variant.id
    )
    assert data["attribute_id"] == graphene.Node.to_global_id(
        "Attribute", rich_text_attribute.id
    )
    assert data["page_id"] is None
    assert data["page_type_id"] is None
    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["rich_text"] == translated_attribute_value.rich_text


def test_generate_unique_page_attribute_value_translation_payload(
    translated_page_unique_attribute_value,
    page,
    rich_text_attribute_page_type,
):
    translated_attribute_value = translated_page_unique_attribute_value
    payload = generate_translation_payload(translated_attribute_value)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "AttributeValue", translated_attribute_value.attribute_value_id
    )
    assert data["language_code"] == translated_attribute_value.language_code
    assert data["product_id"] is None
    assert data["product_variant_id"] is None
    assert data["attribute_id"] == graphene.Node.to_global_id(
        "Attribute", rich_text_attribute_page_type.id
    )
    assert data["page_id"] == graphene.Node.to_global_id("Page", page.id)
    assert data["page_type_id"] == graphene.Node.to_global_id(
        "PageType", page.page_type_id
    )
    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["rich_text"] == translated_attribute_value.rich_text


@freeze_time("1914-06-28 10:50")
def test_generate_customer_payload(customer_user, address_other_country, address):

    customer = customer_user
    customer.default_billing_address = address_other_country
    customer.save()
    payload = json.loads(generate_customer_payload(customer))[0]
    timestamp = timezone.make_aware(
        datetime.strptime("1914-06-28 10:50", "%Y-%m-%d %H:%M"), timezone.utc
    ).isoformat()

    expected_payload = {
        "type": "User",
        "id": graphene.Node.to_global_id("User", customer.id),
        "meta": {
            "issuing_principal": {"id": None, "type": None},
            "issued_at": timestamp,
            "version": __version__,
        },
        "default_shipping_address": {
            "type": "Address",
            "id": graphene.Node.to_global_id(
                "Address", customer.default_shipping_address_id
            ),
            "first_name": customer.default_shipping_address.first_name,
            "last_name": customer.default_shipping_address.last_name,
            "company_name": customer.default_shipping_address.company_name,
            "street_address_1": customer.default_shipping_address.street_address_1,
            "street_address_2": customer.default_shipping_address.street_address_2,
            "city": customer.default_shipping_address.city,
            "city_area": customer.default_shipping_address.city_area,
            "postal_code": customer.default_shipping_address.postal_code,
            "country": customer.default_shipping_address.country,
            "country_area": customer.default_shipping_address.country_area,
            "phone": customer.default_shipping_address.phone,
        },
        "default_billing_address": {
            "type": "Address",
            "id": graphene.Node.to_global_id(
                "Address", customer.default_billing_address_id
            ),
            "first_name": customer.default_billing_address.first_name,
            "last_name": customer.default_billing_address.last_name,
            "company_name": customer.default_billing_address.company_name,
            "street_address_1": customer.default_billing_address.street_address_1,
            "street_address_2": customer.default_billing_address.street_address_2,
            "city": customer.default_billing_address.city,
            "city_area": customer.default_billing_address.city_area,
            "postal_code": customer.default_billing_address.postal_code,
            "country": customer.default_billing_address.country,
            "country_area": customer.default_billing_address.country_area,
            "phone": customer.default_billing_address.phone,
        },
        "addresses": [
            {
                "type": "Address",
                "id": graphene.Node.to_global_id(
                    "Address", customer.default_shipping_address_id
                ),
                "first_name": customer.default_shipping_address.first_name,
                "last_name": customer.default_shipping_address.last_name,
                "company_name": customer.default_shipping_address.company_name,
                "street_address_1": customer.default_shipping_address.street_address_1,
                "street_address_2": customer.default_shipping_address.street_address_2,
                "city": customer.default_shipping_address.city,
                "city_area": customer.default_shipping_address.city_area,
                "postal_code": customer.default_shipping_address.postal_code,
                "country": customer.default_shipping_address.country,
                "country_area": customer.default_shipping_address.country_area,
                "phone": customer.default_shipping_address.phone,
            }
        ],
        "private_metadata": customer.private_metadata,
        "metadata": customer.metadata,
        "email": customer.email,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "is_active": customer.is_active,
        "date_joined": ANY,
    }

    assert payload == expected_payload


def test_generate_collection_point_payload(order_with_lines_for_cc):
    payload = json.loads(generate_order_payload(order_with_lines_for_cc))[0]

    payload_collection_point = payload.get("collection_point")

    assert payload_collection_point
    assert payload_collection_point.get("address")
    assert payload_collection_point.get("email") == "local@example.com"
    assert payload_collection_point.get("name") == "Local Warehouse"
    assert not payload_collection_point.get("is_private")
    assert (
        payload_collection_point.get("click_and_collect_option")
        == WarehouseClickAndCollectOption.LOCAL_STOCK
    )


def test_generate_sale_payload_no_previous_and_current_has_empty_catalogue_lists(sale):
    payload = json.loads(generate_sale_payload(sale))[0]

    assert not payload["categories_added"]
    assert not payload["categories_removed"]
    assert not payload["collections_added"]
    assert not payload["collections_removed"]
    assert not payload["products_added"]
    assert not payload["products_removed"]

    assert graphene.Node.to_global_id("Sale", sale.id) == payload["id"]


def test_generate_sale_payload_with_current_only_has_empty_removed_fields(sale):
    catalogue_info = {
        "categories": {1, 2, 3},
        "collections": {45, 70, 90},
        "products": {4, 5, 6},
        "variants": {"aa", "bb", "cc"},
    }
    payload = json.loads(generate_sale_payload(sale, current_catalogue=catalogue_info))[
        0
    ]

    assert set(payload["categories_added"]) == catalogue_info["categories"]
    assert set(payload["collections_added"]) == catalogue_info["collections"]
    assert set(payload["products_added"]) == catalogue_info["products"]
    assert set(payload["variants_added"]) == catalogue_info["variants"]
    assert not payload["categories_removed"]
    assert not payload["collections_removed"]
    assert not payload["products_removed"]
    assert not payload["variants_removed"]


def test_generate_sale_payload_with_current_only_has_empty_added_fields(sale):
    catalogue_info = {
        "categories": {1, 2, 3},
        "collections": {45, 70, 90},
        "products": {4, 5, 6},
        "variants": {"aa", "bb", "cc"},
    }
    payload = json.loads(
        generate_sale_payload(sale, previous_catalogue=catalogue_info)
    )[0]

    assert set(payload["categories_removed"]) == catalogue_info["categories"]
    assert set(payload["collections_removed"]) == catalogue_info["collections"]
    assert set(payload["products_removed"]) == catalogue_info["products"]
    assert set(payload["variants_removed"]) == catalogue_info["variants"]
    assert not payload["categories_added"]
    assert not payload["collections_added"]
    assert not payload["products_added"]
    assert not payload["variants_added"]


def test_genereate_sale_payload_calculates_set_differences(sale):
    previous_info = {
        "categories": {1, 2, 3},
        "collections": {45, 70, 90},
        "products": {4, 5, 6},
        "variants": {"aaa", "bbb", "ccc"},
    }
    current_info = {
        "categories": {4, 2, 3},
        "collections": set(),
        "products": {4, 5, 6, 10, 20},
        "variants": {"aaa", "bbb", "ddd"},
    }

    payload = json.loads(
        generate_sale_payload(
            sale, previous_catalogue=previous_info, current_catalogue=current_info
        )
    )[0]

    assert set(payload["categories_removed"]) == {1}
    assert set(payload["categories_added"]) == {4}
    assert set(payload["collections_removed"]) == {45, 70, 90}
    assert not payload["collections_added"]
    assert not payload["products_removed"]
    assert set(payload["products_added"]) == {10, 20}
    assert set(payload["variants_added"]) == {"ddd"}
    assert set(payload["variants_removed"]) == {"ccc"}


def test_generate_requestor_returns_dict_with_user_id_and_user_type(staff_user, rf):
    request = rf.request()
    request.user = staff_user
    request.app = None
    requestor = get_user_or_app_from_context(request)

    assert generate_requestor(requestor) == {
        "id": graphene.Node.to_global_id("User", staff_user.id),
        "type": "user",
    }


def test_generate_requestor_returns_dict_with_app_id_and_app_type(app, rf):
    request = rf.request()
    request.user = None
    request.app = app
    requestor = get_user_or_app_from_context(request)

    assert generate_requestor(requestor) == {"id": app.name, "type": "app"}


@freeze_time("1914-06-28 10:50")
def test_generate_meta(app, rf):
    request = rf.request()
    request.app = app
    request.user = None
    requestor = get_user_or_app_from_context(request)

    timestamp = timezone.make_aware(
        datetime.strptime("1914-06-28 10:50", "%Y-%m-%d %H:%M"), timezone.utc
    ).isoformat()

    assert generate_meta(requestor_data=generate_requestor(requestor)) == {
        "issuing_principal": {"id": "Sample app objects", "type": "app"},
        "issued_at": timestamp,
        "version": __version__,
    }

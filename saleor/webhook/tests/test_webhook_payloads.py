import json
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import chain
from unittest import mock
from unittest.mock import ANY

import graphene
import pytest
import pytz
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from freezegun import freeze_time
from measurement.measures import Weight
from prices import Money

from ... import __version__
from ...core.prices import quantize_price
from ...core.utils.json_serializer import CustomJsonEncoder
from ...discount import DiscountValueType, OrderDiscountType
from ...graphql.utils import get_user_or_app_from_context
from ...order import OrderOrigin
from ...order.actions import fulfill_order_lines
from ...order.fetch import OrderLineInfo
from ...order.models import Order
from ...payment import TransactionAction
from ...payment.interface import TransactionActionData, TransactionData
from ...payment.models import TransactionItem
from ...plugins.manager import get_plugins_manager
from ...plugins.webhook.utils import from_payment_app_id
from ...product.models import ProductVariant
from ...shipping.interface import ShippingMethodData
from ...warehouse import WarehouseClickAndCollectOption
from ..payloads import (
    PRODUCT_VARIANT_FIELDS,
    _generate_collection_point_payload,
    generate_checkout_payload,
    generate_collection_payload,
    generate_customer_payload,
    generate_excluded_shipping_methods_for_checkout_payload,
    generate_excluded_shipping_methods_for_order_payload,
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
    generate_transaction_action_request_payload,
    generate_translation_payload,
)
from ..serializers import serialize_checkout_lines


def parse_django_datetime(date):
    return json.loads(json.dumps(date, cls=DjangoJSONEncoder))


@freeze_time()
@mock.patch("saleor.webhook.payloads.generate_order_lines_payload")
@mock.patch("saleor.webhook.payloads.generate_fulfillment_lines_payload")
def test_generate_order_payload(
    mocked_fulfillment_lines,
    mocked_order_lines,
    fulfilled_order,
    payment_txn_captured,
    customer_user,
):
    # given
    fulfillment_lines = '"fulfillment_lines"'
    mocked_fulfillment_lines.return_value = fulfillment_lines
    order_lines = '"order_lines"'
    mocked_order_lines.return_value = order_lines

    order = fulfilled_order
    payment = payment_txn_captured

    payment.psp_reference = "123"
    payment.save(update_fields=["psp_reference"])

    new_order = Order.objects.create(
        channel=order.channel,
        billing_address=order.billing_address,
    )
    order.origin = OrderOrigin.REISSUE
    order.original = new_order
    order.save(update_fields=["origin", "original"])

    discount_1 = order.discounts.create(
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("20"),
        amount_value=Decimal("33.0"),
        reason="Discount from staff",
    )
    discount_2 = order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("10"),
        amount_value=Decimal("16.5"),
        name="Voucher",
    )

    discount_2.created_at = datetime.now(pytz.utc) + timedelta(days=1)
    discount_2.save(update_fields=["created_at"])

    line_without_sku = order.lines.last()
    line_without_sku.product_sku = None
    line_without_sku.save()

    assert order.fulfillments.count() == 1

    fulfillment = order.fulfillments.first()
    shipping_method_channel_listing = order.shipping_method.channel_listings.filter(
        channel=order.channel,
    ).first()

    # when
    payload = json.loads(generate_order_payload(order, customer_user))[0]

    # then
    currency = order.currency
    assert payload == {
        "id": graphene.Node.to_global_id("Order", order.id),
        "type": "Order",
        "token": str(order.id),
        "created": parse_django_datetime(order.created_at),
        "status": order.status,
        "origin": order.origin,
        "user_email": order.user_email,
        "shipping_method_name": order.shipping_method_name,
        "collection_point_name": None,
        "weight": f"{order.weight.value}:{order.weight.unit}",
        "language_code": order.language_code,
        "metadata": order.metadata,
        "private_metadata": order.private_metadata,
        "channel": {
            "id": graphene.Node.to_global_id("Channel", order.channel_id),
            "type": "Channel",
            "slug": order.channel.slug,
            "currency_code": order.channel.currency_code,
        },
        "shipping_method": {
            "id": graphene.Node.to_global_id(
                "ShippingMethod", order.shipping_method_id
            ),
            "name": order.shipping_method.name,
            "type": order.shipping_method.type,
            "currency": shipping_method_channel_listing.currency,
            "price_amount": str(
                quantize_price(
                    shipping_method_channel_listing.price_amount,
                    shipping_method_channel_listing.currency,
                )
            ),
        },
        "payments": [
            {
                "id": graphene.Node.to_global_id("Payment", payment.pk),
                "type": "Payment",
                "gateway": payment.gateway,
                "payment_method_type": payment.payment_method_type,
                "partial": False,
                "cc_brand": payment.cc_brand,
                "is_active": payment.is_active,
                "created": parse_django_datetime(payment.created_at),
                "modified": parse_django_datetime(payment.modified_at),
                "charge_status": payment.charge_status,
                "psp_reference": payment.psp_reference,
                "total": str(quantize_price(payment.total, currency)),
                "captured_amount": str(
                    quantize_price(payment.captured_amount, currency)
                ),
                "currency": payment.currency,
                "billing_email": payment.billing_email,
                "billing_first_name": payment.billing_first_name,
                "billing_last_name": payment.billing_last_name,
                "billing_company_name": payment.billing_company_name,
                "billing_address_1": payment.billing_address_1,
                "billing_address_2": payment.billing_address_2,
                "billing_city": payment.billing_city,
                "billing_city_area": payment.billing_city_area,
                "billing_postal_code": payment.billing_postal_code,
                "billing_country_code": payment.billing_country_code,
                "billing_country_area": payment.billing_country_area,
            }
        ],
        "shipping_address": {
            "id": graphene.Node.to_global_id("Address", order.shipping_address_id),
            "type": "Address",
            "first_name": order.shipping_address.first_name,
            "last_name": order.shipping_address.last_name,
            "company_name": order.shipping_address.company_name,
            "street_address_1": order.shipping_address.street_address_1,
            "street_address_2": order.shipping_address.street_address_2,
            "city": order.shipping_address.city,
            "city_area": order.shipping_address.city_area,
            "postal_code": order.shipping_address.postal_code,
            "country": order.shipping_address.country.code,
            "country_area": order.shipping_address.country_area,
            "phone": str(order.shipping_address.phone),
        },
        "billing_address": {
            "id": graphene.Node.to_global_id("Address", order.billing_address_id),
            "type": "Address",
            "first_name": order.billing_address.first_name,
            "last_name": order.billing_address.last_name,
            "company_name": order.billing_address.company_name,
            "street_address_1": order.billing_address.street_address_1,
            "street_address_2": order.billing_address.street_address_2,
            "city": order.billing_address.city,
            "city_area": order.billing_address.city_area,
            "postal_code": order.billing_address.postal_code,
            "country": order.billing_address.country.code,
            "country_area": order.billing_address.country_area,
            "phone": str(order.billing_address.phone),
        },
        "discounts": [
            {
                "id": graphene.Node.to_global_id("OrderDiscount", discount_1.pk),
                "type": discount_1.type,
                "value_type": discount_1.value_type,
                "value": "20.000",
                "amount_value": str(quantize_price(discount_1.amount_value, currency)),
                "name": discount_1.name,
                "translated_name": discount_1.translated_name,
                "reason": discount_1.reason,
            },
            {
                "id": graphene.Node.to_global_id("OrderDiscount", discount_2.pk),
                "type": discount_2.type,
                "value_type": discount_2.value_type,
                "value": "10.000",
                "amount_value": str(quantize_price(discount_2.amount_value, currency)),
                "name": discount_2.name,
                "translated_name": discount_2.translated_name,
                "reason": discount_2.reason,
            },
        ],
        "original": graphene.Node.to_global_id("Order", order.original_id),
        "lines": json.loads(order_lines),
        "fulfillments": [
            {
                "id": graphene.Node.to_global_id("Fulfillment", fulfillment.pk),
                "type": "Fulfillment",
                "status": fulfillment.status,
                "tracking_number": fulfillment.tracking_number,
                "created": parse_django_datetime(fulfillment.created_at),
                "shipping_refund_amount": "0.00",
                "total_refund_amount": "0.00",
                "lines": json.loads(fulfillment_lines),
            }
        ],
        "collection_point": None,
        "shipping_tax_rate": str(order.shipping_tax_rate),
        "shipping_price_net_amount": str(
            quantize_price(order.shipping_price.net.amount, currency)
        ),
        "shipping_price_gross_amount": str(
            quantize_price(order.shipping_price.gross.amount, currency)
        ),
        "total_net_amount": str(quantize_price(order.total.net.amount, currency)),
        "total_gross_amount": str(quantize_price(order.total.gross.amount, currency)),
        "undiscounted_total_net_amount": str(
            quantize_price(order.undiscounted_total.net.amount, currency)
        ),
        "undiscounted_total_gross_amount": str(
            quantize_price(order.undiscounted_total.gross.amount, currency)
        ),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }

    mocked_fulfillment_lines.assert_called_with(fulfillment)


@freeze_time()
@mock.patch("saleor.webhook.payloads.generate_order_lines_payload")
@mock.patch("saleor.webhook.payloads.generate_fulfillment_lines_payload")
def test_generate_order_payload_no_user_email_but_user_set(
    mocked_fulfillment_lines,
    mocked_order_lines,
    fulfilled_order,
    customer_user,
):
    """Ensure that the assigned user's email is returned in `user_email` payload field
    when the user_email order value is empty."""
    # given
    fulfillment_lines = '"fulfillment_lines"'
    mocked_fulfillment_lines.return_value = fulfillment_lines
    order_lines = '"order_lines"'
    mocked_order_lines.return_value = order_lines

    order = fulfilled_order

    order.user_email = ""
    order.save(update_fields=["user_email"])

    line_without_sku = order.lines.last()
    line_without_sku.product_sku = None
    line_without_sku.save()

    assert order.fulfillments.count() == 1

    # when
    payload = json.loads(generate_order_payload(order, customer_user))[0]

    # then
    assert payload["user_email"] == order.user.email


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
            "token": str(invoice.order.id),
            "id": graphene.Node.to_global_id("Order", invoice.order.id),
            "language_code": "en",
            "private_metadata": invoice.order.private_metadata,
            "metadata": invoice.order.metadata,
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
    assert data["checkout"]["channel"]["id"] == graphene.Node.to_global_id(
        "Channel", checkout.channel.pk
    )
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


@freeze_time("1914-06-28 10:50")
def test_generate_payment_with_transactions_payload(dummy_webhook_app_payment_data):
    transaction_data = {
        "token": "token",
        "is_success": True,
        "kind": "auth",
        "gateway_response": {"status": "SUCCESS"},
        "amount": {
            "amount": str(
                quantize_price(
                    dummy_webhook_app_payment_data.amount,
                    dummy_webhook_app_payment_data.currency,
                )
            ),
            "currency": dummy_webhook_app_payment_data.currency,
        },
    }

    dummy_webhook_app_payment_data.transactions = [TransactionData(**transaction_data)]

    payload = generate_payment_payload(dummy_webhook_app_payment_data)
    expected_payload = asdict(dummy_webhook_app_payment_data)

    expected_payload["amount"] = Decimal(expected_payload["amount"]).quantize(
        Decimal("0.01")
    )
    expected_payload["payment_method"] = from_payment_app_id(
        dummy_webhook_app_payment_data.gateway
    ).name

    expected_payload["meta"] = generate_meta(requestor_data=generate_requestor())

    assert expected_payload["transactions"]
    assert payload == json.dumps(expected_payload, cls=CustomJsonEncoder)


def test_generate_checkout_lines_payload(checkout_with_single_item):
    payload = json.loads(generate_checkout_payload(checkout_with_single_item))[0]
    assert payload.get("lines")

    variant = checkout_with_single_item.lines.first().variant
    line = payload["lines"][0]
    assert line["sku"] == variant.sku
    assert line["variant_id"] == variant.get_global_id()


def test_generate_checkout_lines_payload_custom_price(checkout_with_single_item):
    line = checkout_with_single_item.lines.first()
    price_override = Decimal("11.11")
    line.price_override = price_override
    line.save(update_fields=["price_override"])

    payload = json.loads(generate_checkout_payload(checkout_with_single_item))[0]
    assert payload.get("lines")

    variant = line.variant

    line_data = payload["lines"][0]
    assert line_data["sku"] == variant.sku
    assert line_data["variant_id"] == variant.get_global_id()
    assert line_data["base_price"] == str(price_override)


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
        "language_code": customer.language_code,
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


def test_generate_sale_payload_calculates_set_differences(sale):
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


@freeze_time()
def test_generate_checkout_payload(
    checkout_with_items,
    customer_user,
    address,
    address_other_country,
    shipping_method,
    warehouse,
):
    checkout = checkout_with_items

    checkout.user = customer_user
    checkout.billing_address = address
    checkout.shipping_address = address_other_country
    checkout.shipping_method = shipping_method
    checkout.collection_point = warehouse

    # when
    payload = json.loads(generate_checkout_payload(checkout, customer_user))[0]

    shipping_method_channel_listing = checkout.shipping_method.channel_listings.filter(
        channel=checkout.channel,
    ).first()

    # then
    assert payload == {
        "type": "Checkout",
        "token": graphene.Node.to_global_id("Checkout", checkout.pk),
        "created": parse_django_datetime(checkout.created_at),
        "last_change": parse_django_datetime(checkout.last_change),
        "email": checkout.email,
        "currency": checkout.currency,
        "discount_amount": str(
            quantize_price(checkout.discount_amount, checkout.currency)
        ),
        "discount_name": checkout.discount_name,
        "language_code": checkout.language_code,
        "private_metadata": checkout.private_metadata,
        "metadata": checkout.metadata,
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "user": {
            "type": "User",
            "id": graphene.Node.to_global_id("User", checkout.user.pk),
            "email": checkout.user.email,
            "first_name": checkout.user.first_name,
            "last_name": checkout.user.last_name,
        },
        "billing_address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", checkout.billing_address.pk),
            "first_name": checkout.billing_address.first_name,
            "last_name": checkout.billing_address.last_name,
            "company_name": checkout.billing_address.company_name,
            "street_address_1": checkout.billing_address.street_address_1,
            "street_address_2": checkout.billing_address.street_address_2,
            "city": checkout.billing_address.city,
            "city_area": checkout.billing_address.city_area,
            "postal_code": checkout.billing_address.postal_code,
            "country": checkout.billing_address.country.code,
            "country_area": checkout.billing_address.country_area,
            "phone": str(checkout.billing_address.phone),
        },
        "shipping_address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", checkout.shipping_address.pk),
            "first_name": checkout.shipping_address.first_name,
            "last_name": checkout.shipping_address.last_name,
            "company_name": checkout.shipping_address.company_name,
            "street_address_1": checkout.shipping_address.street_address_1,
            "street_address_2": checkout.shipping_address.street_address_2,
            "city": checkout.shipping_address.city,
            "city_area": checkout.shipping_address.city_area,
            "postal_code": checkout.shipping_address.postal_code,
            "country": checkout.shipping_address.country.code,
            "country_area": checkout.shipping_address.country_area,
            "phone": str(checkout.shipping_address.phone),
        },
        "shipping_method": {
            "id": graphene.Node.to_global_id(
                "ShippingMethod", checkout.shipping_method.pk
            ),
            "name": checkout.shipping_method.name,
            "type": checkout.shipping_method.type,
            "currency": shipping_method_channel_listing.currency,
            "price_amount": str(
                quantize_price(
                    shipping_method_channel_listing.price_amount,
                    shipping_method_channel_listing.currency,
                )
            ),
        },
        "lines": serialize_checkout_lines(checkout),
        "collection_point": json.loads(
            _generate_collection_point_payload(checkout.collection_point)
        )[0],
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
        "warehouse_address": ANY,
    }


def test_generate_excluded_shipping_methods_for_order(order):
    shipping_method = ShippingMethodData(
        id="123",
        price=Money(Decimal("10.59"), "USD"),
        name="shipping",
        maximum_order_weight=Weight(kg=10),
        minimum_order_weight=Weight(g=1),
        maximum_delivery_days=10,
        minimum_delivery_days=2,
    )
    response = json.loads(
        generate_excluded_shipping_methods_for_order_payload(order, [shipping_method])
    )

    assert "order" in response
    assert response["shipping_methods"] == [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", "123"),
            "price": "10.59",
            "currency": "USD",
            "name": "shipping",
            "maximum_order_weight": "10.0:kg",
            "minimum_order_weight": "1.0:g",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
        }
    ]


def test_generate_excluded_shipping_methods_for_checkout(checkout):
    shipping_method = ShippingMethodData(
        id="123",
        price=Money(Decimal("10.59"), "USD"),
        name="shipping",
        maximum_order_weight=Weight(kg=10),
        minimum_order_weight=Weight(g=1),
        maximum_delivery_days=10,
        minimum_delivery_days=2,
    )
    response = json.loads(
        generate_excluded_shipping_methods_for_checkout_payload(
            checkout, [shipping_method]
        )
    )

    assert "checkout" in response
    assert response["shipping_methods"] == [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", "123"),
            "price": "10.59",
            "currency": "USD",
            "name": "shipping",
            "maximum_order_weight": "10.0:kg",
            "minimum_order_weight": "1.0:g",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
        }
    ]


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


@pytest.mark.parametrize(
    "action_type, action_value",
    [
        (TransactionAction.CHARGE, Decimal("5.000")),
        (TransactionAction.REFUND, Decimal("9.000")),
        (TransactionAction.VOID, None),
    ],
)
@freeze_time("1914-06-28 10:50")
def test_generate_transaction_action_request_payload_for_order(
    action_type, action_value, order, app, rf
):
    # given
    request = rf.request()
    request.app = app
    request.user = None
    requestor = get_user_or_app_from_context(request)

    transaction = TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )

    # when
    payload = json.loads(
        generate_transaction_action_request_payload(
            transaction_data=TransactionActionData(
                transaction=transaction,
                action_type=action_type,
                action_value=action_value,
            ),
            requestor=requestor,
        )
    )

    # then
    currency = transaction.currency
    action_value = str(quantize_price(action_value, currency)) if action_value else None
    assert payload == {
        "action": {
            "type": action_type,
            "value": action_value,
            "currency": currency,
        },
        "transaction": {
            "status": transaction.status,
            "type": transaction.type,
            "reference": transaction.reference,
            "available_actions": transaction.available_actions,
            "currency": currency,
            "charged_value": str(quantize_price(transaction.charged_value, currency)),
            "authorized_value": str(
                quantize_price(transaction.authorized_value, currency)
            ),
            "refunded_value": str(quantize_price(transaction.refunded_value, currency)),
            "voided_value": str(quantize_price(transaction.voided_value, currency)),
            "order_id": graphene.Node.to_global_id("Order", order.pk),
            "checkout_id": None,
            "created_at": parse_django_datetime(transaction.created_at),
            "modified_at": parse_django_datetime(transaction.modified_at),
        },
        "meta": {
            "issuing_principal": {"id": "Sample app objects", "type": "app"},
            "issued_at": timezone.make_aware(
                datetime.strptime("1914-06-28 10:50", "%Y-%m-%d %H:%M"), timezone.utc
            ).isoformat(),
            "version": __version__,
        },
    }


@pytest.mark.parametrize(
    "action_type, action_value",
    [
        (TransactionAction.CHARGE, Decimal("5.000")),
        (TransactionAction.REFUND, Decimal("9.000")),
        (TransactionAction.VOID, None),
    ],
)
@freeze_time("1914-06-28 10:50")
def test_generate_transaction_action_request_payload_for_checkout(
    action_type, action_value, checkout, app, rf
):
    # given
    request = rf.request()
    request.app = app
    request.user = None
    requestor = get_user_or_app_from_context(request)

    transaction = TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=Decimal("10"),
    )

    # when
    payload = json.loads(
        generate_transaction_action_request_payload(
            transaction_data=TransactionActionData(
                transaction=transaction,
                action_type=action_type,
                action_value=action_value,
            ),
            requestor=requestor,
        )
    )

    # then
    currency = transaction.currency
    action_value = str(quantize_price(action_value, currency)) if action_value else None
    assert payload == {
        "action": {
            "type": action_type,
            "value": action_value,
            "currency": currency,
        },
        "transaction": {
            "status": transaction.status,
            "type": transaction.type,
            "reference": transaction.reference,
            "available_actions": transaction.available_actions,
            "currency": currency,
            "charged_value": str(quantize_price(transaction.charged_value, currency)),
            "authorized_value": str(
                quantize_price(transaction.authorized_value, currency)
            ),
            "refunded_value": str(quantize_price(transaction.refunded_value, currency)),
            "voided_value": str(quantize_price(transaction.voided_value, currency)),
            "order_id": None,
            "checkout_id": graphene.Node.to_global_id("Checkout", checkout.pk),
            "created_at": parse_django_datetime(transaction.created_at),
            "modified_at": parse_django_datetime(transaction.modified_at),
        },
        "meta": {
            "issuing_principal": {"id": "Sample app objects", "type": "app"},
            "issued_at": timezone.make_aware(
                datetime.strptime("1914-06-28 10:50", "%Y-%m-%d %H:%M"), timezone.utc
            ).isoformat(),
            "version": __version__,
        },
    }

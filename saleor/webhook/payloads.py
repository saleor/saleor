import json
from typing import Optional

from django.db.models import QuerySet

from ..account.models import User
from ..checkout.models import Checkout
from ..core.utils.anonymization import (
    anonymize_checkout,
    anonymize_order,
    generate_fake_user,
)
from ..order import FulfillmentStatus, OrderStatus
from ..order.models import Fulfillment, FulfillmentLine, Order
from ..order.utils import get_order_country
from ..payment import ChargeStatus
from ..product.models import Product
from ..warehouse.models import Warehouse
from .event_types import WebhookEventType
from .payload_serializers import PayloadSerializer
from .serializers import serialize_checkout_lines

ADDRESS_FIELDS = (
    "first_name",
    "last_name",
    "company_name",
    "street_address_1",
    "street_address_2",
    "city",
    "city_area",
    "postal_code",
    "country",
    "country_area",
    "phone",
)


def generate_order_payload(order: "Order"):
    serializer = PayloadSerializer()
    fulfillment_fields = ("status", "tracking_number", "created")
    payment_fields = (
        "gateway"
        "is_active"
        "created"
        "modified"
        "charge_status"
        "total"
        "captured_amount"
        "currency"
        "billing_email"
        "billing_first_name"
        "billing_last_name"
        "billing_company_name"
        "billing_address_1"
        "billing_address_2"
        "billing_city"
        "billing_city_area"
        "billing_postal_code"
        "billing_country_code"
        "billing_country_area"
    )
    line_fields = (
        "product_name",
        "variant_name",
        "translated_product_name",
        "translated_variant_name",
        "product_sku",
        "quantity",
        "currency",
        "unit_price_net_amount",
        "unit_price_gross_amount",
        "tax_rate",
    )
    shipping_method_fields = ("name", "type", "currency", "price_amount")
    order_fields = (
        "created",
        "status",
        "user_email",
        "shipping_method_name",
        "shipping_price_net_amount",
        "shipping_price_gross_amount",
        "total_net_amount",
        "total_gross_amount",
        "shipping_price_net_amount",
        "shipping_price_gross_amount",
        "discount_amount",
        "discount_name",
        "translated_discount_name",
        "weight",
        "private_metadata",
        "metadata",
    )
    order_data = serializer.serialize(
        [order],
        fields=order_fields,
        additional_fields={
            "shipping_method": (lambda o: o.shipping_method, shipping_method_fields),
            "lines": (lambda o: o.lines.all(), line_fields),
            "payments": (lambda o: o.payments.all(), payment_fields),
            "shipping_address": (lambda o: o.shipping_address, ADDRESS_FIELDS),
            "billing_address": (lambda o: o.billing_address, ADDRESS_FIELDS),
            "fulfillments": (lambda o: o.fulfillments.all(), fulfillment_fields),
        },
    )
    return order_data


def generate_checkout_payload(checkout: "Checkout"):
    serializer = PayloadSerializer()
    checkout_fields = (
        "created",
        "last_change",
        "status",
        "email",
        "quantity",
        "currency",
        "discount_amount",
        "discount_name",
        "private_metadata",
        "metadata",
    )
    user_fields = ("email", "first_name", "last_name")
    shipping_method_fields = ("name", "type", "currency", "price_amount")
    lines_dict_data = serialize_checkout_lines(checkout)

    checkout_data = serializer.serialize(
        [checkout],
        fields=checkout_fields,
        obj_id_name="token",
        additional_fields={
            "user": (lambda c: c.user, user_fields),
            "billing_address": (lambda c: c.billing_address, ADDRESS_FIELDS),
            "shipping_address": (lambda c: c.shipping_address, ADDRESS_FIELDS),
            "shipping_method": (lambda c: c.shipping_method, shipping_method_fields),
        },
        extra_dict_data={
            # Casting to list to make it json-serializable
            "lines": list(lines_dict_data)
        },
    )
    return checkout_data


def generate_customer_payload(customer: "User"):
    serializer = PayloadSerializer()
    data = serializer.serialize(
        [customer],
        fields=[
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "private_metadata",
            "metadata",
        ],
        additional_fields={
            "default_shipping_address": (
                lambda c: c.default_billing_address,
                ADDRESS_FIELDS,
            ),
            "default_billing_address": (
                lambda c: c.default_shipping_address,
                ADDRESS_FIELDS,
            ),
        },
    )
    return data


def generate_product_payload(product: "Product"):
    serializer = PayloadSerializer()

    product_fields = (
        "name",
        "description_json",
        "currency",
        "price_amount",
        "minimal_variant_price_amount",
        "attributes",
        "updated_at",
        "charge_taxes",
        "weight",
        "publication_date",
        "is_published",
        "private_metadata",
        "metadata",
    )
    product_variant_fields = (
        "sku",
        "name",
        "currency",
        "price_override_amount",
        "track_inventory",
        "quantity",
        "quantity_allocated",
        "cost_price_amount",
        "private_metadata",
        "metadata",
    )
    product_payload = serializer.serialize(
        [product],
        fields=product_fields,
        additional_fields={
            "category": (lambda p: p.category, ("name", "slug")),
            "collections": (lambda p: p.collections.all(), ("name", "slug")),
            "variants": (lambda p: p.variants.all(), product_variant_fields),
        },
    )
    return product_payload


def generate_fulfillment_lines_payload(fulfillment: Fulfillment):
    serializer = PayloadSerializer()
    lines = FulfillmentLine.objects.prefetch_related(
        "order_line__variant__product__product_type"
    ).filter(fulfillment=fulfillment)
    line_fields = ("quantity",)
    return serializer.serialize(
        lines,
        fields=line_fields,
        extra_dict_data={
            "weight": (lambda fl: fl.order_line.variant.get_weight().g),
            "weight_unit": "gram",
            "product_type": (
                lambda fl: fl.order_line.variant.product.product_type.name
            ),
            "unit_price_gross": lambda fl: fl.order_line.unit_price_gross_amount,
            "currency": (lambda fl: fl.order_line.currency),
        },
    )


def generate_fulfillment_payload(fulfillment: Fulfillment):
    serializer = PayloadSerializer()

    # fulfillment fields to serialize
    fulfillment_fields = ("status", "tracking_code", "order__user_email")
    order_country = get_order_country(fulfillment.order)
    fulfillment_line = fulfillment.lines.first()
    if fulfillment_line and fulfillment_line.stock:
        warehouse = fulfillment_line.stock.warehouse
    else:
        warehouse = Warehouse.objects.for_country(order_country).first()
    fulfillment_data = serializer.serialize(
        [fulfillment],
        fields=fulfillment_fields,
        additional_fields={
            "warehouse_address": (lambda f: warehouse.address, ADDRESS_FIELDS),
        },
        extra_dict_data={
            "order": json.loads(generate_order_payload(fulfillment.order))[0],
            "lines": json.loads(generate_fulfillment_lines_payload(fulfillment)),
        },
    )
    return fulfillment_data


def _get_sample_object(qs: QuerySet):
    """Return random object from query."""
    random_object = qs.order_by("?").first()
    return random_object


def _generate_sample_order_payload(event_name):
    order_qs = Order.objects.prefetch_related(
        "payments",
        "lines",
        "shipping_method",
        "shipping_address",
        "billing_address",
        "fulfillments",
    )
    order = None
    if event_name == WebhookEventType.ORDER_CREATED:
        order = _get_sample_object(order_qs.filter(status=OrderStatus.UNFULFILLED))
    elif event_name == WebhookEventType.ORDER_FULLY_PAID:
        order = _get_sample_object(
            order_qs.filter(payments__charge_status=ChargeStatus.FULLY_CHARGED)
        )
    elif event_name == WebhookEventType.ORDER_FULFILLED:
        order = _get_sample_object(
            order_qs.filter(fulfillments__status=FulfillmentStatus.FULFILLED)
        )
    elif event_name in [
        WebhookEventType.ORDER_CANCELLED,
        WebhookEventType.ORDER_UPDATED,
    ]:
        order = _get_sample_object(order_qs.filter(status=OrderStatus.CANCELED))
    if order:
        anonymized_order = anonymize_order(order)
        return generate_order_payload(anonymized_order)


def generate_sample_payload(event_name: str) -> Optional[dict]:
    if event_name == WebhookEventType.CUSTOMER_CREATED:
        user = generate_fake_user()
        payload = generate_customer_payload(user)
    elif event_name == WebhookEventType.PRODUCT_CREATED:
        product = _get_sample_object(
            Product.objects.prefetch_related("category", "collections", "variants")
        )
        payload = generate_product_payload(product) if product else None
    elif event_name == WebhookEventType.CHECKOUT_QUANTITY_CHANGED:
        checkout = _get_sample_object(
            Checkout.objects.prefetch_related("lines__variant__product")
        )
        if checkout:
            anonymized_checkout = anonymize_checkout(checkout)
            payload = generate_checkout_payload(anonymized_checkout)
    elif event_name == WebhookEventType.FULFILLMENT_CREATED:
        fulfillment = _get_sample_object(
            Fulfillment.objects.prefetch_related("lines__order_line__variant")
        )
        fulfillment.order = anonymize_order(fulfillment.order)
        payload = generate_fulfillment_payload(fulfillment)
    else:
        payload = _generate_sample_order_payload(event_name)
    return json.loads(payload) if payload else None

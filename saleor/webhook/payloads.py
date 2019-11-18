import json
from typing import Optional

from django.db.models import Model, QuerySet

from ..account.models import User
from ..order import FulfillmentStatus, OrderStatus
from ..order.models import Order
from ..payment import ChargeStatus
from ..product.models import Product
from . import WebhookEventType
from .payload_serializers import PayloadSerializer

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
        "private_meta",
        "meta",
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
            "private_meta",
            "meta",
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
        "private_meta",
        "meta",
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
        "private_meta",
        "meta",
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


def _get_sample_object(qs: QuerySet) -> Optional[Model]:
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
    return generate_order_payload(order) if order else None


def generate_sample_payload(event_name: str) -> Optional[dict]:
    if event_name == WebhookEventType.CUSTOMER_CREATED:
        user = _get_sample_object(User.objects.filter(is_staff=False, is_active=True))
        payload = generate_customer_payload(user) if user else None
    elif event_name == WebhookEventType.PRODUCT_CREATED:
        product = _get_sample_object(
            Product.objects.prefetch_related("category", "collections", "variants")
        )
        payload = generate_product_payload(product) if product else None
    else:
        payload = _generate_sample_order_payload(event_name)
    return json.loads(payload) if payload else None

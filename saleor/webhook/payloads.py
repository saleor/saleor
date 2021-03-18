import json
from typing import TYPE_CHECKING, Iterable, Optional

import graphene
from django.db.models import QuerySet

from ..account.models import User
from ..checkout.models import Checkout
from ..core.utils import build_absolute_uri
from ..core.utils.anonymization import (
    anonymize_checkout,
    anonymize_order,
    generate_fake_user,
)
from ..invoice.models import Invoice
from ..order import FulfillmentStatus, OrderStatus
from ..order.models import Fulfillment, FulfillmentLine, Order, OrderLine
from ..order.utils import get_order_country
from ..page.models import Page
from ..payment import ChargeStatus
from ..product import ProductMediaTypes
from ..product.models import Product
from ..warehouse.models import Warehouse
from .event_types import WebhookEventType
from .payload_serializers import PayloadSerializer
from .serializers import (
    serialize_checkout_lines,
    serialize_product_or_variant_attributes,
)

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from ..product.models import ProductVariant


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

ORDER_FIELDS = (
    "created",
    "status",
    "user_email",
    "shipping_method_name",
    "shipping_price_net_amount",
    "shipping_price_gross_amount",
    "shipping_tax_rate",
    "total_net_amount",
    "total_gross_amount",
    "shipping_price_net_amount",
    "shipping_price_gross_amount",
    "weight",
    "private_metadata",
    "metadata",
)


def generate_order_lines_payload(lines: Iterable[OrderLine]):
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
        "unit_discount_amount",
        "unit_discount_type",
        "unit_discount_reason",
        "total_price_net_amount",
        "total_price_gross_amount",
        "tax_rate",
    )
    serializer = PayloadSerializer()
    return serializer.serialize(
        lines,
        fields=line_fields,
        extra_dict_data={
            "total_price_net_amount": (lambda l: l.total_price.net.amount),
            "total_price_gross_amount": (lambda l: l.total_price.gross.amount),
        },
    )


def generate_order_payload(order: "Order"):
    serializer = PayloadSerializer()
    fulfillment_fields = ("status", "tracking_number", "created")
    payment_fields = (
        "gateway",
        "payment_method_type",
        "cc_brand",
        "is_active",
        "created",
        "modified",
        "charge_status",
        "total",
        "captured_amount",
        "currency",
        "billing_email",
        "billing_first_name",
        "billing_last_name",
        "billing_company_name",
        "billing_address_1",
        "billing_address_2",
        "billing_city",
        "billing_city_area",
        "billing_postal_code",
        "billing_country_code",
        "billing_country_area",
    )

    discount_fields = (
        "type",
        "value_type",
        "value",
        "amount_value",
        "name",
        "translated_name",
        "reason",
    )
    shipping_method_fields = ("name", "type", "currency", "price_amount")
    lines = order.lines.all()
    order_data = serializer.serialize(
        [order],
        fields=ORDER_FIELDS,
        additional_fields={
            "shipping_method": (lambda o: o.shipping_method, shipping_method_fields),
            "payments": (lambda o: o.payments.all(), payment_fields),
            "shipping_address": (lambda o: o.shipping_address, ADDRESS_FIELDS),
            "billing_address": (lambda o: o.billing_address, ADDRESS_FIELDS),
            "fulfillments": (lambda o: o.fulfillments.all(), fulfillment_fields),
            "discounts": (lambda o: o.discounts.all(), discount_fields),
        },
        extra_dict_data={"lines": json.loads(generate_order_lines_payload(lines))},
    )
    return order_data


def generate_invoice_payload(invoice: "Invoice"):
    serializer = PayloadSerializer()
    invoice_fields = ("id", "number", "external_url", "created")
    return serializer.serialize(
        [invoice],
        fields=invoice_fields,
        additional_fields={"order": (lambda i: i.order, ORDER_FIELDS)},
    )


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
            "addresses": (
                lambda c: c.addresses.all(),
                ADDRESS_FIELDS,
            ),
        },
    )
    return data


PRODUCT_FIELDS = (
    "name",
    "description",
    "currency",
    "updated_at",
    "charge_taxes",
    "weight",
    "publication_date",
    "is_published",
    "private_metadata",
    "metadata",
)


def generate_product_payload(product: "Product"):
    serializer = PayloadSerializer(
        extra_model_fields={"ProductVariant": ("quantity", "quantity_allocated")}
    )
    product_variant_fields = (
        "sku",
        "name",
        "currency",
        "price_amount",
        "track_inventory",
        "cost_price_amount",
        "private_metadata",
        "metadata",
    )
    product_payload = serializer.serialize(
        [product],
        fields=PRODUCT_FIELDS,
        additional_fields={
            "category": (lambda p: p.category, ("name", "slug")),
            "collections": (lambda p: p.collections.all(), ("name", "slug")),
            "variants": (
                lambda p: p.variants.annotate_quantities().all(),
                product_variant_fields,
            ),
        },
        extra_dict_data={
            "attributes": serialize_product_or_variant_attributes(product)
        },
    )
    return product_payload


def generate_product_deleted_payload(product: "Product", variants_id):
    serializer = PayloadSerializer()
    product_fields = PRODUCT_FIELDS
    variant_global_ids = [
        graphene.Node.to_global_id("ProductVariant", pk) for pk in variants_id
    ]
    product_payload = serializer.serialize(
        [product],
        fields=product_fields,
        extra_dict_data={"variants": list(variant_global_ids)},
    )
    return product_payload


PRODUCT_VARIANT_FIELDS = (
    "name",
    "sku",
    "private_metadata",
    "metadata",
)


def generate_product_variant_payload(product_variant: "ProductVariant"):
    serializer = PayloadSerializer()
    product_id = graphene.Node.to_global_id("Product", product_variant.product.id)
    payload = serializer.serialize(
        [product_variant],
        fields=PRODUCT_VARIANT_FIELDS,
        additional_fields={
            "channel_listings": (
                lambda p: p.channel_listings.all(),
                (
                    "currency",
                    "price_amount",
                    "cost_price_amount",
                ),
            ),
        },
        extra_dict_data={
            "attributes": serialize_product_or_variant_attributes(product_variant),
            "product_id": product_id,
            "media": [
                {
                    "alt": media_obj.media.alt,
                    "url": (
                        build_absolute_uri(media_obj.media.image.url)
                        if media_obj.media.type == ProductMediaTypes.IMAGE
                        else media_obj.media.external_url
                    ),
                }
                for media_obj in product_variant.variant_media.all()
            ],
        },
    )
    return payload


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


def generate_page_payload(page: Page):
    serializer = PayloadSerializer()
    page_fields = [
        "private_metadata",
        "metadata",
        "title",
        "content",
        "publication_date",
        "is_published",
        "updated_at",
    ]
    page_payload = serializer.serialize(
        [page],
        fields=page_fields,
    )
    return page_payload


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
    checkout_events = [
        WebhookEventType.CHECKOUT_UPADTED,
        WebhookEventType.CHECKOUT_CREATED,
    ]
    pages_events = [
        WebhookEventType.PAGE_CREATED,
        WebhookEventType.PAGE_DELETED,
        WebhookEventType.PAGE_UPDATED,
    ]
    user_events = [WebhookEventType.CUSTOMER_CREATED, WebhookEventType.CUSTOMER_UPDATED]

    if event_name in user_events:
        user = generate_fake_user()
        payload = generate_customer_payload(user)
    elif event_name == WebhookEventType.PRODUCT_CREATED:
        product = _get_sample_object(
            Product.objects.prefetch_related("category", "collections", "variants")
        )
        payload = generate_product_payload(product) if product else None
    elif event_name in checkout_events:
        checkout = _get_sample_object(
            Checkout.objects.prefetch_related("lines__variant__product")
        )
        if checkout:
            anonymized_checkout = anonymize_checkout(checkout)
            payload = generate_checkout_payload(anonymized_checkout)
    elif event_name in pages_events:
        page = _get_sample_object(Page.objects.all())
        if page:
            payload = generate_page_payload(page)
    elif event_name == WebhookEventType.FULFILLMENT_CREATED:
        fulfillment = _get_sample_object(
            Fulfillment.objects.prefetch_related("lines__order_line__variant")
        )
        fulfillment.order = anonymize_order(fulfillment.order)
        payload = generate_fulfillment_payload(fulfillment)
    else:
        payload = _generate_sample_order_payload(event_name)
    return json.loads(payload) if payload else None

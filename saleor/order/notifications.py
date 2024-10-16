from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlencode

from django.conf import settings
from django.forms import model_to_dict

from ..account.models import StaffNotificationRecipient
from ..attribute.models import (
    AssignedProductAttributeValue,
    Attribute,
    AttributeProduct,
    AttributeValue,
)
from ..core.notification.utils import get_site_context
from ..core.notify import NotifyEventType, NotifyHandler
from ..core.prices import quantize_price, quantize_price_fields
from ..core.utils.url import build_absolute_uri, prepare_url
from ..discount import DiscountType
from ..graphql.core.utils import to_global_id_or_none
from ..product import ProductMediaTypes
from ..product.models import DigitalContentUrl, Product, ProductMedia, ProductVariant
from ..thumbnail import THUMBNAIL_SIZES
from ..thumbnail.utils import get_image_or_proxy_url
from .models import FulfillmentLine, Order, OrderLine

if TYPE_CHECKING:
    from ..account.models import User  # noqa: F401
    from ..app.models import App


@dataclass
class AttributeData:
    attribute_map: dict[int, Attribute]
    attribute_value_map: dict[int, AttributeValue]
    product_type_id_to_attribute_id_map: dict[int, list[int]]
    assigned_product_attribute_values_map: dict[int, list[int]]


def get_attribute_data_from_order_lines(lines: Iterable["OrderLine"]) -> AttributeData:
    product_ids = {line.variant.product_id for line in lines if line.variant_id}  # type: ignore[union-attr]
    assigned_product_attribute_values = (
        AssignedProductAttributeValue.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        )
        .filter(product_id__in=product_ids)
        .values_list("product_id", "value_id")
    )
    assigned_product_attribute_values_map = defaultdict(list)
    attribute_value_ids = set()
    for product_id, value_id in assigned_product_attribute_values:
        attribute_value_ids.add(value_id)
        assigned_product_attribute_values_map[product_id].append(value_id)

    attribute_values_map = AttributeValue.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).in_bulk(attribute_value_ids)

    product_type_ids = {
        line.variant.product.product_type_id  # type: ignore[union-attr]
        for line in lines
        if line.variant_id
    }

    attribute_products = AttributeProduct.objects.filter(
        product_type_id__in=product_type_ids
    ).values_list("product_type_id", "attribute_id")
    attribute_ids = set()
    product_type_id_to_attribute_id_map = defaultdict(list)
    for product_type_id, attribute_id in attribute_products:
        attribute_ids.add(attribute_id)
        product_type_id_to_attribute_id_map[product_type_id].append(attribute_id)

    attributes_map = Attribute.objects.in_bulk(attribute_ids)

    return AttributeData(
        attribute_map=attributes_map,
        attribute_value_map=attribute_values_map,
        product_type_id_to_attribute_id_map=product_type_id_to_attribute_id_map,
        assigned_product_attribute_values_map=assigned_product_attribute_values_map,
    )


def get_image_payload(instance: ProductMedia):
    return {
        # This is temporary solution, the get_product_image_thumbnail_url
        # should be optimize - we should fetch all thumbnails at once instead of
        # fetching thumbnails by one for each size
        str(size): build_absolute_uri(
            get_image_or_proxy_url(None, str(instance.id), "ProductMedia", size, None)
        )
        for size in THUMBNAIL_SIZES
    }


def get_default_images_payload(images: list[ProductMedia]):
    first_image_payload = None
    first_image = images[0] if images else None
    if first_image:
        first_image_payload = {"original": get_image_payload(first_image)}
    images_payload = None
    if images:
        images_payload = [{"original": get_image_payload(image) for image in images}]  # noqa: B035
    return {"first_image": first_image_payload, "images": images_payload}


def get_product_attributes_payload(product, attribute_data: AttributeData):
    attribute_ids = attribute_data.product_type_id_to_attribute_id_map.get(
        product.product_type.id, []
    )
    assigned_value_ids = attribute_data.assigned_product_attribute_values_map.get(
        product.id, []
    )

    attributes = [
        attribute_data.attribute_map[attribute_id]
        for attribute_id in attribute_ids
        if attribute_id in attribute_data.attribute_map
    ]
    attribute_values = [
        attribute_data.attribute_value_map[value_id]
        for value_id in assigned_value_ids
        if value_id in attribute_data.attribute_value_map
    ]

    values_map = defaultdict(list)
    for value in attribute_values:
        values_map[value.attribute_id].append(value)

    attributes_payload = []
    for attribute in attributes:
        attr = attribute
        attributes_payload.append(
            {
                "assignment": {
                    "attribute": {
                        "slug": attr.slug,
                        "name": attr.name,
                    }
                },
                "values": [
                    {
                        "name": value.name,
                        "value": value.value,
                        "slug": value.slug,
                        "file_url": value.file_url,
                    }
                    for value in values_map[attr.id]
                ],
            }
        )
    return attributes_payload


def get_product_payload(product: Product, attribute_data: AttributeData):
    all_media = product.media.all()
    images = [media for media in all_media if media.type == ProductMediaTypes.IMAGE]
    return {
        "id": to_global_id_or_none(product),
        "attributes": get_product_attributes_payload(product, attribute_data),
        "weight": str(product.weight or ""),
        **get_default_images_payload(images),
    }


def get_product_variant_payload(variant: ProductVariant):
    all_media = variant.media.all()
    images = [media for media in all_media if media.type == ProductMediaTypes.IMAGE]
    return {
        "id": to_global_id_or_none(variant),
        "weight": str(variant.weight or ""),
        "is_preorder": variant.is_preorder_active(),
        "preorder_global_threshold": variant.preorder_global_threshold,
        "preorder_end_date": variant.preorder_end_date,
        **get_default_images_payload(images),
    }


def get_order_line_payload(line: "OrderLine", attribute_data: AttributeData):
    digital_url: Optional[str] = None
    if line.is_digital:
        content = DigitalContentUrl.objects.filter(line=line).first()
        digital_url = content.get_absolute_url() if content else None
    variant_dependent_fields = {}
    if line.variant:
        variant_dependent_fields = {
            "product": get_product_payload(line.variant.product, attribute_data),
            "variant": get_product_variant_payload(line.variant),
        }
    currency = line.currency

    return {
        "id": to_global_id_or_none(line),
        "product": variant_dependent_fields.get("product"),
        "product_name": line.product_name,
        "translated_product_name": line.translated_product_name or line.product_name,
        "variant_name": line.variant_name,
        "variant": variant_dependent_fields.get("variant"),
        "translated_variant_name": line.translated_variant_name or line.variant_name,
        "product_sku": line.product_sku,
        "product_variant_id": line.product_variant_id,
        "quantity": line.quantity,
        "quantity_fulfilled": line.quantity_fulfilled,
        "currency": currency,
        "unit_price_net_amount": quantize_price(line.unit_price.net.amount, currency),
        "unit_price_gross_amount": quantize_price(
            line.unit_price.gross.amount, currency
        ),
        "unit_tax_amount": quantize_price(line.unit_price.tax.amount, currency),
        "total_gross_amount": quantize_price(line.total_price.gross.amount, currency),
        "total_net_amount": quantize_price(line.total_price.net.amount, currency),
        "total_tax_amount": quantize_price(line.total_price.tax.amount, currency),
        "tax_rate": line.tax_rate,
        "is_shipping_required": line.is_shipping_required,
        "is_digital": line.is_digital,
        "digital_url": digital_url,
        "unit_discount_value": line.unit_discount_value,
        "unit_discount_reason": line.unit_discount_reason,
        "unit_discount_type": line.unit_discount_type,
        "unit_discount_amount": line.unit_discount_amount,
        "metadata": line.metadata,
    }


def get_lines_payload(
    order_lines: Iterable["OrderLine"], attribute_data: AttributeData
):
    payload = []
    for line in order_lines:
        payload.append(get_order_line_payload(line, attribute_data))
    return payload


ADDRESS_MODEL_FIELDS = [
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
]


def get_address_payload(address):
    if not address:
        return None
    address = model_to_dict(address, fields=ADDRESS_MODEL_FIELDS)
    address["country"] = str(address["country"])
    address["phone"] = str(address["phone"])
    return address


def get_discounts_payload(order):
    order_discounts = order.discounts.all()
    voucher_discount = None
    all_discounts = []
    discount_amount = 0
    for order_discount in order_discounts:
        dicount_obj = {
            "type": order_discount.type,
            "value_type": order_discount.value_type,
            "value": order_discount.value,
            "amount_value": order_discount.amount_value,
            "name": order_discount.name,
            "translated_name": order_discount.translated_name,
            "reason": order_discount.reason,
        }
        all_discounts.append(dicount_obj)
        if order_discount.type == DiscountType.VOUCHER:
            voucher_discount = dicount_obj
        discount_amount += order_discount.amount_value

    return {
        "voucher_discount": voucher_discount,
        "discounts": all_discounts,
        "discount_amount": discount_amount,
    }


ORDER_MODEL_FIELDS = [
    "display_gross_prices",
    "currency",
    "total_gross_amount",
    "total_net_amount",
    "undiscounted_total_gross_amount",
    "undiscounted_total_net_amount",
    "status",
    "metadata",
    "private_metadata",
    "user_id",
    "language_code",
]

ORDER_PRICE_FIELDS = [
    "total_gross_amount",
    "total_net_amount",
    "undiscounted_total_gross_amount",
    "undiscounted_total_net_amount",
]


def get_custom_order_payload(order: Order):
    payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        **get_site_context(),
    }
    return payload


def get_default_order_payload(
    order: "Order",
    redirect_url: str = "",
    lines: Optional[Iterable["OrderLine"]] = None,
    attribute_data: Optional[AttributeData] = None,
):
    order_details_url = ""
    if redirect_url:
        order_details_url = prepare_order_details_url(order, redirect_url)
    subtotal = order.subtotal
    tax = order.total_gross_amount - order.total_net_amount or Decimal(0)

    if lines is None:
        lines = order.lines.prefetch_related(
            "variant__media",
            "variant__product__media",
            "variant__product__product_type",
        ).all()
    if attribute_data is None:
        attribute_data = get_attribute_data_from_order_lines(lines)

    currency = order.currency
    quantize_price_fields(order, fields=ORDER_PRICE_FIELDS, currency=currency)
    order_payload = model_to_dict(order, fields=ORDER_MODEL_FIELDS)
    order_payload.update(
        {
            "id": to_global_id_or_none(order),
            "token": order.id,  # DEPRECATED: will be removed in Saleor 4.0.
            "number": order.number,
            "channel_slug": order.channel.slug,
            "created": str(order.created_at),
            "shipping_price_net_amount": order.shipping_price_net_amount,
            "shipping_price_gross_amount": order.shipping_price_gross_amount,
            "order_details_url": order_details_url,
            "email": order.get_customer_email(),
            "subtotal_gross_amount": quantize_price(subtotal.gross.amount, currency),
            "subtotal_net_amount": quantize_price(subtotal.net.amount, currency),
            "tax_amount": quantize_price(tax, currency),
            "lines": get_lines_payload(lines, attribute_data),
            "billing_address": get_address_payload(order.billing_address),
            "shipping_address": get_address_payload(order.shipping_address),
            "shipping_method_name": order.shipping_method_name,
            "collection_point_name": order.collection_point_name,
            **get_discounts_payload(order),
        }
    )
    # Deprecated: override private_metadata with empty dict as it shouldn't be returned
    # in the payload (see SALEOR-7046). Should be removed in Saleor 4.0.
    order_payload["private_metadata"] = {}
    return order_payload


def get_default_fulfillment_line_payload(
    line: "FulfillmentLine", attribute_data: AttributeData
):
    return {
        "id": to_global_id_or_none(line),
        "order_line": get_order_line_payload(line.order_line, attribute_data),
        "quantity": line.quantity,
    }


def get_default_fulfillment_payload(order, fulfillment):
    lines = fulfillment.lines.prefetch_related(
        "order_line__variant__media",
        "order_line__variant__product__media",
        "order_line__variant__product__product_type",
    ).all()
    attribute_data = get_attribute_data_from_order_lines(
        [line.order_line for line in lines]
    )

    physical_lines = [line for line in lines if not line.order_line.is_digital]
    digital_lines = [line for line in lines if line.order_line.is_digital]

    payload = {
        "order": get_default_order_payload(
            order, order.redirect_url, attribute_data=attribute_data
        ),
        "fulfillment": {
            "tracking_number": fulfillment.tracking_number,
            "is_tracking_number_url": fulfillment.is_tracking_number_url,
        },
        "physical_lines": [
            get_default_fulfillment_line_payload(line, attribute_data)
            for line in physical_lines
        ],
        "digital_lines": [
            get_default_fulfillment_line_payload(line, attribute_data)
            for line in digital_lines
        ],
        "recipient_email": order.get_customer_email(),
        **get_site_context(),
    }
    return payload


def prepare_order_details_url(order: Order, redirect_url: str) -> str:
    params = urlencode({"token": order.id})
    return prepare_url(params, redirect_url)


def send_order_confirmation(order_info, redirect_url, manager):
    """Send notification with order confirmation."""

    def _generate_payload():
        payload = {
            "order": get_default_order_payload(order_info.order, redirect_url),
            "recipient_email": order_info.customer_email,
            **get_site_context(),
        }
        return payload

    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.ORDER_CONFIRMATION,
        payload_func=handler.payload,
        channel_slug=order_info.channel.slug,
    )

    # Prepare staff notification for this order
    staff_notifications = StaffNotificationRecipient.objects.filter(
        active=True, user__is_active=True, user__is_staff=True
    )
    recipient_emails = [
        notification.get_email() for notification in staff_notifications
    ]
    if recipient_emails:

        def _generate_staff_payload():
            payload = _generate_payload()
            payload = {
                "order": payload["order"],
                "recipient_list": recipient_emails,
                **get_site_context(),
            }
            return payload

        handler = NotifyHandler(_generate_payload)
        manager.notify(
            NotifyEventType.STAFF_ORDER_CONFIRMATION, payload_func=handler.payload
        )


def send_order_confirmed(order, user, app, manager):
    """Send email which tells customer that order has been confirmed."""

    def _generate_payload():
        payload = {
            "order": get_default_order_payload(order, order.redirect_url),
            "recipient_email": order.get_customer_email(),
            **get_site_context(),
        }
        attach_requester_payload_data(payload, user, app)
        return payload

    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.ORDER_CONFIRMED,
        payload_func=handler.payload,
        channel_slug=order.channel.slug,
    )


def send_fulfillment_confirmation_to_customer(order, fulfillment, user, app, manager):
    def _generate_payload():
        _payload = get_default_fulfillment_payload(order, fulfillment)
        attach_requester_payload_data(_payload, user, app)
        return _payload

    handler = NotifyHandler(_generate_payload)

    manager.notify(
        NotifyEventType.ORDER_FULFILLMENT_CONFIRMATION,
        payload_func=handler.payload,
        channel_slug=order.channel.slug,
    )


def send_fulfillment_update(order, fulfillment, manager):
    handler = NotifyHandler(
        partial(get_default_fulfillment_payload, order, fulfillment)
    )
    manager.notify(
        NotifyEventType.ORDER_FULFILLMENT_UPDATE,
        payload_func=handler.payload,
        channel_slug=order.channel.slug,
    )


def send_payment_confirmation(order_info, manager):
    """Send notification with the payment confirmation."""

    def _generate_payload():
        payment = order_info.payment
        payload = {
            "order": get_default_order_payload(order_info.order),
            "recipient_email": order_info.customer_email,
            **get_site_context(),
        }
        if payment:
            payment_currency = payment.currency
            payload.update(
                {
                    "payment": {
                        "created": payment.created_at,
                        "modified": payment.modified_at,
                        "charge_status": payment.charge_status,
                        "total": quantize_price(payment.total, payment_currency),
                        "captured_amount": quantize_price(
                            payment.captured_amount, payment_currency
                        ),
                        "currency": payment_currency,
                    }
                }
            )
        return payload

    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION,
        payload_func=handler.payload,
        channel_slug=order_info.channel.slug,
    )


def send_order_canceled_confirmation(
    order: "Order", user: Optional["User"], app: Optional["App"], manager
):
    def _generate_payload():
        payload = {
            "order": get_default_order_payload(order),
            "recipient_email": order.get_customer_email(),
            **get_site_context(),
        }
        attach_requester_payload_data(payload, user, app)
        return payload

    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.ORDER_CANCELED,
        payload_func=handler.payload,
        channel_slug=order.channel.slug,
    )


def send_order_refunded_confirmation(
    order: "Order",
    user: Optional["User"],
    app: Optional["App"],
    amount: "Decimal",
    currency: str,
    manager,
):
    def _generate_payload():
        payload = {
            "order": get_default_order_payload(order),
            "recipient_email": order.get_customer_email(),
            "amount": quantize_price(amount, currency),
            "currency": currency,
            **get_site_context(),
        }
        attach_requester_payload_data(payload, user, app)
        return payload

    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.ORDER_REFUND_CONFIRMATION,
        payload_func=handler.payload,
        channel_slug=order.channel.slug,
    )


def attach_requester_payload_data(
    payload: dict, user: Optional["User"], app: Optional["App"]
):
    payload["requester_user_id"] = to_global_id_or_none(user) if user else None
    payload["requester_app_id"] = to_global_id_or_none(app) if app else None

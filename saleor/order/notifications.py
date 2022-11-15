from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, List, Optional
from urllib.parse import urlencode

from django.forms import model_to_dict

from ..account.models import StaffNotificationRecipient
from ..core.notification.utils import get_site_context
from ..core.notify_events import NotifyEventType
from ..core.prices import quantize_price, quantize_price_fields
from ..core.utils.url import prepare_url
from ..discount import OrderDiscountType
from ..graphql.core.utils import to_global_id_or_none
from ..product import ProductMediaTypes
from ..product.models import DigitalContentUrl, Product, ProductMedia, ProductVariant
from ..thumbnail import THUMBNAIL_SIZES
from ..thumbnail.utils import get_image_or_proxy_url
from .models import FulfillmentLine, Order, OrderLine

if TYPE_CHECKING:
    from ..account.models import User  # noqa: F401
    from ..app.models import App


def get_image_payload(instance: ProductMedia):
    return {
        # This is temporary solution, the get_product_image_thumbnail_url
        # should be optimize - we should fetch all thumbnails at once instead of
        # fetching thumbnails by one for each size
        size: get_image_or_proxy_url(None, instance.id, "ProductMedia", size, None)
        for size in THUMBNAIL_SIZES
    }


def get_default_images_payload(images: List[ProductMedia]):
    first_image_payload = None
    first_image = images[0] if images else None
    if first_image:
        first_image_payload = {"original": get_image_payload(first_image)}
    images_payload = None
    if images:
        images_payload = [{"original": get_image_payload(image) for image in images}]
    return {"first_image": first_image_payload, "images": images_payload}


def get_product_attributes(product):
    attributes = product.attributes.all()
    attributes_payload = []
    for attr in attributes:
        attributes_payload.append(
            {
                "assignment": {
                    "attribute": {
                        "slug": attr.assignment.attribute.slug,
                        "name": attr.assignment.attribute.name,
                    }
                },
                "values": [
                    {
                        "name": value.name,
                        "value": value.value,
                        "slug": value.slug,
                        "file_url": value.file_url,
                    }
                    for value in attr.values.all()
                ],
            }
        )
    return attributes_payload


def get_product_payload(product: Product):
    all_media = product.media.all()
    images = [media for media in all_media if media.type == ProductMediaTypes.IMAGE]
    return {
        "id": to_global_id_or_none(product),
        "attributes": get_product_attributes(product),
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


def get_order_line_payload(line: "OrderLine"):
    digital_url = ""
    if line.is_digital:
        content = DigitalContentUrl.objects.filter(line=line).first()
        digital_url = content.get_absolute_url() if content else None  # type: ignore
    variant_dependent_fields = {}
    if line.variant:
        variant_dependent_fields = {
            "product": get_product_payload(line.variant.product),
            "variant": get_product_variant_payload(line.variant),
        }
    currency = line.currency

    return {
        "id": to_global_id_or_none(line),
        "product": variant_dependent_fields.get("product"),  # type: ignore
        "product_name": line.product_name,
        "translated_product_name": line.translated_product_name or line.product_name,
        "variant_name": line.variant_name,
        "variant": variant_dependent_fields.get("variant"),  # type: ignore
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
    }


def get_lines_payload(order_lines: Iterable["OrderLine"]):
    payload = []
    for line in order_lines:
        payload.append(get_order_line_payload(line))
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
        if order_discount.type == OrderDiscountType.VOUCHER:
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


def get_default_order_payload(order: "Order", redirect_url: str = ""):
    order_details_url = ""
    if redirect_url:
        order_details_url = prepare_order_details_url(order, redirect_url)
    subtotal = order.get_subtotal()
    tax = order.total_gross_amount - order.total_net_amount or Decimal(0)

    lines = order.lines.prefetch_related(
        "variant__product__media",
        "variant__media",
        "variant__product__attributes__assignment__attribute",
        "variant__product__attributes__values",
    ).all()
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
            "lines": get_lines_payload(lines),
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


def get_default_fulfillment_line_payload(line: "FulfillmentLine"):
    return {
        "id": to_global_id_or_none(line),
        "order_line": get_order_line_payload(line.order_line),
        "quantity": line.quantity,
    }


def get_default_fulfillment_payload(order, fulfillment):
    lines = fulfillment.lines.all()
    physical_lines = [line for line in lines if not line.order_line.is_digital]

    digital_lines = [line for line in lines if line.order_line.is_digital]
    payload = {
        "order": get_default_order_payload(order, order.redirect_url),
        "fulfillment": {
            "tracking_number": fulfillment.tracking_number,
            "is_tracking_number_url": fulfillment.is_tracking_number_url,
        },
        "physical_lines": [
            get_default_fulfillment_line_payload(line) for line in physical_lines
        ],
        "digital_lines": [
            get_default_fulfillment_line_payload(line) for line in digital_lines
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
    payload = {
        "order": get_default_order_payload(order_info.order, redirect_url),
        "recipient_email": order_info.customer_email,
        **get_site_context(),
    }
    manager.notify(
        NotifyEventType.ORDER_CONFIRMATION,
        payload,
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
        payload = {
            "order": payload["order"],
            "recipient_list": recipient_emails,
            **get_site_context(),
        }
        manager.notify(NotifyEventType.STAFF_ORDER_CONFIRMATION, payload=payload)


def send_order_confirmed(order, user, app, manager):
    """Send email which tells customer that order has been confirmed."""
    payload = {
        "order": get_default_order_payload(order, order.redirect_url),
        "recipient_email": order.get_customer_email(),
        **get_site_context(),
    }
    attach_requester_payload_data(payload, user, app)
    manager.notify(
        NotifyEventType.ORDER_CONFIRMED, payload, channel_slug=order.channel.slug
    )


def send_fulfillment_confirmation_to_customer(order, fulfillment, user, app, manager):
    payload = get_default_fulfillment_payload(order, fulfillment)
    attach_requester_payload_data(payload, user, app)
    manager.notify(
        NotifyEventType.ORDER_FULFILLMENT_CONFIRMATION,
        payload=payload,
        channel_slug=order.channel.slug,
    )


def send_fulfillment_update(order, fulfillment, manager):
    payload = get_default_fulfillment_payload(order, fulfillment)
    manager.notify(
        NotifyEventType.ORDER_FULFILLMENT_UPDATE,
        payload,
        channel_slug=order.channel.slug,
    )


def send_payment_confirmation(order_info, manager):
    """Send notification with the payment confirmation."""
    payment = order_info.payment
    payment_currency = payment.currency
    payload = {
        "order": get_default_order_payload(order_info.order),
        "recipient_email": order_info.customer_email,
        "payment": {
            "created": payment.created_at,
            "modified": payment.modified_at,
            "charge_status": payment.charge_status,
            "total": quantize_price(payment.total, payment_currency),
            "captured_amount": quantize_price(
                payment.captured_amount, payment_currency
            ),
            "currency": payment_currency,
        },
        **get_site_context(),
    }
    manager.notify(
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION,
        payload,
        channel_slug=order_info.channel.slug,
    )


def send_order_canceled_confirmation(
    order: "Order", user: Optional["User"], app: Optional["App"], manager
):
    payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        **get_site_context(),
    }
    attach_requester_payload_data(payload, user, app)
    manager.notify(
        NotifyEventType.ORDER_CANCELED, payload, channel_slug=order.channel.slug
    )


def send_order_refunded_confirmation(
    order: "Order",
    user: Optional["User"],
    app: Optional["App"],
    amount: "Decimal",
    currency: str,
    manager,
):
    payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "amount": quantize_price(amount, currency),
        "currency": currency,
        **get_site_context(),
    }
    attach_requester_payload_data(payload, user, app)
    manager.notify(
        NotifyEventType.ORDER_REFUND_CONFIRMATION,
        payload,
        channel_slug=order.channel.slug,
    )


def attach_requester_payload_data(
    payload: dict, user: Optional["User"], app: Optional["App"]
):
    payload["requester_user_id"] = to_global_id_or_none(user) if user else None
    payload["requester_app_id"] = to_global_id_or_none(app) if app else None

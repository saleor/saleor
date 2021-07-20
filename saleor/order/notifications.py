from typing import TYPE_CHECKING, Iterable, List, Optional
from urllib.parse import urlencode

from django.forms import model_to_dict

from ..account.models import StaffNotificationRecipient
from ..core.notifications import get_site_context
from ..core.notify_events import NotifyEventType
from ..core.utils.url import prepare_url
from ..discount import OrderDiscountType
from ..product import ProductMediaTypes
from ..product.models import DigitalContentUrl, Product, ProductMedia, ProductVariant
from ..product.product_images import AVAILABLE_PRODUCT_SIZES, get_thumbnail
from .models import FulfillmentLine, Order, OrderLine

if TYPE_CHECKING:
    from decimal import Decimal

    from ..account.models import User  # noqa: F401
    from ..app.models import App


def get_image_payload(instance: ProductMedia):
    image_file = instance.image if instance else None
    return {
        size: get_thumbnail(image_file, size, "thumbnail")
        for size in AVAILABLE_PRODUCT_SIZES
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
                        "name": value.get("name"),
                        "value": value.get("value"),
                        "slug": value.get("slug"),
                        "file_url": value.get("file_url"),
                    }
                    for value in attr.values.values("name", "value", "slug", "file_url")
                ],
            }
        )
    return attributes_payload


def get_product_payload(product: Product):
    all_media = product.media.all()
    images = [media for media in all_media if media.type == ProductMediaTypes.IMAGE]
    return {
        "id": product.id,
        "attributes": get_product_attributes(product),
        "weight": str(product.weight or ""),
        **get_default_images_payload(images),
    }


def get_product_variant_payload(variant: ProductVariant):
    all_media = variant.media.all()
    images = [media for media in all_media if media.type == ProductMediaTypes.IMAGE]
    return {
        "id": variant.id,
        "weight": str(variant.weight or ""),
        **get_default_images_payload(images),
    }


def get_order_line_payload(line: "OrderLine"):
    digital_url = ""
    if line.is_digital:
        content = DigitalContentUrl.objects.filter(line=line).first()
        digital_url = content.get_absolute_url() if content else None  # type: ignore
    return {
        "id": line.id,
        "product": get_product_payload(line.variant.product),  # type: ignore
        "product_name": line.product_name,
        "translated_product_name": line.translated_product_name or line.product_name,
        "variant_name": line.variant_name,
        "variant": get_product_variant_payload(line.variant),  # type: ignore
        "translated_variant_name": line.translated_variant_name or line.variant_name,
        "product_sku": line.product_sku,
        "quantity": line.quantity,
        "quantity_fulfilled": line.quantity_fulfilled,
        "currency": line.currency,
        "unit_price_net_amount": line.unit_price.net.amount,
        "unit_price_gross_amount": line.unit_price.gross.amount,
        "unit_tax_amount": line.unit_price.tax.amount,
        "total_gross_amount": line.total_price.gross.amount,
        "total_net_amount": line.total_price.net.amount,
        "total_tax_amount": line.total_price.tax.amount,
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
    "id",
    "token",
    "display_gross_prices",
    "currency",
    "discount_amount",
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


def get_default_order_payload(order: "Order", redirect_url: str = ""):
    order_details_url = ""
    if redirect_url:
        order_details_url = prepare_order_details_url(order, redirect_url)
    subtotal = order.get_subtotal()
    tax = order.total_gross_amount - order.total_net_amount

    lines = order.lines.prefetch_related(
        "variant__product__media",
        "variant__media",
        "variant__product__attributes__assignment__attribute",
        "variant__product__attributes__values",
    ).all()
    order_payload = model_to_dict(order, fields=ORDER_MODEL_FIELDS)
    order_payload.update(
        {
            "channel_slug": order.channel.slug,
            "created": str(order.created),
            "shipping_price_net_amount": order.shipping_price_net_amount,
            "shipping_price_gross_amount": order.shipping_price_gross_amount,
            "order_details_url": order_details_url,
            "email": order.get_customer_email(),
            "subtotal_gross_amount": subtotal.gross.amount,
            "subtotal_net_amount": subtotal.net.amount,
            "tax_amount": tax,
            "lines": get_lines_payload(lines),
            "billing_address": get_address_payload(order.billing_address),
            "shipping_address": get_address_payload(order.shipping_address),
            "shipping_method_name": order.shipping_method_name,
            **get_discounts_payload(order),
        }
    )
    return order_payload


def get_default_fulfillment_line_payload(line: "FulfillmentLine"):
    return {
        "id": line.id,
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
    params = urlencode({"token": order.token})
    return prepare_url(params, redirect_url)


def send_order_confirmation(order, redirect_url, manager):
    """Send notification with order confirmation."""
    payload = {
        "order": get_default_order_payload(order, redirect_url),
        "recipient_email": order.get_customer_email(),
        **get_site_context(),
    }
    manager.notify(
        NotifyEventType.ORDER_CONFIRMATION, payload, channel_slug=order.channel.slug
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


def send_payment_confirmation(order, manager):
    """Send notification with the payment confirmation."""
    payment = order.get_last_payment()
    payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "payment": {
            "created": payment.created,
            "modified": payment.modified,
            "charge_status": payment.charge_status,
            "total": payment.total,
            "captured_amount": payment.captured_amount,
            "currency": payment.currency,
        },
        **get_site_context(),
    }
    manager.notify(
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION,
        payload,
        channel_slug=order.channel.slug,
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
        "amount": amount,
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
    payload["requester_user_id"] = user.id if user else None
    payload["requester_app_id"] = app.id if app else None

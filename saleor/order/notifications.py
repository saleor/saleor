from typing import TYPE_CHECKING, Iterable, Optional
from urllib.parse import urlencode

from django.forms import model_to_dict

from ..account.models import StaffNotificationRecipient
from ..core.notify_events import NotifyEventType
from ..core.utils.url import prepare_url
from ..product.models import DigitalContentUrl
from . import events
from .models import FulfillmentLine, Order, OrderLine

if TYPE_CHECKING:
    from decimal import Decimal

    from ..account.models import User  # noqa: F401


def get_order_line_payload(line: "OrderLine"):
    unit_tax_amount = (line.unit_price_gross_amount - line.unit_price_net_amount,)
    total_gross = line.unit_price_gross * line.quantity
    total_net = line.unit_price_net * line.quantity
    total_tax = total_gross - total_net
    digital_url = ""
    if line.is_digital:
        content = DigitalContentUrl.objects.filter(line=line).first()
        digital_url = content.get_absolute_url() if content else None  # type: ignore
    return {
        "id": line.id,
        "product_name": line.translated_product_name or line.product_name,
        "variant_name": line.translated_variant_name or line.variant_name,
        "product_sku": line.product_sku,
        "quantity": line.quantity,
        "quantity_fulfilled": line.quantity_fulfilled,
        "currency": line.currency,
        "unit_price_net_amount": line.unit_price_net_amount,
        "unit_price_gross_amount": line.unit_price_gross_amount,
        "unit_tax_amount": unit_tax_amount,
        "total_gross_amount": total_gross.amount,
        "total_net_amount": total_net.amount,
        "total_tax_amount": total_tax.amount,
        "tax_rate": line.tax_rate,
        "is_shipping_required": line.is_shipping_required,
        "is_digital": line.is_digital,
        "digital_url": digital_url,
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


ORDER_MODEL_FIELDS = [
    "id",
    "token",
    "display_gross_prices",
    "currency",
    "discount_amount",
    "total_gross_amount",
    "total_net_amount",
    "status",
    "metadata",
    "private_metadata",
]


def get_default_order_payload(order: "Order", redirect_url: str = ""):
    order_details_url = ""
    if redirect_url:
        order_details_url = prepare_order_details_url(order, redirect_url)
    subtotal = order.get_subtotal()
    tax = order.total_gross_amount - order.total_net_amount

    order_payload = model_to_dict(order, fields=ORDER_MODEL_FIELDS)
    order_payload.update(
        {
            "created": order.created,
            "shipping_price_net_amount": order.shipping_price_net_amount,
            "shipping_price_gross_amount": order.shipping_price_gross_amount,
            "order_details_url": order_details_url,
            "email": order.get_customer_email(),
            "subtotal_gross_amount": subtotal.gross.amount,
            "subtotal_net_amount": subtotal.net.amount,
            "tax_amount": tax,
            "discount_name": order.translated_discount_name or order.discount_name,
            "lines": get_lines_payload(order.lines.all()),
            "billing_address": get_address_payload(order.billing_address),
            "shipping_address": get_address_payload(order.shipping_address),
            "shipping_method_name": order.shipping_method_name,
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
    payload = {"order": get_default_order_payload(order)}
    lines = fulfillment.lines.all()
    physical_lines = [line for line in lines if not line.order_line.is_digital]

    digital_lines = [line for line in lines if line.order_line.is_digital]
    payload.update(
        {
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
            "email": order.get_customer_email(),
        }
    )
    return payload


def prepare_order_details_url(order: Order, redirect_url: str) -> str:
    params = urlencode({"token": order.token})
    return prepare_url(params, redirect_url)


def send_order_confirmation(order, redirect_url, user, manager):
    """Send notification with order confirmation."""
    # FIXME Order payload should be placed in order key.
    order_payload = get_default_order_payload(order, redirect_url)
    manager.notify(NotifyEventType.ORDER_CONFIRMATION, order_payload)
    events.email_sent_event(
        order=order,
        user=None,
        user_pk=user.pk if user else None,
        email_type=events.OrderEventsEmails.ORDER_CONFIRMATION,
    )


def send_staff_order_confirmation(order, redirect_url, manager):
    """Send staff notification with order confirmation."""
    staff_notifications = StaffNotificationRecipient.objects.filter(
        active=True, user__is_active=True, user__is_staff=True
    )
    recipient_emails = [
        notification.get_email() for notification in staff_notifications
    ]
    if recipient_emails:
        payload = {
            "order": get_default_order_payload(order, redirect_url),
            "recipient_list": recipient_emails,
        }
        manager.notify(NotifyEventType.STAFF_ORDER_CONFIRMATION, payload=payload)


def send_fulfillment_confirmation_to_customer(order, fulfillment, user, manager):
    payload = get_default_fulfillment_payload(order, fulfillment)
    manager.notify(NotifyEventType.ORDER_FULFILLMENT_CONFIRMATION, payload=payload)

    events.email_sent_event(
        order=order, user=user, email_type=events.OrderEventsEmails.FULFILLMENT
    )

    # If digital lines were sent in the fulfillment email,
    # trigger the event
    if any((line for line in order if line.variant.is_digital())):
        events.email_sent_event(
            order=order, user=user, email_type=events.OrderEventsEmails.DIGITAL_LINKS
        )


def send_fulfillment_update(order, fulfillment, manager):
    payload = get_default_fulfillment_payload(order, fulfillment)
    manager.notify(NotifyEventType.ORDER_FULFILLMENT_UPDATE, payload)


def send_payment_confirmation(order, manager):
    """Send notification with the payment confirmation."""
    payment = order.get_last_payment()
    payload = {
        "order": get_default_order_payload(order),
        "email": order.get_customer_email(),
        "payment": {
            "created": payment.created,
            "modified": payment.modified,
            "charge_status": payment.charge_status,
            "total": payment.total,
            "captured_amount": payment.captured_amount,
            "currency": payment.currency,
        },
    }
    manager.notify(NotifyEventType.ORDER_PAYMENT_CONFIRMATION, payload)


def send_order_canceled_confirmation(order: "Order", user: Optional["User"], manager):
    payload = {
        "order": get_default_order_payload(order),
        "email": order.get_customer_email(),
    }
    manager.notify(NotifyEventType.ORDER_CANCELED, payload)
    events.email_sent_event(
        order=order, user=user, email_type=events.OrderEventsEmails.ORDER_CANCEL
    )


def send_order_refunded_confirmation(
    order: "Order", user: Optional["User"], amount: "Decimal", currency: str, manager
):
    payload = get_default_order_payload(order)
    payload.update({"amount": amount, "currency": currency})
    manager.notify(NotifyEventType.ORDER_REFUND_CONFIRMATION, payload)
    events.email_sent_event(
        order=order, user=user, email_type=events.OrderEventsEmails.ORDER_REFUND
    )

from django.conf import settings
from django.template import Library
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django_prices.templatetags import prices_i18n
from prices import Money

from ...order import events
from ...order.models import OrderEvent

register = Library()

EMAIL_CHOICES = {
    events.OrderEventsEmails.PAYMENT: pgettext_lazy(
        "Email type", "Payment confirmation"
    ),
    events.OrderEventsEmails.SHIPPING: pgettext_lazy(
        "Email type", "Shipping confirmation"
    ),
    events.OrderEventsEmails.FULFILLMENT: pgettext_lazy(
        "Email type", "Fulfillment confirmation"
    ),
    events.OrderEventsEmails.ORDER: pgettext_lazy("Email type", "Order confirmation"),
}


def get_money_from_params(amount):
    """Retrieve the correct money amount from the given object.

    Money serialization changed at one point, as for now it's serialized
    as a dict. But we keep those settings for the legacy data.

    Can be safely removed after migrating to Dashboard 2.0
    """
    if isinstance(amount, Money):
        return amount
    if isinstance(amount, dict):
        return Money(amount=amount["amount"], currency=amount["currency"])
    return Money(amount, settings.DEFAULT_CURRENCY)


@register.simple_tag
def display_order_event(order_event: OrderEvent):
    """Keep the backwards compatibility with the old dashboard and new type of events.

    The new one is storing enums values instead of raw messages.
    """
    event_type = order_event.type
    params = order_event.parameters
    if event_type == events.OrderEvents.PLACED_FROM_DRAFT:
        return pgettext_lazy(
            "Dashboard message related to an order", "Order placed from draft order"
        )
    if event_type == events.OrderEvents.PAYMENT_VOIDED:
        return pgettext_lazy(
            "Dashboard message related to an order",
            "Payment was voided by %(user_name)s" % {"user_name": order_event.user},
        )
    if event_type == events.OrderEvents.PAYMENT_REFUNDED:
        amount = get_money_from_params(params["amount"])
        return pgettext_lazy(
            "Dashboard message related to an order",
            "Successfully refunded: %(amount)s"
            % {"amount": prices_i18n.amount(amount)},
        )
    if event_type == events.OrderEvents.PAYMENT_CAPTURED:
        amount = get_money_from_params(params["amount"])
        return pgettext_lazy(
            "Dashboard message related to an order",
            "Successfully captured: %(amount)s"
            % {"amount": prices_i18n.amount(amount)},
        )
    if event_type == events.OrderEvents.ORDER_MARKED_AS_PAID:
        return pgettext_lazy(
            "Dashboard message related to an order", "Order manually marked as paid"
        )
    if event_type == events.OrderEvents.CANCELED:
        return pgettext_lazy(
            "Dashboard message related to an order", "Order was canceled"
        )
    if event_type == events.OrderEvents.FULFILLMENT_RESTOCKED_ITEMS:
        return npgettext_lazy(
            "Dashboard message related to an order",
            "We restocked %(quantity)d item",
            "We restocked %(quantity)d items",
            number="quantity",
        ) % {"quantity": params["quantity"]}
    if event_type == events.OrderEvents.NOTE_ADDED:
        return pgettext_lazy(
            "Dashboard message related to an order",
            "%(user_name)s added note: %(note)s"
            % {"note": params["message"], "user_name": order_event.user},
        )
    if event_type == events.OrderEvents.FULFILLMENT_CANCELED:
        return pgettext_lazy(
            "Dashboard message",
            "Fulfillment #%(fulfillment)s canceled by %(user_name)s",
        ) % {"fulfillment": params["composed_id"], "user_name": order_event.user}
    if event_type == events.OrderEvents.FULFILLMENT_FULFILLED_ITEMS:
        return pgettext_lazy(
            "Dashboard message related to an order", "Fulfilled some items"
        )
    if event_type == events.OrderEvents.PLACED:
        return pgettext_lazy(
            "Dashboard message related to an order", "Order was placed"
        )
    if event_type == events.OrderEvents.ORDER_FULLY_PAID:
        return pgettext_lazy(
            "Dashboard message related to an order", "Order was fully paid"
        )
    if event_type == events.OrderEvents.EMAIL_SENT:
        return pgettext_lazy(
            "Dashboard message related to an order",
            "%(email_type)s email was sent to the customer " "(%(email)s)",
        ) % {
            "email_type": EMAIL_CHOICES[params["email_type"]],
            "email": params["email"],
        }
    if event_type == events.OrderEvents.TRACKING_UPDATED:
        return pgettext_lazy(
            "Dashboard message related to an order",
            "Fulfillment #%(fulfillment)s tracking was updated to"
            " %(tracking_number)s by %(user_name)s",
        ) % {
            "fulfillment": params["composed_id"],
            "tracking_number": params["tracking_number"],
            "user_name": order_event.user,
        }
    if event_type == events.OrderEvents.DRAFT_CREATED:
        return pgettext_lazy(
            "Dashboard message related to an order",
            "The draft was created by %(user_name)s",
        ) % {"user_name": order_event.user}
    if event_type == events.OrderEvents.DRAFT_ADDED_PRODUCTS:
        return pgettext_lazy(
            "Dashboard message related to an order", "%(user_name)s added some products"
        ) % {"user_name": order_event.user}
    if event_type == events.OrderEvents.DRAFT_REMOVED_PRODUCTS:
        return pgettext_lazy(
            "Dashboard message related to an order",
            "%(user_name)s removed some products",
        ) % {"user_name": order_event.user}
    if event_type == events.OrderEvents.OVERSOLD_ITEMS:
        return pgettext_lazy(
            "Dashboard message related to an order",
            "%(user_name)s placed the order by bypassing oversold items",
        ) % {"user_name": order_event.user}
    if event_type == events.OrderEvents.UPDATED_ADDRESS:
        return pgettext_lazy(
            "Dashboard message related to an order",
            "The order address was updated by %(user_name)s",
        ) % {"user_name": order_event.user}
    if event_type == events.OrderEvents.PAYMENT_FAILED:
        return pgettext_lazy(
            "Dashboard message related to an order",
            "The payment was failed by %(user_name)s",
        ) % {"user_name": order_event.user}

    if event_type == events.OrderEvents.OTHER:
        return order_event.parameters["message"]
    raise ValueError("Not supported event type: %s" % (event_type))

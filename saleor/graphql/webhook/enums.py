import graphene

from ...webhook.event_types import WebhookEventType
from ..core.utils import str_to_enum


def description(enum):
    if enum == WebhookEventTypeEnum.CHECKOUT_CREATED:
        return "A new checkout is created."
    elif enum == WebhookEventTypeEnum.CHECKOUT_UPDATED:
        return "A checkout is updated. Also triggers for all updates related to a checkout."
    elif enum == WebhookEventTypeEnum.CUSTOMER_CREATED:
        return "A new customer account is created."
    elif enum == WebhookEventTypeEnum.ORDER_CREATED:
        return "A new order is placed."
    elif enum == WebhookEventTypeEnum.ORDER_CONFIRMED:
        return "An order is confirmed (status change unconfirmed -> unfulfilled) by staff user using OrderConfirm mutation. Also triggers when user finish checkout and shop setting `automatically_confirm_all_new_orders` is enabled."
    elif enum == WebhookEventTypeEnum.ORDER_FULLY_PAID:
        return "Payment is made and an order is fully paid."
    elif enum == WebhookEventTypeEnum.ORDER_UPDATED:
        return "An order is updated; triggered for all changes related to an order; covers all other order webhooks, except for ORDER_CREATED."
    elif enum == WebhookEventTypeEnum.ORDER_CANCELLED:
        return "An order is cancelled."
    elif enum == WebhookEventTypeEnum.ORDER_FULFILLED:
        return "An order is fulfilled."
    elif enum == WebhookEventTypeEnum.FULFILLMENT_CREATED:
        return "A new fulfillment is created."
    elif enum == WebhookEventTypeEnum.PRODUCT_CREATED:
        return "A new product is created."
    elif enum == WebhookEventTypeEnum.PRODUCT_UPDATED:
        return "A product is updated."
    elif enum == WebhookEventTypeEnum.INVOICE_REQUESTED:
        return "An invoice for order requested."
    elif enum == WebhookEventTypeEnum.INVOICE_DELETED:
        return "An invoice is deleted."
    elif enum == WebhookEventTypeEnum.INVOICE_SENT:
        return "Invoice has been send."
    elif enum == WebhookEventTypeEnum.ANY_EVENTS:
        return "All the events."
    return "Enum determining type of webhook."


WebhookEventTypeEnum = graphene.Enum(
    "WebhookEventTypeEnum",
    [(str_to_enum(e_type[0]), e_type[0]) for e_type in WebhookEventType.CHOICES],
    description=description,
)
WebhookSampleEventTypeEnum = graphene.Enum(
    "WebhookSampleEventTypeEnum",
    [
        (str_to_enum(e_type[0]), e_type[0])
        for e_type in WebhookEventType.CHOICES
        if e_type[0] != WebhookEventType.ANY
    ],
)

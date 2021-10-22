import graphene

from ...webhook.event_types import WebhookEventType
from ..core.utils import str_to_enum


def description(enum):
    if enum is None:
        return "Enum determining type of webhook."
    elif enum == WebhookEventTypeEnum.CHECKOUT_CREATED:
        return "A new checkout is created."
    elif enum == WebhookEventTypeEnum.CHECKOUT_UPDATED:
        return (
            "A checkout is updated. "
            "It also triggers all updates related to the checkout."
        )
    elif enum == WebhookEventTypeEnum.CUSTOMER_CREATED:
        return "A new customer account is created."
    elif enum == WebhookEventTypeEnum.CUSTOMER_UPDATED:
        return "A customer account is updated."
    elif enum == WebhookEventTypeEnum.NOTIFY_USER:
        return "User notification triggered."
    elif enum == WebhookEventTypeEnum.ORDER_CREATED:
        return "A new order is placed."
    elif enum == WebhookEventTypeEnum.ORDER_CONFIRMED:
        return (
            "An order is confirmed (status change unconfirmed -> unfulfilled) "
            "by a staff user using the OrderConfirm mutation. "
            "It also triggers when the user completes the checkout and the shop "
            "setting `automatically_confirm_all_new_orders` is enabled."
        )
    elif enum == WebhookEventTypeEnum.ORDER_FULLY_PAID:
        return "Payment is made and an order is fully paid."
    elif enum == WebhookEventTypeEnum.ORDER_UPDATED:
        return (
            "An order is updated; triggered for all changes related to an order; "
            "covers all other order webhooks, except for ORDER_CREATED."
        )
    elif enum == WebhookEventTypeEnum.ORDER_CANCELLED:
        return "An order is cancelled."
    elif enum == WebhookEventTypeEnum.ORDER_FULFILLED:
        return "An order is fulfilled."
    elif enum == WebhookEventTypeEnum.FULFILLMENT_CREATED:
        return "A new fulfillment is created."
    elif enum == WebhookEventTypeEnum.FULFILLMENT_CANCELED:
        return "A fulfillment is cancelled."
    elif enum == WebhookEventTypeEnum.PAGE_CREATED:
        return "A new page is created."
    elif enum == WebhookEventTypeEnum.PAGE_UPDATED:
        return "A page is updated."
    elif enum == WebhookEventTypeEnum.PAGE_DELETED:
        return "A page is deleted."
    elif enum == WebhookEventTypeEnum.PRODUCT_CREATED:
        return "A new product is created."
    elif enum == WebhookEventTypeEnum.PRODUCT_UPDATED:
        return "A product is updated."
    elif enum == WebhookEventTypeEnum.PRODUCT_DELETED:
        return "A product is deleted."
    elif enum == WebhookEventTypeEnum.PRODUCT_VARIANT_CREATED:
        return "A new product variant is created."
    elif enum == WebhookEventTypeEnum.PRODUCT_VARIANT_UPDATED:
        return "A product variant is updated."
    elif enum == WebhookEventTypeEnum.PRODUCT_VARIANT_DELETED:
        return "A product variant is deleted."
    elif enum == WebhookEventTypeEnum.INVOICE_REQUESTED:
        return "An invoice for order requested."
    elif enum == WebhookEventTypeEnum.INVOICE_DELETED:
        return "An invoice is deleted."
    elif enum == WebhookEventTypeEnum.INVOICE_SENT:
        return "Invoice has been sent."
    elif enum == WebhookEventTypeEnum.ANY_EVENTS:
        return "All the events."
    return None


WebhookEventTypeEnum = graphene.Enum(
    "WebhookEventTypeEnum",
    [(str_to_enum(e_type[0]), e_type[0]) for e_type in WebhookEventType.CHOICES],
    description=description,
)

WebhookEventTypeSync = graphene.Enum(
    "WebhookEventTypeSync",
    [
        (str_to_enum(e_type[0]), e_type[0])
        for e_type in WebhookEventType.CHOICES
        if e_type[0] in WebhookEventType.SYNC_EVENTS
    ],
    description=description,
)

WebhookEventTypeAsync = graphene.Enum(
    "WebhookEventTypeAsync",
    [
        (str_to_enum(e_type[0]), e_type[0])
        for e_type in WebhookEventType.CHOICES
        if not e_type[0] in WebhookEventType.SYNC_EVENTS
    ],
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

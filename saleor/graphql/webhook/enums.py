import graphene

from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..core.utils import str_to_enum


def description(enum):
    if enum is None:
        return "Enum determining type of webhook."
    elif enum == WebhookEventTypeAsyncEnum.CHECKOUT_CREATED:
        return "A new checkout is created."
    elif enum == WebhookEventTypeAsyncEnum.CHECKOUT_UPDATED:
        return (
            "A checkout is updated. "
            "It also triggers all updates related to the checkout."
        )
    elif enum == WebhookEventTypeAsyncEnum.COLLECTION_CREATED:
        return "A new collection is created."
    elif enum == WebhookEventTypeAsyncEnum.COLLECTION_UPDATED:
        return "A collection is updated."
    elif enum == WebhookEventTypeAsyncEnum.COLLECTION_DELETED:
        return "A collection is deleted."
    elif enum == WebhookEventTypeAsyncEnum.CUSTOMER_CREATED:
        return "A new customer account is created."
    elif enum == WebhookEventTypeAsyncEnum.CUSTOMER_UPDATED:
        return "A customer account is updated."
    elif enum == WebhookEventTypeAsyncEnum.NOTIFY_USER:
        return "User notification triggered."
    elif enum == WebhookEventTypeAsyncEnum.ORDER_CREATED:
        return "A new order is placed."
    elif enum == WebhookEventTypeAsyncEnum.ORDER_CONFIRMED:
        return (
            "An order is confirmed (status change unconfirmed -> unfulfilled) "
            "by a staff user using the OrderConfirm mutation. "
            "It also triggers when the user completes the checkout and the shop "
            "setting `automatically_confirm_all_new_orders` is enabled."
        )
    elif enum == WebhookEventTypeAsyncEnum.ORDER_FULLY_PAID:
        return "Payment is made and an order is fully paid."
    elif enum == WebhookEventTypeAsyncEnum.ORDER_UPDATED:
        return (
            "An order is updated; triggered for all changes related to an order; "
            "covers all other order webhooks, except for ORDER_CREATED."
        )
    elif enum == WebhookEventTypeAsyncEnum.ORDER_CANCELLED:
        return "An order is cancelled."
    elif enum == WebhookEventTypeAsyncEnum.ORDER_FULFILLED:
        return "An order is fulfilled."
    elif enum == WebhookEventTypeAsyncEnum.FULFILLMENT_CREATED:
        return "A new fulfillment is created."
    elif enum == WebhookEventTypeAsyncEnum.FULFILLMENT_CANCELED:
        return "A fulfillment is cancelled."
    elif enum == WebhookEventTypeAsyncEnum.PAGE_CREATED:
        return "A new page is created."
    elif enum == WebhookEventTypeAsyncEnum.PAGE_UPDATED:
        return "A page is updated."
    elif enum == WebhookEventTypeAsyncEnum.PAGE_DELETED:
        return "A page is deleted."
    elif enum == WebhookEventTypeAsyncEnum.PRODUCT_CREATED:
        return "A new product is created."
    elif enum == WebhookEventTypeAsyncEnum.PRODUCT_UPDATED:
        return "A product is updated."
    elif enum == WebhookEventTypeAsyncEnum.PRODUCT_DELETED:
        return "A product is deleted."
    elif enum == WebhookEventTypeAsyncEnum.PRODUCT_VARIANT_CREATED:
        return "A new product variant is created."
    elif enum == WebhookEventTypeAsyncEnum.PRODUCT_VARIANT_UPDATED:
        return "A product variant is updated."
    elif enum == WebhookEventTypeAsyncEnum.PRODUCT_VARIANT_DELETED:
        return "A product variant is deleted."
    elif enum == WebhookEventTypeAsyncEnum.INVOICE_REQUESTED:
        return "An invoice for order requested."
    elif enum == WebhookEventTypeAsyncEnum.INVOICE_DELETED:
        return "An invoice is deleted."
    elif enum == WebhookEventTypeAsyncEnum.INVOICE_SENT:
        return "Invoice has been sent."
    elif enum == WebhookEventTypeAsyncEnum.ANY_EVENTS:
        return "All the events."
    return None


WebhookEventTypeEnum = graphene.Enum(
    "WebhookEventTypeEnum",
    [
        (str_to_enum(e_type[0]), e_type[0])
        for e_type in (WebhookEventAsyncType.CHOICES + WebhookEventSyncType.CHOICES)
    ],
    description=description,
)


WebhookEventTypeAsyncEnum = graphene.Enum(
    "WebhookEventTypeAsyncEnum",
    [(str_to_enum(e_type[0]), e_type[0]) for e_type in WebhookEventAsyncType.CHOICES],
    description=description,
)

WebhookEventTypeSyncEnum = graphene.Enum(
    "WebhookEventTypeSyncEnum",
    [(str_to_enum(e_type[0]), e_type[0]) for e_type in WebhookEventSyncType.CHOICES],
    description=description,
)

WebhookSampleEventTypeEnum = graphene.Enum(
    "WebhookSampleEventTypeEnum",
    [
        (str_to_enum(e_type[0]), e_type[0])
        for e_type in WebhookEventAsyncType.CHOICES
        if e_type[0] != WebhookEventAsyncType.ANY
    ],
)


class EventDeliveryStatusEnum(graphene.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

import graphene

from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..core.utils import str_to_enum

checkout_updated_event_enum_description = (
    "A checkout is updated. It also triggers all updates related to the checkout."
)

order_confirmed_event_enum_description = (
    "An order is confirmed (status change unconfirmed -> unfulfilled) "
    "by a staff user using the OrderConfirm mutation. "
    "It also triggers when the user completes the checkout and the shop "
    "setting `automatically_confirm_all_new_orders` is enabled."
)

order_fully_paid_event_enum_description = "Payment is made and an order is fully paid."

order_updated_event_enum_description = (
    "An order is updated; triggered for all changes related to an order; "
    "covers all other order webhooks, except for ORDER_CREATED."
)


WEBHOOK_EVENT_DESCRIPTION = {
    WebhookEventAsyncType.APP_CREATED: "A new app created.",
    WebhookEventAsyncType.APP_UPDATED: "An app updated.",
    WebhookEventAsyncType.APP_DELETED: "An app deleted.",
    WebhookEventAsyncType.APP_STATUS_CHANGED: "An app status is changed.",
    WebhookEventAsyncType.CATEGORY_CREATED: "A new category created.",
    WebhookEventAsyncType.CATEGORY_UPDATED: "A category is updated.",
    WebhookEventAsyncType.CATEGORY_DELETED: "A category is deleted.",
    WebhookEventAsyncType.CHANNEL_CREATED: "A new channel created.",
    WebhookEventAsyncType.CHANNEL_UPDATED: "A channel is updated.",
    WebhookEventAsyncType.CHANNEL_DELETED: "A channel is deleted.",
    WebhookEventAsyncType.CHANNEL_STATUS_CHANGED: "A channel status is changed.",
    WebhookEventAsyncType.CHECKOUT_CREATED: "A new checkout is created.",
    WebhookEventAsyncType.CHECKOUT_UPDATED: checkout_updated_event_enum_description,
    WebhookEventAsyncType.COLLECTION_CREATED: "A new collection is created.",
    WebhookEventAsyncType.COLLECTION_UPDATED: "A collection is updated.",
    WebhookEventAsyncType.COLLECTION_DELETED: "A collection is deleted.",
    WebhookEventAsyncType.CUSTOMER_CREATED: "A new customer account is created.",
    WebhookEventAsyncType.CUSTOMER_UPDATED: "A customer account is updated.",
    WebhookEventAsyncType.GIFT_CARD_CREATED: "A new gift card created.",
    WebhookEventAsyncType.GIFT_CARD_UPDATED: "A gift card is updated.",
    WebhookEventAsyncType.GIFT_CARD_DELETED: "A gift card is deleted.",
    WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED: "A gift card status is changed.",
    WebhookEventAsyncType.INVOICE_REQUESTED: "An invoice for order requested.",
    WebhookEventAsyncType.INVOICE_DELETED: "An invoice is deleted.",
    WebhookEventAsyncType.INVOICE_SENT: "Invoice has been sent.",
    WebhookEventAsyncType.MENU_CREATED: "A new menu created.",
    WebhookEventAsyncType.MENU_UPDATED: "A menu is updated.",
    WebhookEventAsyncType.MENU_DELETED: "A menu is deleted.",
    WebhookEventAsyncType.MENU_ITEM_CREATED: "A new menu item created.",
    WebhookEventAsyncType.MENU_ITEM_UPDATED: "A menu item is updated.",
    WebhookEventAsyncType.MENU_ITEM_DELETED: "A menu item is deleted.",
    WebhookEventAsyncType.NOTIFY_USER: "User notification triggered.",
    WebhookEventAsyncType.ORDER_CREATED: "A new order is placed.",
    WebhookEventAsyncType.ORDER_CONFIRMED: order_confirmed_event_enum_description,
    WebhookEventAsyncType.ORDER_FULLY_PAID: order_fully_paid_event_enum_description,
    WebhookEventAsyncType.ORDER_UPDATED: order_updated_event_enum_description,
    WebhookEventAsyncType.ORDER_CANCELLED: "An order is cancelled.",
    WebhookEventAsyncType.ORDER_FULFILLED: "An order is fulfilled.",
    WebhookEventAsyncType.FULFILLMENT_CREATED: "A new fulfillment is created.",
    WebhookEventAsyncType.FULFILLMENT_CANCELED: "A fulfillment is cancelled.",
    WebhookEventAsyncType.PAGE_CREATED: "A new page is created.",
    WebhookEventAsyncType.PAGE_UPDATED: "A page is updated.",
    WebhookEventAsyncType.PAGE_DELETED: "A page is deleted.",
    WebhookEventAsyncType.PRODUCT_CREATED: "A new product is created.",
    WebhookEventAsyncType.PRODUCT_UPDATED: "A product is updated.",
    WebhookEventAsyncType.PRODUCT_DELETED: "A product is deleted.",
    WebhookEventAsyncType.PRODUCT_VARIANT_CREATED: "A new product variant is created.",
    WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED: "A product variant is updated.",
    WebhookEventAsyncType.PRODUCT_VARIANT_DELETED: "A product variant is deleted.",
    WebhookEventAsyncType.SHIPPING_PRICE_CREATED: "A new shipping price is created.",
    WebhookEventAsyncType.SHIPPING_PRICE_UPDATED: "A shipping price is updated.",
    WebhookEventAsyncType.SHIPPING_PRICE_DELETED: "A shipping price is deleted.",
    WebhookEventAsyncType.SHIPPING_ZONE_CREATED: "A new shipping zone is created.",
    WebhookEventAsyncType.SHIPPING_ZONE_UPDATED: "A shipping zone is updated.",
    WebhookEventAsyncType.SHIPPING_ZONE_DELETED: "A shipping zone is deleted.",
    WebhookEventAsyncType.VOUCHER_CREATED: "A new voucher created.",
    WebhookEventAsyncType.VOUCHER_UPDATED: "A voucher is updated.",
    WebhookEventAsyncType.VOUCHER_DELETED: "A voucher is deleted.",
    WebhookEventAsyncType.ANY: "All the events.",
}


def description(enum):
    if enum:
        return WEBHOOK_EVENT_DESCRIPTION.get(enum.value)
    return "Enum determining type of webhook."


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

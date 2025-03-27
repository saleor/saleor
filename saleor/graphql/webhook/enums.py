import graphene

from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..core.descriptions import (
    ADDED_IN_318,
    DEFAULT_DEPRECATION_REASON,
)
from ..core.doc_category import DOC_CATEGORY_WEBHOOKS
from ..core.types import BaseEnum
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
    WebhookEventAsyncType.ACCOUNT_CONFIRMATION_REQUESTED: (
        "An account confirmation is requested."
    ),
    WebhookEventAsyncType.ACCOUNT_EMAIL_CHANGED: "An account email was changed",
    WebhookEventAsyncType.ACCOUNT_CHANGE_EMAIL_REQUESTED: (
        "An account email change is requested."
    ),
    WebhookEventAsyncType.ACCOUNT_SET_PASSWORD_REQUESTED: (
        "Setting a new password for the account is requested."
    ),
    WebhookEventAsyncType.ACCOUNT_CONFIRMED: "An account is confirmed.",
    WebhookEventAsyncType.ACCOUNT_DELETE_REQUESTED: "An account delete is requested.",
    WebhookEventAsyncType.ACCOUNT_DELETED: "An account is deleted.",
    WebhookEventAsyncType.ADDRESS_CREATED: "A new address created.",
    WebhookEventAsyncType.ADDRESS_UPDATED: "An address updated.",
    WebhookEventAsyncType.ADDRESS_DELETED: "An address deleted.",
    WebhookEventAsyncType.APP_INSTALLED: "A new app installed.",
    WebhookEventAsyncType.APP_UPDATED: "An app updated.",
    WebhookEventAsyncType.APP_DELETED: "An app deleted.",
    WebhookEventAsyncType.APP_STATUS_CHANGED: "An app status is changed.",
    WebhookEventAsyncType.ATTRIBUTE_CREATED: "A new attribute is created.",
    WebhookEventAsyncType.ATTRIBUTE_UPDATED: "An attribute is updated.",
    WebhookEventAsyncType.ATTRIBUTE_DELETED: "An attribute is deleted.",
    WebhookEventAsyncType.ATTRIBUTE_VALUE_CREATED: "A new attribute value is created.",
    WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED: "An attribute value is updated.",
    WebhookEventAsyncType.ATTRIBUTE_VALUE_DELETED: "An attribute value is deleted.",
    WebhookEventAsyncType.CATEGORY_CREATED: "A new category created.",
    WebhookEventAsyncType.CATEGORY_UPDATED: "A category is updated.",
    WebhookEventAsyncType.CATEGORY_DELETED: "A category is deleted.",
    WebhookEventAsyncType.CHANNEL_CREATED: "A new channel created.",
    WebhookEventAsyncType.CHANNEL_UPDATED: "A channel is updated.",
    WebhookEventAsyncType.CHANNEL_DELETED: "A channel is deleted.",
    WebhookEventAsyncType.CHANNEL_STATUS_CHANGED: "A channel status is changed.",
    WebhookEventAsyncType.CHANNEL_METADATA_UPDATED: "A channel metadata is updated.",
    WebhookEventAsyncType.CHECKOUT_CREATED: "A new checkout is created.",
    WebhookEventAsyncType.CHECKOUT_UPDATED: checkout_updated_event_enum_description,
    WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED: "A checkout metadata is updated.",
    WebhookEventAsyncType.COLLECTION_CREATED: "A new collection is created.",
    WebhookEventAsyncType.COLLECTION_UPDATED: "A collection is updated.",
    WebhookEventAsyncType.COLLECTION_DELETED: "A collection is deleted.",
    WebhookEventAsyncType.COLLECTION_METADATA_UPDATED: "A collection metadata is updated.",
    WebhookEventAsyncType.CUSTOMER_CREATED: "A new customer account is created.",
    WebhookEventAsyncType.CUSTOMER_UPDATED: "A customer account is updated.",
    WebhookEventAsyncType.CUSTOMER_DELETED: "A customer account is deleted.",
    WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED: "A customer account metadata is updated.",
    WebhookEventAsyncType.GIFT_CARD_CREATED: "A new gift card created.",
    WebhookEventAsyncType.GIFT_CARD_UPDATED: "A gift card is updated.",
    WebhookEventAsyncType.GIFT_CARD_DELETED: "A gift card is deleted.",
    WebhookEventAsyncType.GIFT_CARD_SENT: "A gift card has been sent.",
    WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED: "A gift card status is changed.",
    WebhookEventAsyncType.GIFT_CARD_METADATA_UPDATED: "A gift card metadata is updated.",
    WebhookEventAsyncType.GIFT_CARD_EXPORT_COMPLETED: "A gift card export is completed.",
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
    WebhookEventAsyncType.ORDER_PAID: (
        "Payment has been made. The order may be partially or fully paid."
    ),
    WebhookEventAsyncType.ORDER_FULLY_PAID: order_fully_paid_event_enum_description,
    WebhookEventAsyncType.ORDER_REFUNDED: (
        "The order received a refund. The order may be partially or fully refunded."
    ),
    WebhookEventAsyncType.ORDER_FULLY_REFUNDED: ("The order is fully refunded."),
    WebhookEventAsyncType.ORDER_UPDATED: order_updated_event_enum_description,
    WebhookEventAsyncType.ORDER_CANCELLED: "An order is cancelled.",
    WebhookEventAsyncType.ORDER_EXPIRED: "An order is expired.",
    WebhookEventAsyncType.ORDER_FULFILLED: "An order is fulfilled.",
    WebhookEventAsyncType.ORDER_METADATA_UPDATED: ("An order metadata is updated."),
    WebhookEventAsyncType.ORDER_BULK_CREATED: "Orders are imported.",
    WebhookEventAsyncType.DRAFT_ORDER_CREATED: "A draft order is created.",
    WebhookEventAsyncType.DRAFT_ORDER_UPDATED: "A draft order is updated.",
    WebhookEventAsyncType.DRAFT_ORDER_DELETED: "A draft order is deleted.",
    WebhookEventAsyncType.SALE_CREATED: "A sale is created.",
    WebhookEventAsyncType.SALE_UPDATED: "A sale is updated.",
    WebhookEventAsyncType.SALE_DELETED: "A sale is deleted.",
    WebhookEventAsyncType.SALE_TOGGLE: "A sale is activated or deactivated.",
    WebhookEventAsyncType.PROMOTION_CREATED: "A promotion is created.",
    WebhookEventAsyncType.PROMOTION_UPDATED: "A promotion is updated.",
    WebhookEventAsyncType.PROMOTION_DELETED: "A promotion is deleted.",
    WebhookEventAsyncType.PROMOTION_STARTED: "A promotion is activated.",
    WebhookEventAsyncType.PROMOTION_ENDED: "A promotion is deactivated.",
    WebhookEventAsyncType.PROMOTION_RULE_CREATED: "A promotion rule is created.",
    WebhookEventAsyncType.PROMOTION_RULE_UPDATED: "A promotion rule is updated.",
    WebhookEventAsyncType.PROMOTION_RULE_DELETED: "A promotion rule is deleted.",
    WebhookEventAsyncType.FULFILLMENT_CREATED: "A new fulfillment is created.",
    WebhookEventAsyncType.FULFILLMENT_CANCELED: "A fulfillment is cancelled.",
    WebhookEventAsyncType.FULFILLMENT_APPROVED: "A fulfillment is approved.",
    WebhookEventAsyncType.FULFILLMENT_METADATA_UPDATED: (
        "A fulfillment metadata is updated."
    ),
    WebhookEventAsyncType.PAGE_CREATED: "A new page is created.",
    WebhookEventAsyncType.PAGE_UPDATED: "A page is updated.",
    WebhookEventAsyncType.PAGE_DELETED: "A page is deleted.",
    WebhookEventAsyncType.PAGE_TYPE_CREATED: "A new page type is created.",
    WebhookEventAsyncType.PAGE_TYPE_UPDATED: "A page type is updated.",
    WebhookEventAsyncType.PAGE_TYPE_DELETED: "A page type is deleted.",
    WebhookEventAsyncType.PERMISSION_GROUP_CREATED: (
        "A new permission group is created."
    ),
    WebhookEventAsyncType.PERMISSION_GROUP_UPDATED: "A permission group is updated.",
    WebhookEventAsyncType.PERMISSION_GROUP_DELETED: "A permission group is deleted.",
    WebhookEventAsyncType.PRODUCT_CREATED: "A new product is created.",
    WebhookEventAsyncType.PRODUCT_UPDATED: "A product is updated.",
    WebhookEventAsyncType.PRODUCT_DELETED: "A product is deleted.",
    WebhookEventAsyncType.PRODUCT_METADATA_UPDATED: ("A product metadata is updated."),
    WebhookEventAsyncType.PRODUCT_MEDIA_CREATED: "A new product media is created.",
    WebhookEventAsyncType.PRODUCT_MEDIA_UPDATED: "A product media is updated.",
    WebhookEventAsyncType.PRODUCT_MEDIA_DELETED: "A product media is deleted.",
    WebhookEventAsyncType.PRODUCT_VARIANT_CREATED: "A new product variant is created.",
    WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED: "A product variant is updated.",
    WebhookEventAsyncType.PRODUCT_VARIANT_DELETED: "A product variant is deleted. Warning: this event will not be executed when parent product has been deleted. Check PRODUCT_DELETED.",
    WebhookEventAsyncType.PRODUCT_VARIANT_METADATA_UPDATED: (
        "A product variant metadata is updated."
    ),
    WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK: (
        "A product variant is out of stock."
    ),
    WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK: (
        "A product variant is back in stock."
    ),
    WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED: (
        "A product variant stock is updated"
    ),
    WebhookEventAsyncType.PRODUCT_EXPORT_COMPLETED: ("A product export is completed."),
    WebhookEventAsyncType.SHIPPING_PRICE_CREATED: "A new shipping price is created.",
    WebhookEventAsyncType.SHIPPING_PRICE_UPDATED: "A shipping price is updated.",
    WebhookEventAsyncType.SHIPPING_PRICE_DELETED: "A shipping price is deleted.",
    WebhookEventAsyncType.SHIPPING_ZONE_CREATED: "A new shipping zone is created.",
    WebhookEventAsyncType.SHIPPING_ZONE_UPDATED: "A shipping zone is updated.",
    WebhookEventAsyncType.SHIPPING_ZONE_DELETED: "A shipping zone is deleted.",
    WebhookEventAsyncType.SHIPPING_ZONE_METADATA_UPDATED: (
        "A shipping zone metadata is updated."
    ),
    WebhookEventAsyncType.STAFF_SET_PASSWORD_REQUESTED: (
        "Setting a new password for the staff account is requested."
    ),
    WebhookEventAsyncType.STAFF_CREATED: "A new staff user is created.",
    WebhookEventAsyncType.STAFF_UPDATED: "A staff user is updated.",
    WebhookEventAsyncType.STAFF_DELETED: "A staff user is deleted.",
    WebhookEventAsyncType.TRANSACTION_ITEM_METADATA_UPDATED: (
        "Transaction item metadata is updated."
    ),
    WebhookEventAsyncType.TRANSLATION_CREATED: "A new translation is created.",
    WebhookEventAsyncType.TRANSLATION_UPDATED: "A translation is updated.",
    WebhookEventAsyncType.WAREHOUSE_CREATED: "A new warehouse created.",
    WebhookEventAsyncType.WAREHOUSE_UPDATED: "A warehouse is updated.",
    WebhookEventAsyncType.WAREHOUSE_DELETED: "A warehouse is deleted.",
    WebhookEventAsyncType.WAREHOUSE_METADATA_UPDATED: (
        "A warehouse metadata is updated."
    ),
    WebhookEventAsyncType.VOUCHER_CREATED: "A new voucher created.",
    WebhookEventAsyncType.VOUCHER_UPDATED: "A voucher is updated.",
    WebhookEventAsyncType.VOUCHER_DELETED: "A voucher is deleted.",
    WebhookEventAsyncType.VOUCHER_METADATA_UPDATED: ("A voucher metadata is updated."),
    WebhookEventAsyncType.VOUCHER_CODE_EXPORT_COMPLETED: (
        "A voucher code export is completed." + ADDED_IN_318
    ),
    WebhookEventAsyncType.ANY: "All the events.",
    WebhookEventAsyncType.OBSERVABILITY: "An observability event is created.",
    WebhookEventAsyncType.THUMBNAIL_CREATED: "A thumbnail is created.",
    WebhookEventAsyncType.SHOP_METADATA_UPDATED: "Shop metadata is updated.",
    WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT: (
        "Fetch external shipping methods for checkout."
    ),
    WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS: (
        "Filter shipping methods for checkout."
    ),
    WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS: (
        "Filter shipping methods for order."
    ),
    WebhookEventSyncType.PAYMENT_LIST_GATEWAYS: "Listing available payment gateways.",
    WebhookEventSyncType.PAYMENT_AUTHORIZE: "Authorize payment.",
    WebhookEventSyncType.PAYMENT_CAPTURE: "Capture payment.",
    WebhookEventSyncType.PAYMENT_REFUND: "Refund payment.",
    WebhookEventSyncType.PAYMENT_VOID: "Void payment.",
    WebhookEventSyncType.PAYMENT_CONFIRM: "Confirm payment.",
    WebhookEventSyncType.PAYMENT_PROCESS: "Process payment.",
    WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES: (
        "Event called for checkout tax calculation."
    ),
    WebhookEventSyncType.ORDER_CALCULATE_TAXES: (
        "Event called for order tax calculation."
    ),
    WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED: (
        "Event called when charge has been requested for transaction."
    ),
    WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED: (
        "Event called when refund has been requested for transaction."
    ),
    WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED: (
        "Event called when cancel has been requested for transaction."
    ),
}


def description(enum):
    if enum:
        return WEBHOOK_EVENT_DESCRIPTION.get(enum.value)
    return "Enum determining type of webhook."


def deprecation_reason(enum):
    if enum.value == WebhookEventAsyncType.NOTIFY_USER:
        return (
            "See the docs for more details about migrating from NOTIFY_USER to other events: "
            "https://docs.saleor.io/docs/next/upgrade-guides/notify-user-deprecation"
        )
    if enum.value == WebhookEventAsyncType.ANY:
        return DEFAULT_DEPRECATION_REASON
    return None


WebhookEventTypeEnum = graphene.Enum(
    "WebhookEventTypeEnum",
    [
        (str_to_enum(e_type[0]), e_type[0])
        for e_type in (WebhookEventAsyncType.CHOICES + WebhookEventSyncType.CHOICES)
    ],
    description=description,
    deprecation_reason=deprecation_reason,
)
WebhookEventTypeEnum.doc_category = DOC_CATEGORY_WEBHOOKS


WebhookEventTypeAsyncEnum = graphene.Enum(
    "WebhookEventTypeAsyncEnum",
    [(str_to_enum(e_type[0]), e_type[0]) for e_type in WebhookEventAsyncType.CHOICES],
    description=description,
    deprecation_reason=deprecation_reason,
)
WebhookEventTypeAsyncEnum.doc_category = DOC_CATEGORY_WEBHOOKS

WebhookEventTypeSyncEnum = graphene.Enum(
    "WebhookEventTypeSyncEnum",
    [(str_to_enum(e_type[0]), e_type[0]) for e_type in WebhookEventSyncType.CHOICES],
    description=description,
    deprecation_reason=deprecation_reason,
)
WebhookEventTypeSyncEnum.doc_category = DOC_CATEGORY_WEBHOOKS

WebhookSampleEventTypeEnum = graphene.Enum(
    "WebhookSampleEventTypeEnum",
    [
        (str_to_enum(e_type[0]), e_type[0])
        for e_type in WebhookEventAsyncType.CHOICES
        if e_type[0] != WebhookEventAsyncType.ANY
    ],
)
WebhookSampleEventTypeEnum.doc_category = DOC_CATEGORY_WEBHOOKS


class EventDeliveryStatusEnum(BaseEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS

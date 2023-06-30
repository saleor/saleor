import pytest

from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.models import Webhook
from . import subscription_queries as queries


@pytest.fixture
def subscription_webhook(webhook_app):
    def fun(query, event_type, name="Subscription"):
        webhook = Webhook.objects.create(
            name=name,
            app=webhook_app,
            target_url="http://www.example.com/any",
            subscription_query=query,
        )
        webhook.events.create(event_type=event_type)
        return webhook

    return fun


@pytest.fixture
def subscription_account_confirmation_requested_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ACCOUNT_CONFIRMATION_REQUESTED,
        WebhookEventAsyncType.ACCOUNT_CONFIRMATION_REQUESTED,
    )


@pytest.fixture
def subscription_account_change_email_requested_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ACCOUNT_CHANGE_EMAIL_REQUESTED,
        WebhookEventAsyncType.ACCOUNT_CHANGE_EMAIL_REQUESTED,
    )


@pytest.fixture
def subscription_account_delete_requested_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ACCOUNT_DELETE_REQUESTED,
        WebhookEventAsyncType.ACCOUNT_DELETE_REQUESTED,
    )


@pytest.fixture
def subscription_address_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ADDRESS_CREATED, WebhookEventAsyncType.ADDRESS_CREATED
    )


@pytest.fixture
def subscription_address_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ADDRESS_UPDATED, WebhookEventAsyncType.ADDRESS_UPDATED
    )


@pytest.fixture
def subscription_address_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ADDRESS_DELETED, WebhookEventAsyncType.ADDRESS_DELETED
    )


@pytest.fixture
def subscription_app_installed_webhook(subscription_webhook):
    return subscription_webhook(
        queries.APP_INSTALLED, WebhookEventAsyncType.APP_INSTALLED
    )


@pytest.fixture
def subscription_app_updated_webhook(subscription_webhook):
    return subscription_webhook(queries.APP_UPDATED, WebhookEventAsyncType.APP_UPDATED)


@pytest.fixture
def subscription_app_deleted_webhook(subscription_webhook):
    return subscription_webhook(queries.APP_DELETED, WebhookEventAsyncType.APP_DELETED)


@pytest.fixture
def subscription_app_status_changed_webhook(subscription_webhook):
    return subscription_webhook(
        queries.APP_STATUS_CHANGED,
        WebhookEventAsyncType.APP_STATUS_CHANGED,
    )


@pytest.fixture
def subscription_attribute_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ATTRIBUTE_CREATED, WebhookEventAsyncType.ATTRIBUTE_CREATED
    )


@pytest.fixture
def subscription_attribute_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ATTRIBUTE_UPDATED, WebhookEventAsyncType.ATTRIBUTE_UPDATED
    )


@pytest.fixture
def subscription_attribute_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ATTRIBUTE_DELETED, WebhookEventAsyncType.ATTRIBUTE_DELETED
    )


@pytest.fixture
def subscription_attribute_value_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ATTRIBUTE_VALUE_CREATED,
        WebhookEventAsyncType.ATTRIBUTE_VALUE_CREATED,
    )


@pytest.fixture
def subscription_attribute_value_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ATTRIBUTE_VALUE_UPDATED,
        WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED,
    )


@pytest.fixture
def subscription_attribute_value_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ATTRIBUTE_VALUE_DELETED,
        WebhookEventAsyncType.ATTRIBUTE_VALUE_DELETED,
    )


@pytest.fixture
def subscription_category_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CATEGORY_CREATED, WebhookEventAsyncType.CATEGORY_CREATED
    )


@pytest.fixture
def subscription_category_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CATEGORY_UPDATED, WebhookEventAsyncType.CATEGORY_UPDATED
    )


@pytest.fixture
def subscription_category_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CATEGORY_DELETED, WebhookEventAsyncType.CATEGORY_DELETED
    )


@pytest.fixture
def subscription_channel_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CHANNEL_CREATED, WebhookEventAsyncType.CHANNEL_CREATED
    )


@pytest.fixture
def subscription_channel_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CHANNEL_UPDATED, WebhookEventAsyncType.CHANNEL_UPDATED
    )


@pytest.fixture
def subscription_channel_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CHANNEL_DELETED, WebhookEventAsyncType.CHANNEL_DELETED
    )


@pytest.fixture
def subscription_channel_status_changed_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CHANNEL_STATUS_CHANGED,
        WebhookEventAsyncType.CHANNEL_STATUS_CHANGED,
    )


@pytest.fixture
def subscription_gift_card_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.GIFT_CARD_CREATED, WebhookEventAsyncType.GIFT_CARD_CREATED
    )


@pytest.fixture
def subscription_gift_card_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.GIFT_CARD_UPDATED, WebhookEventAsyncType.GIFT_CARD_UPDATED
    )


@pytest.fixture
def subscription_gift_card_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.GIFT_CARD_DELETED, WebhookEventAsyncType.GIFT_CARD_DELETED
    )


@pytest.fixture
def subscription_gift_card_sent_webhook(subscription_webhook):
    return subscription_webhook(
        queries.GIFT_CARD_SENT, WebhookEventAsyncType.GIFT_CARD_SENT
    )


@pytest.fixture
def subscription_gift_card_status_changed_webhook(subscription_webhook):
    return subscription_webhook(
        queries.GIFT_CARD_STATUS_CHANGED,
        WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED,
    )


@pytest.fixture
def subscription_gift_card_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.GIFT_CARD_METADATA_UPDATED,
        WebhookEventAsyncType.GIFT_CARD_METADATA_UPDATED,
    )


@pytest.fixture
def subscription_menu_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.MENU_CREATED, WebhookEventAsyncType.MENU_CREATED
    )


@pytest.fixture
def subscription_menu_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.MENU_UPDATED, WebhookEventAsyncType.MENU_UPDATED
    )


@pytest.fixture
def subscription_menu_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.MENU_DELETED, WebhookEventAsyncType.MENU_DELETED
    )


@pytest.fixture
def subscription_menu_item_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.MENU_ITEM_CREATED, WebhookEventAsyncType.MENU_ITEM_CREATED
    )


@pytest.fixture
def subscription_menu_item_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.MENU_ITEM_UPDATED, WebhookEventAsyncType.MENU_ITEM_UPDATED
    )


@pytest.fixture
def subscription_menu_item_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.MENU_ITEM_DELETED, WebhookEventAsyncType.MENU_ITEM_DELETED
    )


@pytest.fixture
def subscription_shipping_price_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SHIPPING_PRICE_CREATED,
        WebhookEventAsyncType.SHIPPING_PRICE_CREATED,
    )


@pytest.fixture
def subscription_shipping_price_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SHIPPING_PRICE_UPDATED_UPDATED,
        WebhookEventAsyncType.SHIPPING_PRICE_UPDATED,
    )


@pytest.fixture
def subscription_shipping_price_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SHIPPING_PRICE_DELETED,
        WebhookEventAsyncType.SHIPPING_PRICE_DELETED,
    )


@pytest.fixture
def subscription_shipping_zone_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SHIPPING_ZONE_CREATED,
        WebhookEventAsyncType.SHIPPING_ZONE_CREATED,
    )


@pytest.fixture
def subscription_shipping_zone_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SHIPPING_ZONE_UPDATED_UPDATED,
        WebhookEventAsyncType.SHIPPING_ZONE_UPDATED,
    )


@pytest.fixture
def subscription_shipping_zone_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SHIPPING_ZONE_DELETED,
        WebhookEventAsyncType.SHIPPING_ZONE_DELETED,
    )


@pytest.fixture
def subscription_shipping_zone_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SHIPPING_ZONE_METADATA_UPDATED,
        WebhookEventAsyncType.SHIPPING_ZONE_METADATA_UPDATED,
    )


@pytest.fixture
def subscription_product_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_UPDATED, WebhookEventAsyncType.PRODUCT_UPDATED
    )


@pytest.fixture
def subscription_product_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_CREATED, WebhookEventAsyncType.PRODUCT_CREATED
    )


@pytest.fixture
def subscription_product_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_DELETED, WebhookEventAsyncType.PRODUCT_DELETED
    )


@pytest.fixture
def subscription_product_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_METADATA_UPDATED, WebhookEventAsyncType.PRODUCT_METADATA_UPDATED
    )


@pytest.fixture
def subscription_product_media_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_MEDIA_CREATED, WebhookEventAsyncType.PRODUCT_CREATED
    )


@pytest.fixture
def subscription_product_media_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_MEDIA_UPDATED, WebhookEventAsyncType.PRODUCT_UPDATED
    )


@pytest.fixture
def subscription_product_media_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_MEDIA_DELETED, WebhookEventAsyncType.PRODUCT_DELETED
    )


@pytest.fixture
def subscription_product_variant_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_VARIANT_CREATED,
        WebhookEventAsyncType.PRODUCT_VARIANT_CREATED,
    )


@pytest.fixture
def subscription_product_variant_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_VARIANT_UPDATED,
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
    )


@pytest.fixture
def subscription_product_variant_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_VARIANT_DELETED,
        WebhookEventAsyncType.PRODUCT_VARIANT_DELETED,
    )


@pytest.fixture
def subscription_product_variant_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_VARIANT_METADATA_UPDATED,
        WebhookEventAsyncType.PRODUCT_VARIANT_METADATA_UPDATED,
    )


@pytest.fixture
def subscription_product_variant_out_of_stock_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_VARIANT_OUT_OF_STOCK,
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK,
    )


@pytest.fixture
def subscription_product_variant_back_in_stock_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_VARIANT_BACK_IN_STOCK,
        WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK,
    )


@pytest.fixture
def subscription_product_variant_stock_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PRODUCT_VARIANT_STOCK_UPDATED,
        WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED,
    )


@pytest.fixture
def subscription_order_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_CREATED, WebhookEventAsyncType.ORDER_CREATED
    )


@pytest.fixture
def subscription_order_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_UPDATED, WebhookEventAsyncType.ORDER_UPDATED
    )


@pytest.fixture
def subscription_order_confirmed_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_CONFIRMED, WebhookEventAsyncType.ORDER_CONFIRMED
    )


@pytest.fixture
def subscription_order_fully_paid_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_FULLY_PAID, WebhookEventAsyncType.ORDER_FULLY_PAID
    )


@pytest.fixture
def subscription_order_paid_webhook(subscription_webhook):
    return subscription_webhook(queries.ORDER_PAID, WebhookEventAsyncType.ORDER_PAID)


@pytest.fixture
def subscription_order_fully_refunded_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_FULLY_REFUNDED, WebhookEventAsyncType.ORDER_FULLY_REFUNDED
    )


@pytest.fixture
def subscription_order_refunded_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_REFUNDED, WebhookEventAsyncType.ORDER_REFUNDED
    )


@pytest.fixture
def subscription_order_cancelled_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_CANCELLED, WebhookEventAsyncType.ORDER_CANCELLED
    )


@pytest.fixture
def subscription_order_expired_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_EXPIRED, WebhookEventAsyncType.ORDER_EXPIRED
    )


@pytest.fixture
def subscription_order_fulfilled_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_FULFILLED, WebhookEventAsyncType.ORDER_FULFILLED
    )


@pytest.fixture
def subscription_order_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_METADATA_UPDATED, WebhookEventAsyncType.ORDER_METADATA_UPDATED
    )


@pytest.fixture
def subscription_order_bulk_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_BULK_CREATED, WebhookEventAsyncType.ORDER_BULK_CREATED
    )


@pytest.fixture
def subscription_draft_order_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.DRAFT_ORDER_CREATED,
        WebhookEventAsyncType.DRAFT_ORDER_CREATED,
    )


@pytest.fixture
def subscription_draft_order_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.DRAFT_ORDER_UPDATED,
        WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
    )


@pytest.fixture
def subscription_draft_order_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.DRAFT_ORDER_DELETED,
        WebhookEventAsyncType.DRAFT_ORDER_DELETED,
    )


@pytest.fixture
def subscription_sale_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SALE_CREATED, WebhookEventAsyncType.SALE_CREATED
    )


@pytest.fixture
def subscription_sale_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SALE_UPDATED, WebhookEventAsyncType.SALE_UPDATED
    )


@pytest.fixture
def subscription_sale_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SALE_DELETED, WebhookEventAsyncType.SALE_DELETED
    )


@pytest.fixture
def subscription_sale_toggle_webhook(subscription_webhook):
    return subscription_webhook(queries.SALE_TOGGLE, WebhookEventAsyncType.SALE_TOGGLE)


@pytest.fixture
def subscription_invoice_requested_webhook(subscription_webhook):
    return subscription_webhook(
        queries.INVOICE_REQUESTED, WebhookEventAsyncType.INVOICE_REQUESTED
    )


@pytest.fixture
def subscription_invoice_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.INVOICE_DELETED, WebhookEventAsyncType.INVOICE_DELETED
    )


@pytest.fixture
def subscription_invoice_sent_webhook(subscription_webhook):
    return subscription_webhook(
        queries.INVOICE_SENT, WebhookEventAsyncType.INVOICE_SENT
    )


@pytest.fixture
def subscription_fulfillment_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.FULFILLMENT_CREATED,
        WebhookEventAsyncType.FULFILLMENT_CREATED,
    )


@pytest.fixture
def subscription_fulfillment_canceled_webhook(subscription_webhook):
    return subscription_webhook(
        queries.FULFILLMENT_CANCELED,
        WebhookEventAsyncType.FULFILLMENT_CANCELED,
    )


@pytest.fixture
def subscription_fulfillment_approved_webhook(subscription_webhook):
    return subscription_webhook(
        queries.FULFILLMENT_APPROVED,
        WebhookEventAsyncType.FULFILLMENT_APPROVED,
    )


@pytest.fixture
def subscription_fulfillment_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.FULFILLMENT_METADATA_UPDATED,
        WebhookEventAsyncType.FULFILLMENT_METADATA_UPDATED,
    )


@pytest.fixture
def subscription_customer_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CUSTOMER_CREATED, WebhookEventAsyncType.CUSTOMER_CREATED
    )


@pytest.fixture
def subscription_customer_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CUSTOMER_UPDATED, WebhookEventAsyncType.CUSTOMER_UPDATED
    )


@pytest.fixture
def subscription_customer_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CUSTOMER_DELETED, WebhookEventAsyncType.CUSTOMER_DELETED
    )


@pytest.fixture
def subscription_customer_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CUSTOMER_METADATA_UPDATED,
        WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED,
    )


@pytest.fixture
def subscription_collection_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.COLLECTION_CREATED,
        WebhookEventAsyncType.COLLECTION_CREATED,
    )


@pytest.fixture
def subscription_collection_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.COLLECTION_UPDATED,
        WebhookEventAsyncType.COLLECTION_UPDATED,
    )


@pytest.fixture
def subscription_collection_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.COLLECTION_DELETED,
        WebhookEventAsyncType.COLLECTION_DELETED,
    )


@pytest.fixture
def subscription_collection_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.COLLECTION_METADATA_UPDATED,
        WebhookEventAsyncType.COLLECTION_METADATA_UPDATED,
    )


@pytest.fixture
def subscription_checkout_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CHECKOUT_CREATED, WebhookEventAsyncType.CHECKOUT_CREATED
    )


@pytest.fixture
def subscription_checkout_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CHECKOUT_UPDATED, WebhookEventAsyncType.CHECKOUT_UPDATED
    )


@pytest.fixture
def subscription_checkout_fully_paid_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CHECKOUT_FULLY_PAID, WebhookEventAsyncType.CHECKOUT_FULLY_PAID
    )


@pytest.fixture
def subscription_checkout_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CHECKOUT_METADATA_UPDATED,
        WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED,
    )


@pytest.fixture
def subscription_page_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAGE_CREATED, WebhookEventAsyncType.PAGE_CREATED
    )


@pytest.fixture
def subscription_page_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAGE_UPDATED,
        WebhookEventAsyncType.PAGE_UPDATED,
    )


@pytest.fixture
def subscription_page_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAGE_DELETED,
        WebhookEventAsyncType.PAGE_DELETED,
    )


@pytest.fixture
def subscription_page_type_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAGE_TYPE_CREATED, WebhookEventAsyncType.PAGE_TYPE_CREATED
    )


@pytest.fixture
def subscription_page_type_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAGE_TYPE_UPDATED, WebhookEventAsyncType.PAGE_TYPE_UPDATED
    )


@pytest.fixture
def subscription_page_type_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAGE_TYPE_DELETED, WebhookEventAsyncType.PAGE_TYPE_DELETED
    )


@pytest.fixture
def subscription_permission_group_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PERMISSION_GROUP_CREATED,
        WebhookEventAsyncType.PERMISSION_GROUP_CREATED,
    )


@pytest.fixture
def subscription_permission_group_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PERMISSION_GROUP_UPDATED,
        WebhookEventAsyncType.PERMISSION_GROUP_UPDATED,
    )


@pytest.fixture
def subscription_permission_group_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PERMISSION_GROUP_DELETED,
        WebhookEventAsyncType.PERMISSION_GROUP_DELETED,
    )


@pytest.fixture
def subscription_product_created_multiple_events_webhook(subscription_webhook):
    return subscription_webhook(
        queries.MULTIPLE_EVENTS,
        WebhookEventAsyncType.TRANSLATION_CREATED,
    )


@pytest.fixture
def subscription_staff_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.STAFF_CREATED, WebhookEventAsyncType.STAFF_CREATED
    )


@pytest.fixture
def subscription_staff_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.STAFF_UPDATED,
        WebhookEventAsyncType.STAFF_UPDATED,
    )


@pytest.fixture
def subscription_staff_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.STAFF_DELETED,
        WebhookEventAsyncType.STAFF_DELETED,
    )


@pytest.fixture
def subscription_transaction_item_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.TRANSACTION_ITEM_METADATA_UPDATED,
        WebhookEventAsyncType.TRANSACTION_ITEM_METADATA_UPDATED,
    )


@pytest.fixture
def subscription_translation_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.TRANSLATION_CREATED,
        WebhookEventAsyncType.TRANSLATION_CREATED,
    )


@pytest.fixture
def subscription_translation_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.TRANSLATION_UPDATED,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
    )


@pytest.fixture
def subscription_warehouse_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.WAREHOUSE_CREATED, WebhookEventAsyncType.WAREHOUSE_CREATED
    )


@pytest.fixture
def subscription_warehouse_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.WAREHOUSE_UPDATED, WebhookEventAsyncType.WAREHOUSE_UPDATED
    )


@pytest.fixture
def subscription_warehouse_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.WAREHOUSE_DELETED, WebhookEventAsyncType.WAREHOUSE_DELETED
    )


@pytest.fixture
def subscription_warehouse_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.WAREHOUSE_METADATA_UPDATED,
        WebhookEventAsyncType.WAREHOUSE_METADATA_UPDATED,
    )


@pytest.fixture
def subscription_voucher_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.VOUCHER_CREATED, WebhookEventAsyncType.VOUCHER_CREATED
    )


@pytest.fixture
def subscription_voucher_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.VOUCHER_UPDATED, WebhookEventAsyncType.VOUCHER_UPDATED
    )


@pytest.fixture
def subscription_voucher_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        queries.VOUCHER_DELETED, WebhookEventAsyncType.VOUCHER_DELETED
    )


@pytest.fixture
def subscription_voucher_webhook_with_meta(subscription_webhook):
    return subscription_webhook(
        queries.VOUCHER_CREATED_WITH_META,
        WebhookEventAsyncType.VOUCHER_CREATED,
    )


@pytest.fixture
def subscription_voucher_metadata_updated_webhook(subscription_webhook):
    return subscription_webhook(
        queries.VOUCHER_METADATA_UPDATED, WebhookEventAsyncType.VOUCHER_METADATA_UPDATED
    )


@pytest.fixture
def subscription_payment_authorize_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAYMENT_AUTHORIZE, WebhookEventSyncType.PAYMENT_AUTHORIZE
    )


@pytest.fixture
def subscription_payment_capture_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAYMENT_CAPTURE, WebhookEventSyncType.PAYMENT_CAPTURE
    )


@pytest.fixture
def subscription_payment_refund_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAYMENT_REFUND, WebhookEventSyncType.PAYMENT_REFUND
    )


@pytest.fixture
def subscription_payment_void_webhook(subscription_webhook):
    return subscription_webhook(queries.PAYMENT_VOID, WebhookEventSyncType.PAYMENT_VOID)


@pytest.fixture
def subscription_payment_confirm_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAYMENT_CONFIRM, WebhookEventSyncType.PAYMENT_CONFIRM
    )


@pytest.fixture
def subscription_payment_process_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAYMENT_PROCESS, WebhookEventSyncType.PAYMENT_PROCESS
    )


@pytest.fixture
def subscription_payment_list_gateways_webhook(subscription_webhook):
    return subscription_webhook(
        queries.PAYMENT_LIST_GATEWAYS,
        WebhookEventSyncType.PAYMENT_LIST_GATEWAYS,
    )


@pytest.fixture
def subscription_checkout_filter_shipping_methods_webhook(subscription_webhook):
    return subscription_webhook(
        queries.CHECKOUT_FILTER_SHIPPING_METHODS,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_shipping_list_methods_for_checkout_webhook(subscription_webhook):
    return subscription_webhook(
        queries.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )


@pytest.fixture
def subscription_order_filter_shipping_methods_webhook(subscription_webhook):
    return subscription_webhook(
        queries.ORDER_FILTER_SHIPPING_METHODS,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_checkout_filter_shipping_method_webhook_with_shipping_methods(
    subscription_webhook,
):
    return subscription_webhook(
        queries.CHECKOUT_FILTER_SHIPPING_METHODS_CIRCULAR_SHIPPING_METHODS,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_checkout_filter_shipping_method_webhook_with_available_ship_methods(
    subscription_webhook,
):
    return subscription_webhook(
        queries.CHECKOUT_FILTER_SHIPPING_METHODS_AVAILABLE_SHIPPING_METHODS,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_checkout_filter_shipping_method_webhook_with_payment_gateways(
    subscription_webhook,
):
    return subscription_webhook(
        queries.CHECKOUT_FILTER_SHIPPING_METHODS_AVAILABLE_PAYMENT_GATEWAYS,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_order_filter_shipping_methods_webhook_with_shipping_methods(
    subscription_webhook,
):
    return subscription_webhook(
        queries.ORDER_FILTER_SHIPPING_METHODS_CIRCULAR_SHIPPING_METHODS,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_order_filter_shipping_methods_webhook_with_available_ship_methods(
    subscription_webhook,
):
    return subscription_webhook(
        queries.ORDER_FILTER_SHIPPING_METHODS_AVAILABLE_SHIPPING_METHODS,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_thumbnail_created_webhook(subscription_webhook):
    return subscription_webhook(
        queries.THUMBNAIL_CREATED,
        WebhookEventAsyncType.THUMBNAIL_CREATED,
    )


@pytest.fixture
def subscription_calculate_taxes_for_order(
    subscription_webhook,
):
    return subscription_webhook(
        queries.ORDER_CALCULATE_TAXES,
        WebhookEventSyncType.ORDER_CALCULATE_TAXES,
    )

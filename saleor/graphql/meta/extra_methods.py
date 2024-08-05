from ...checkout.actions import call_checkout_event_for_checkout_info
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...core.utils.events import webhook_async_event_requires_sync_webhooks_to_trigger
from ...order.actions import call_order_event
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...webhook.utils import get_webhooks_for_multiple_events
from ..core import ResolveInfo
from ..plugins.dataloaders import get_plugin_manager_promise


def extra_checkout_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    webhook_event_map = get_webhooks_for_multiple_events(
        [
            WebhookEventAsyncType.CHECKOUT_UPDATED,
            WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED,
            *WebhookEventSyncType.CHECKOUT_EVENTS,
        ]
    )
    # In case of having any active combination of async/sync webhooks for these events
    # we need to fetch checkout lines and checkout info to call sync webhook first.
    if webhook_async_event_requires_sync_webhooks_to_trigger(
        WebhookEventAsyncType.CHECKOUT_UPDATED,
        webhook_event_map,
        possible_sync_events=WebhookEventSyncType.CHECKOUT_EVENTS,
    ) or webhook_async_event_requires_sync_webhooks_to_trigger(
        WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED,
        webhook_event_map,
        possible_sync_events=WebhookEventSyncType.CHECKOUT_EVENTS,
    ):
        lines_info, _ = fetch_checkout_lines(
            instance,
        )
        checkout_info = fetch_checkout_info(
            instance,
            lines_info,
            manager,
        )
        call_checkout_event_for_checkout_info(
            manager=manager,
            event_func=manager.checkout_updated,
            event_name=WebhookEventAsyncType.CHECKOUT_UPDATED,
            checkout_info=checkout_info,
            lines=lines_info,
            webhook_event_map=webhook_event_map,
        )
        call_checkout_event_for_checkout_info(
            manager=manager,
            event_func=manager.checkout_metadata_updated,
            event_name=WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED,
            checkout_info=checkout_info,
            lines=lines_info,
            webhook_event_map=webhook_event_map,
        )
    else:
        manager.checkout_updated(instance)
        manager.checkout_metadata_updated(instance)


def extra_channel_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.channel_metadata_updated(instance)


def extra_collection_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.collection_metadata_updated(instance)


def extra_fulfillment_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.fulfillment_metadata_updated(instance)


def extra_gift_card_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.gift_card_metadata_updated(instance)


def extra_order_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    call_order_event(
        manager,
        manager.order_metadata_updated,
        WebhookEventAsyncType.ORDER_METADATA_UPDATED,
        instance,
    )


def extra_product_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.product_updated(instance)
    manager.product_metadata_updated(instance)


def extra_variant_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.product_variant_updated(instance)
    manager.product_variant_metadata_updated(instance)


def extra_shipping_zone_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.shipping_zone_metadata_updated(instance)


def extra_transaction_item_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.transaction_item_metadata_updated(instance)


def extra_user_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.customer_updated(instance)
    manager.customer_metadata_updated(instance)


def extra_warehouse_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.warehouse_metadata_updated(instance)


def extra_voucher_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.voucher_metadata_updated(instance)


def extra_shop_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()
    manager.shop_metadata_updated(instance)


TYPE_EXTRA_METHODS = {
    "Checkout": extra_checkout_actions,
    "Collection": extra_collection_actions,
    "Fulfillment": extra_fulfillment_actions,
    "GiftCard": extra_gift_card_actions,
    "Channel": extra_channel_actions,
    "Order": extra_order_actions,
    "Product": extra_product_actions,
    "ProductVariant": extra_variant_actions,
    "ShippingZone": extra_shipping_zone_actions,
    "Shop": extra_shop_actions,
    "TransactionItem": extra_transaction_item_actions,
    "User": extra_user_actions,
    "Warehouse": extra_warehouse_actions,
    "Voucher": extra_voucher_actions,
}

from ...checkout.actions import call_checkout_events
from ...order.actions import call_order_event
from ...webhook.event_types import WebhookEventAsyncType
from ..core import ResolveInfo
from ..plugins.dataloaders import get_plugin_manager_promise


def extra_checkout_actions(instance, info: ResolveInfo, **data):
    manager = get_plugin_manager_promise(info.context).get()

    call_checkout_events(
        manager=manager,
        event_names=[
            WebhookEventAsyncType.CHECKOUT_UPDATED,
            WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED,
        ],
        checkout=instance,
    )


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

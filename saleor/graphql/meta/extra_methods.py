from ...product.models import Product, ProductVariant
from ..plugins.dataloaders import load_plugin_manager


def extra_checkout_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.checkout_updated(instance)
    manager.checkout_metadata_updated(instance)


def extra_collection_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.collection_metadata_updated(instance)


def extra_fulfillment_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.fulfillment_metadata_updated(instance)


def extra_gift_card_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.gift_card_metadata_updated(instance)


def extra_order_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.order_metadata_updated(instance)


def extra_product_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.product_updated(instance)
    manager.product_metadata_updated(instance)


def extra_variant_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.product_variant_updated(instance)
    manager.product_variant_metadata_updated(instance)


def extra_shipping_zone_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.shipping_zone_metadata_updated(instance)


def extra_transaction_item_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.transaction_item_metadata_updated(instance)


def extra_user_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.customer_updated(instance)
    manager.customer_metadata_updated(instance)


def extra_warehouse_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.warehouse_metadata_updated(instance)


def extra_voucher_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.voucher_metadata_updated(instance)


MODEL_EXTRA_METHODS = {
    "Checkout": extra_checkout_actions,
    "Collection": extra_collection_actions,
    "Fulfillment": extra_fulfillment_actions,
    "GiftCard": extra_gift_card_actions,
    "Order": extra_order_actions,
    "Product": extra_product_actions,
    "ProductVariant": extra_variant_actions,
    "ShippingZone": extra_shipping_zone_actions,
    "TransactionItem": extra_transaction_item_actions,
    "User": extra_user_actions,
    "Warehouse": extra_warehouse_actions,
    "Voucher": extra_voucher_actions,
}


MODEL_EXTRA_PREFETCH = {
    "Product": Product.objects.prefetched_for_webhook,
    "ProductVariant": ProductVariant.objects.prefetched_for_webhook,
}

from ...product.models import Product, ProductVariant
from ..plugins.dataloaders import load_plugin_manager


def extra_checkout_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.checkout_updated(instance)


def extra_product_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.product_updated(instance)


def extra_variant_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.product_variant_updated(instance)


def extra_user_actions(instance, info, **data):
    manager = load_plugin_manager(info.context)
    manager.customer_updated(instance)


MODEL_EXTRA_METHODS = {
    "Checkout": extra_checkout_actions,
    "Product": extra_product_actions,
    "ProductVariant": extra_variant_actions,
    "User": extra_user_actions,
}


MODEL_EXTRA_PREFETCH = {
    "Product": Product.objects.prefetched_for_webhook,
    "ProductVariant": ProductVariant.objects.prefetched_for_webhook,
}

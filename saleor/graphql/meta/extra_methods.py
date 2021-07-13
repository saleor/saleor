from ...product.models import Product, ProductVariant


def extra_checkout_actions(instance, info, **data):
    info.context.plugins.checkout_updated(instance)


def extra_product_actions(instance, info, **data):
    info.context.plugins.product_updated(instance)


def extra_variant_actions(instance, info, **data):
    info.context.plugins.product_variant_updated(instance)


def extra_user_actions(instance, info, **data):
    info.context.plugins.customer_updated(instance)


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

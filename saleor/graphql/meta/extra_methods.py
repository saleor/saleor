def extra_product_actions(instance, info, **data):
    info.context.plugins.product_updated(instance)


def extra_order_actions(instance, info, **data):
    info.context.plugins.order_updated(instance)


MODEL_EXTRA_METHODS = {"Product": extra_product_actions, "Order": extra_order_actions}

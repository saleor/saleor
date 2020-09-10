def extra_product_actions(instance, info, **data):
    info.context.plugins.product_updated(instance)


MODEL_EXTRA_METHODS = {"Product": extra_product_actions}

def extra_product_actions(instance, info, **data):
    info.context.plugins.product_updated(instance)


def extra_user_actions(instance, info, **data):
    info.context.plugins.customer_updated(instance)


MODEL_EXTRA_METHODS = {"Product": extra_product_actions, "User": extra_user_actions}

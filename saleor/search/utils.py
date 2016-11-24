from . import search_indexes


def update_product_index(instance):
    search_indexes.ProductIndex().update_object(instance)


def update_order_index(instance):
    search_indexes.OrderIndex().update_object(instance)


def update_user_index(instance):
    search_indexes.UserIndex().update_object(instance)

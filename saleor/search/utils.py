from . import search_indexes


def update_product(instance):
    search_indexes.ProductIndex().update_object(instance)


def update_order(instance):
    search_indexes.OrderIndex().update_object(instance)


def update_user(instance):
    search_indexes.UserIndex().update_object(instance)

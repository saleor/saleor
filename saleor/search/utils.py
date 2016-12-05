import datetime

from . import search_indexes


def update_product_index(instance):
    search_indexes.ProductIndex().update_object(instance)


def update_order_index(instance):
    search_indexes.OrderIndex().update_object(instance)


def update_user_index(instance):
    search_indexes.UserIndex().update_object(instance)


def visible_search_results(results):
    today = datetime.date.today()
    return results.filter_or(available_on__lte=today)

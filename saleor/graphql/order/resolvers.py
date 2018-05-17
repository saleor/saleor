from ...order import models


def resolve_orders():
    return models.Order.objects.all().distinct()

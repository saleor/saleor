from django.core.exceptions import PermissionDenied

from ...order import models
from ..utils import get_node
from .types import Order


def resolve_orders(info):
    user = info.context.user
    if user.is_anonymous:
        raise PermissionDenied('You have no permission to see this')
    if user.get_all_permissions() & {'order.view_order', 'order.edit_order'}:
        return models.Order.objects.all().distinct()
    return models.Order.objects.filter(user=user).distinct()


def resolve_order(info, id):
    order = get_node(info, id, only_type=Order)
    user = info.context.user
    if (order.user == user
        or user.is_superuser
        or user.get_all_permissions() & {
            'order.view_order', 'order.edit_order'}):
        return order

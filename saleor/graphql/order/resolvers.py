from graphql_jwt.decorators import login_required

from ...order import models
from ..utils import get_node
from .types import Order


@login_required
def resolve_orders(info):
    user = info.context.user
    qs = user.orders.confirmed().distinct()
    if user.get_all_permissions() & {'order.view_order', 'order.edit_order'}:
        qs =  models.Order.objects.all().distinct()
    return qs.prefetch_related('lines')


@login_required
def resolve_order(info, id):
    """Return order only for user assigned to it or proper staff user."""
    order = get_node(info, id, only_type=Order)
    user = info.context.user
    if (order.user == user or user.get_all_permissions() & {
            'order.view_order', 'order.edit_order'}):
        return order

import graphene

from ...order import models
from ..utils import filter_by_query_param
from .types import Order

ORDER_SEARCH_FIELDS = (
    'id', 'discount_name', 'token', 'user_email', 'user__email')


def resolve_orders(info, query):
    user = info.context.user
    if user.has_perm('order.manage_orders'):
        qs = models.Order.objects.all()
    else:
        qs = user.orders.confirmed()
    qs = filter_by_query_param(qs, query, ORDER_SEARCH_FIELDS)
    return qs.prefetch_related('lines').distinct()


def resolve_order(info, id):
    """Return order only for user assigned to it or proper staff user."""
    user = info.context.user
    order = graphene.Node.get_node_from_global_id(info, id, Order)
    if user.has_perm('order.manage_orders') or order.user == user:
        return order
    return None

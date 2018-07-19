from graphql_jwt.decorators import login_required

from ...order import models
from ..utils import filter_by_query_param, get_node
from .types import Order

ORDER_SEARCH_FIELDS = (
    'id', 'discount_name', 'token', 'user_email', 'user__email')


@login_required
def resolve_orders(info, query):
    user = info.context.user
    queryset = user.orders.confirmed().distinct()
    if user.get_all_permissions() & {'order.manage_orders'}:
        queryset = models.Order.objects.all().distinct()
    queryset = filter_by_query_param(queryset, query, ORDER_SEARCH_FIELDS)
    return queryset.prefetch_related('lines')


@login_required
def resolve_order(info, id):
    """Return order only for user assigned to it or proper staff user."""
    order = get_node(info, id, only_type=Order)
    user = info.context.user
    if (order.user == user or user.get_all_permissions() & {
            'order.manage_orders'}):
        return order

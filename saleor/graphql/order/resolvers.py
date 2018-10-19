import graphene

from ...order import models
from ...shipping import models as shipping_models
from ..utils import filter_by_query_param
from .types import Order, OrderStatusFilter


ORDER_SEARCH_FIELDS = (
    'id', 'discount_name', 'token', 'user_email', 'user__email')


def resolve_orders(info, status, query):
    user = info.context.user
    if user.has_perm('order.manage_orders'):
        qs = models.Order.objects.all()
    else:
        qs = user.orders.confirmed()
    qs = filter_by_query_param(qs, query, ORDER_SEARCH_FIELDS)

    # filter orders by status
    if status is not None:
        if status == OrderStatusFilter.READY_TO_FULFILL:
            qs = qs.ready_to_fulfill()
        elif status == OrderStatusFilter.READY_TO_CAPTURE:
            qs = qs.ready_to_capture()
    return qs.prefetch_related('lines').distinct()


def resolve_order(info, id):
    """Return order only for user assigned to it or proper staff user."""
    user = info.context.user
    order = graphene.Node.get_node_from_global_id(info, id, Order)
    if user.has_perm('order.manage_orders') or order.user == user:
        return order
    return None


def resolve_shipping_methods(obj, info):
    if not obj.is_shipping_required():
        return None
    if not obj.shipping_address:
        return None

    qs = shipping_models.ShippingMethod.objects
    return qs.applicable_shipping_methods(
        price=obj.get_subtotal().gross.amount, weight=obj.get_total_weight(),
        country_code=obj.shipping_address.country.code)

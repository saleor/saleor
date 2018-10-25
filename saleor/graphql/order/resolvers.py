import graphene
import graphene_django_optimizer as gql_optimizer

from ...order import models, OrderStatus, OrderEvents
from ...order.utils import sum_order_totals
from ..utils import filter_by_query_param, filter_by_period
from .types import Order, OrderStatusFilter


ORDER_SEARCH_FIELDS = (
    'id', 'discount_name', 'token', 'user_email', 'user__email')


def resolve_orders(info, created, status, query):
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

    # filter orders by creation date
    if created is not None:
        qs = filter_by_period(qs, created, 'created')

    return gql_optimizer.query(qs, info)


def resolve_orders_total(info, period):
    qs = models.Order.objects.confirmed().exclude(status=OrderStatus.CANCELED)
    qs = filter_by_period(qs, period, 'created')
    return sum_order_totals(qs)


def resolve_order(info, id):
    """Return order only for user assigned to it or proper staff user."""
    user = info.context.user
    order = graphene.Node.get_node_from_global_id(info, id, Order)
    if user.has_perm('order.manage_orders') or order.user == user:
        return order
    return None


def resolve_homepage_events(info):
    # Filter only selected events to be displayed on homepage.
    types = [
        OrderEvents.PLACED.value, OrderEvents.PLACED_FROM_DRAFT.value,
        OrderEvents.ORDER_FULLY_PAID.value]
    return models.OrderEvent.objects.filter(type__in=types)

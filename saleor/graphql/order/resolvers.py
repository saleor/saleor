import graphene
import graphene_django_optimizer as gql_optimizer

from ...order import OrderEvents, OrderStatus, models
from ...order.utils import sum_order_totals
from ..utils import filter_by_period, filter_by_query_param
from .enums import OrderStatusFilter
from .types import Order
from .utils import applicable_shipping_methods

ORDER_SEARCH_FIELDS = (
    'id', 'discount_name', 'token', 'user_email', 'user__email')


def filter_orders(qs, info, created, status, query):
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


def resolve_orders(info, created, status, query):
    qs = models.Order.objects.confirmed()
    return filter_orders(qs, info, created, status, query)


def resolve_draft_orders(info, created, query):
    qs = models.Order.objects.drafts()
    return filter_orders(qs, info, created, None, query)


def resolve_orders_total(_info, period):
    qs = models.Order.objects.confirmed().exclude(status=OrderStatus.CANCELED)
    qs = filter_by_period(qs, period, 'created')
    return sum_order_totals(qs)


def resolve_order(info, order_id):
    """Return order only for user assigned to it or proper staff user."""
    user = info.context.user
    order = graphene.Node.get_node_from_global_id(info, order_id, Order)
    if user.has_perm('order.manage_orders') or order.user == user:
        return order
    return None


def resolve_homepage_events():
    # Filter only selected events to be displayed on homepage.
    types = [
        OrderEvents.PLACED.value, OrderEvents.PLACED_FROM_DRAFT.value,
        OrderEvents.ORDER_FULLY_PAID.value]
    return models.OrderEvent.objects.filter(type__in=types)


def resolve_order_by_token(token):
    return models.Order.objects.filter(token=token).first()

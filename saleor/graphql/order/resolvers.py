import graphene

from ...order import OrderStatus, models
from ...order.events import OrderEvents
from ...order.models import OrderEvent
from ...order.utils import sum_order_totals
from ..utils.filters import filter_by_period
from .enums import OrderStatusFilter
from .types import Order

ORDER_SEARCH_FIELDS = ("id", "discount_name", "token", "user_email", "user__email")


def filter_orders(qs, info, created, status):
    # DEPRECATED: Will be removed in Saleor 2.11, use the `filter` field instead.
    # filter orders by status
    if status is not None:
        if status == OrderStatusFilter.READY_TO_FULFILL:
            qs = qs.ready_to_fulfill()
        elif status == OrderStatusFilter.READY_TO_CAPTURE:
            qs = qs.ready_to_capture()

    # DEPRECATED: Will be removed in Saleor 2.11, use the `filter` field instead.
    # filter orders by creation date
    if created is not None:
        qs = filter_by_period(qs, created, "created")

    return qs


def resolve_orders(info, created, status, **_kwargs):
    qs = models.Order.objects.confirmed()
    return filter_orders(qs, info, created, status)


def resolve_draft_orders(info, created, **_kwargs):
    qs = models.Order.objects.drafts()
    return filter_orders(qs, info, created, None)


def resolve_orders_total(_info, period):
    qs = models.Order.objects.confirmed().exclude(status=OrderStatus.CANCELED)
    qs = filter_by_period(qs, period, "created")
    return sum_order_totals(qs)


def resolve_order(info, order_id):
    return graphene.Node.get_node_from_global_id(info, order_id, Order)


def resolve_homepage_events():
    # Filter only selected events to be displayed on homepage.
    types = [
        OrderEvents.PLACED,
        OrderEvents.PLACED_FROM_DRAFT,
        OrderEvents.ORDER_FULLY_PAID,
    ]
    return OrderEvent.objects.filter(type__in=types)


def resolve_order_by_token(token):
    return (
        models.Order.objects.exclude(status=OrderStatus.DRAFT)
        .filter(token=token)
        .first()
    )

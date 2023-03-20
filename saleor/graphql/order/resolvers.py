from uuid import UUID

from django.db.models import Q

from ...channel.models import Channel
from ...order import OrderStatus, models
from ...order.events import OrderEvents
from ...order.models import OrderEvent
from ...order.utils import sum_order_totals
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..core.context import get_database_connection_name
from ..core.tracing import traced_resolver
from ..utils.filters import filter_by_period

ORDER_SEARCH_FIELDS = ("id", "discount_name", "token", "user_email", "user__email")


def resolve_orders(info, channel_slug):
    database_connection_name = get_database_connection_name(info.context)
    qs = models.Order.objects.using(database_connection_name).non_draft()
    if channel_slug:
        qs = qs.filter(channel__slug=str(channel_slug))
    return qs


def resolve_draft_orders(info):
    database_connection_name = get_database_connection_name(info.context)
    return models.Order.objects.using(database_connection_name).drafts()


@traced_resolver
def resolve_orders_total(info, period, channel_slug):
    if channel_slug is None:
        channel_slug = get_default_channel_slug_or_graphql_error()
    channel = Channel.objects.filter(slug=str(channel_slug)).first()
    if not channel:
        return None
    database_connection_name = get_database_connection_name(info.context)
    qs = (
        models.Order.objects.using(database_connection_name)
        .non_draft()
        .exclude(status=OrderStatus.CANCELED)
        .filter(channel__slug=str(channel_slug))
    )
    qs = filter_by_period(qs, period, "created_at")
    return sum_order_totals(qs, channel.currency_code)


def resolve_order(info, id):
    if id is None:
        return None
    try:
        id = UUID(id)
        lookup = Q(id=id)
    except ValueError:
        lookup = Q(number=id) & Q(use_old_id=True)
    database_connection_name = get_database_connection_name(info.context)
    return models.Order.objects.using(database_connection_name).filter(lookup).first()


def resolve_homepage_events(info):
    # Filter only selected events to be displayed on homepage.
    types = [
        OrderEvents.PLACED,
        OrderEvents.PLACED_FROM_DRAFT,
        OrderEvents.ORDER_FULLY_PAID,
    ]
    database_connection_name = get_database_connection_name(info.context)
    return OrderEvent.objects.using(database_connection_name).filter(type__in=types)


def resolve_order_by_token(info, token):
    database_connection_name = get_database_connection_name(info.context)
    return (
        models.Order.objects.using(database_connection_name)
        .exclude(status=OrderStatus.DRAFT)
        .filter(id=token)
        .first()
    )

from uuid import UUID

from django.db.models import Q

from ...account.models import User
from ...app.models import App
from ...channel.models import Channel
from ...order import OrderStatus, models
from ...order.events import OrderEvents
from ...order.utils import sum_order_totals
from ..account.utils import get_user_accessible_channels
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..core.tracing import traced_resolver
from ..utils import get_user_or_app_from_context
from ..utils.filters import filter_by_period

ORDER_SEARCH_FIELDS = ("id", "discount_name", "token", "user_email", "user__email")


def resolve_orders(info, channel_slug):
    qs = models.Order.objects.non_draft()
    if channel_slug:
        qs = qs.filter(channel__slug=str(channel_slug))

    requestor = get_user_or_app_from_context(info.context)
    if isinstance(requestor, App):
        return qs
    accessible_channels = get_user_accessible_channels(requestor)
    return qs.filter(channel_id__in=accessible_channels.values("id"))


def resolve_draft_orders(info):
    qs = models.Order.objects.drafts()
    requestor = get_user_or_app_from_context(info.context)
    if isinstance(requestor, App):
        return qs
    accessible_channels = get_user_accessible_channels(requestor)
    return qs.filter(channel_id__in=accessible_channels.values("id"))


@traced_resolver
def resolve_orders_total(_info, period, channel_slug):
    if channel_slug is None:
        channel_slug = get_default_channel_slug_or_graphql_error()
    channel = Channel.objects.filter(slug=str(channel_slug)).first()
    if not channel:
        return None
    qs = (
        models.Order.objects.non_draft()
        .exclude(status=OrderStatus.CANCELED)
        .filter(channel__slug=str(channel_slug))
    )
    qs = filter_by_period(qs, period, "created_at")
    return sum_order_totals(qs, channel.currency_code)


def resolve_order(id):
    if id is None:
        return None
    try:
        id = UUID(id)
        lookup = Q(id=id)
    except ValueError:
        lookup = Q(number=id) & Q(use_old_id=True)
    return models.Order.objects.filter(lookup).first()


def resolve_homepage_events(info):
    # Filter only selected events to be displayed on homepage.
    types = [
        OrderEvents.PLACED,
        OrderEvents.PLACED_FROM_DRAFT,
        OrderEvents.ORDER_FULLY_PAID,
    ]
    lookup = Q(type__in=types)
    requestor = get_user_or_app_from_context(info.context)
    if isinstance(requestor, User):
        # get order events from orders that user has access to
        accessible_channels = get_user_accessible_channels(requestor)
        accessible_orders = models.Order.objects.filter(
            channel_id__in=accessible_channels.values("id")
        )
        lookup &= Q(order_id__in=accessible_orders.values("id"))
    return models.OrderEvent.objects.filter(lookup)


def resolve_order_by_token(token):
    return (
        models.Order.objects.exclude(status=OrderStatus.DRAFT).filter(id=token).first()
    )

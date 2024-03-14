from uuid import UUID

from django.db.models import Q

from ...channel.models import Channel
from ...core.exceptions import PermissionDenied
from ...order import OrderStatus, models
from ...order.events import OrderEvents
from ...order.utils import sum_order_totals
from ..account.utils import get_user_accessible_channels
from ..app.dataloaders import get_app_promise
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..core.context import get_database_connection_name
from ..core.tracing import traced_resolver
from ..utils.filters import filter_by_period

ORDER_SEARCH_FIELDS = ("id", "discount_name", "token", "user_email", "user__email")


def resolve_orders(
    info, channel_slug=None, requesting_user=None, requestor_has_access_to_all=False
):
    database_connection_name = get_database_connection_name(info.context)
    qs = models.Order.objects.using(database_connection_name).non_draft()
    if channel_slug:
        qs = qs.filter(channel__slug=str(channel_slug))

    if requesting_user and not requestor_has_access_to_all:
        return qs.filter(user_id=requesting_user.id)

    if get_app_promise(info.context).get():
        return qs

    accessible_channels = get_user_accessible_channels(info, info.context.user)
    if channel_slug and channel_slug not in [
        channel.slug for channel in accessible_channels
    ]:
        raise PermissionDenied(
            message=f"You do not have access to the {channel_slug} channel."
        )
    channel_ids = [channel.id for channel in accessible_channels]
    return qs.filter(channel_id__in=channel_ids)


def resolve_draft_orders(info):
    database_connection_name = get_database_connection_name(info.context)
    qs = models.Order.objects.using(database_connection_name).drafts()

    if get_app_promise(info.context).get():
        return qs

    accessible_channels = get_user_accessible_channels(info, info.context.user)
    channel_ids = [channel.id for channel in accessible_channels]
    return qs.filter(channel_id__in=channel_ids)


@traced_resolver
def resolve_orders_total(info, period, channel_slug):
    database_connection_name = get_database_connection_name(info.context)
    if channel_slug is None:
        channel_slug = get_default_channel_slug_or_graphql_error(
            allow_replica=info.context.allow_replica
        )
    channel = (
        Channel.objects.using(database_connection_name)
        .filter(slug=str(channel_slug))
        .first()
    )
    if not channel:
        return None

    app = get_app_promise(info.context).get()
    if not app:
        accessible_channels = get_user_accessible_channels(info, info.context.user)
        if channel_slug not in [channel.slug for channel in accessible_channels]:
            raise PermissionDenied(
                message=f"You do not have access to the {channel_slug} channel."
            )

    qs = (
        models.Order.objects.using(database_connection_name)
        .non_draft()
        .exclude(status__in=[OrderStatus.CANCELED, OrderStatus.EXPIRED])
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
    lookup = Q(type__in=types)
    app = get_app_promise(info.context).get()
    if not app:
        # get order events from orders that user has access to
        accessible_channels = get_user_accessible_channels(info, info.context.user)
        channel_ids = [channel.id for channel in accessible_channels]
        accessible_orders = models.Order.objects.using(database_connection_name).filter(
            channel_id__in=channel_ids
        )
        lookup &= Q(order_id__in=accessible_orders.values("id"))
    return models.OrderEvent.objects.using(database_connection_name).filter(lookup)


def resolve_order_by_token(info, token):
    database_connection_name = get_database_connection_name(info.context)
    return (
        models.Order.objects.using(database_connection_name)
        .exclude(status=OrderStatus.DRAFT)
        .filter(id=token)
        .first()
    )

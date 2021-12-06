from ...channel.models import Channel
from ...core.tracing import traced_resolver
from ...order import OrderStatus, models
from ...order.events import OrderEvents
from ...order.models import OrderEvent
from ...order.utils import get_valid_shipping_methods_for_order, sum_order_totals
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..shipping.dataloaders import ShippingMethodChannelListingByChannelSlugLoader
from ..shipping.utils import annotate_active_shipping_methods
from ..utils.filters import filter_by_period

ORDER_SEARCH_FIELDS = ("id", "discount_name", "token", "user_email", "user__email")


def resolve_orders(_info, channel_slug, **_kwargs):
    qs = models.Order.objects.non_draft()
    if channel_slug:
        qs = qs.filter(channel__slug=str(channel_slug))
    return qs


def resolve_draft_orders(_info, **_kwargs):
    qs = models.Order.objects.drafts()
    return qs


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
    qs = filter_by_period(qs, period, "created")
    return sum_order_totals(qs, channel.currency_code)


def resolve_order(id):
    return models.Order.objects.filter(pk=id).first()


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


def _resolve_order_shipping_methods(
    root: models.Order,
    info,
    shipping_method_channel_listings,
):
    # TODO: We should optimize it in/after PR#5819
    cache_key = "__fetched_shipping_methods"
    if hasattr(root, cache_key):
        return getattr(root, cache_key)

    available = get_valid_shipping_methods_for_order(
        root, shipping_method_channel_listings
    )
    manager = info.context.plugins

    excluded_shipping_methods = manager.excluded_shipping_methods_for_order(
        root, available
    )
    annotate_active_shipping_methods(
        available,
        excluded_shipping_methods,
    )

    setattr(root, cache_key, available)
    return getattr(root, cache_key)


def resolve_order_shipping_methods(root: models.Order, info, include_active_only=False):
    # TODO: We should optimize it in/after PR#5819
    def with_channel(channel):
        def with_listings(channel_listings):
            instances = _resolve_order_shipping_methods(root, info, channel_listings)
            if include_active_only:
                instances = [instance for instance in instances if instance.active]
            return instances

        return (
            ShippingMethodChannelListingByChannelSlugLoader(info.context)
            .load(channel.slug)
            .then(with_listings)
        )

    return ChannelByIdLoader(info.context).load(root.channel_id).then(with_channel)

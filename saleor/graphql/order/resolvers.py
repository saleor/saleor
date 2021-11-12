from ...channel.models import Channel
from ...core.taxes import identical_taxed_money
from ...core.tracing import traced_resolver
from ...order import OrderStatus, models
from ...order.events import OrderEvents
from ...order.models import OrderEvent
from ...order.utils import get_valid_shipping_methods_for_order, sum_order_totals
from ..channel import ChannelContext
from ..channel.utils import get_default_channel_slug_or_graphql_error
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


# TODO: We should optimize it in/after PR#5819
def resolve_order_shipping_methods(root: models.Order, info):
    available = get_valid_shipping_methods_for_order(root)
    if available is None:
        return []
    if available is not None:
        available_shipping_methods = []
        channel_slug = root.channel.slug
        for shipping_method in available:
            # Ignore typing check because it is checked in
            # get_valid_shipping_methods_for_order
            shipping_channel_listing = (
                shipping_method.channel_listings.filter(  # type: ignore
                    channel=root.channel
                ).first()
            )
            if shipping_channel_listing:
                shipping_method.price = identical_taxed_money(
                    shipping_channel_listing.price
                )
                shipping_method.minimum_order_price = (
                    shipping_channel_listing.minimum_order_price
                )
                available_shipping_methods.append(shipping_method)
    instances = [
        ChannelContext(node=method, channel_slug=channel_slug) for method in available
    ]
    return instances

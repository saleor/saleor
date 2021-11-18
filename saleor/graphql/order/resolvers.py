from ...channel.models import Channel
from ...core.tracing import traced_resolver
from ...order import OrderStatus, models
from ...order.events import OrderEvents
from ...order.models import OrderEvent
from ...order.utils import get_valid_shipping_methods_for_order, sum_order_totals
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..shipping.utils import (
    annotate_active_shipping_methods,
    convert_shipping_method_model_to_dataclass,
    wrap_with_channel_context,
)
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


def _resolve_order_shipping_methods(root: models.Order, info):
    # TODO: We should optimize it in/after PR#5819
    cache_key = "__fetched_shipping_methods"
    if hasattr(root, cache_key):
        return getattr(root, cache_key)

    available = get_valid_shipping_methods_for_order(root)
    if available is None:
        return []
    available_shipping_methods = []
    manager = info.context.plugins
    channel_slug = root.channel.slug
    for shipping_method in available:
        # Ignore typing check because it is checked in
        # get_valid_shipping_methods_for_order
        shipping_channel_listing = shipping_method.channel_listings.filter(
            channel=root.channel
        ).first()
        if shipping_channel_listing:
            shipping_method.price = shipping_channel_listing.price
            available_shipping_methods.append(shipping_method)

    shipping_method_dataclasses = [
        convert_shipping_method_model_to_dataclass(shipping)
        for shipping in available_shipping_methods
    ]
    excluded_shipping_methods = manager.excluded_shipping_methods_for_order(
        root, shipping_method_dataclasses
    )
    annotate_active_shipping_methods(
        available_shipping_methods,
        excluded_shipping_methods,
    )
    available_with_channel_context = wrap_with_channel_context(
        available_shipping_methods,
        channel_slug,
    )

    setattr(root, cache_key, available_with_channel_context)
    return getattr(root, cache_key)


def resolve_order_shipping_methods(root: models.Order, info, include_active_only=False):
    # TODO: We should optimize it in/after PR#5819
    instances = _resolve_order_shipping_methods(root, info)
    if include_active_only:
        instances = [instance for instance in instances if instance.node.active]
    return instances

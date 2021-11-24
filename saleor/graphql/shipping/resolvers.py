from prices import MoneyRange

from ...shipping import models
from ..channel import ChannelContext, ChannelQsContext
from .dataloaders import (
    ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader,
)


def resolve_shipping_zones(channel_slug):
    if channel_slug:
        instances = models.ShippingZone.objects.filter(channels__slug=channel_slug)
    else:
        instances = models.ShippingZone.objects.all()
    return ChannelQsContext(qs=instances, channel_slug=channel_slug)


def resolve_price_range(channel_slug):
    # TODO: Add dataloader.
    channel_listing = models.ShippingMethodChannelListing.objects.filter(
        channel__slug=str(channel_slug)
    )
    prices = [shipping.get_total() for shipping in channel_listing]

    return MoneyRange(min(prices), max(prices)) if prices else None


def resolve_shipping_minimum_order_price(
    root: ChannelContext[models.ShippingMethod], info, **_kwargs
):
    if not root.channel_slug:
        return None

    return (
        ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(info.context)
        .load((root.node.id, root.channel_slug))
        .then(
            lambda channel_listing: channel_listing
            and channel_listing.minimum_order_price
        )
    )


def resolve_shipping_maximum_order_price(
    root: ChannelContext[models.ShippingMethod], info, **_kwargs
):
    if not root.channel_slug:
        return None

    return (
        ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(info.context)
        .load((root.node.id, root.channel_slug))
        .then(
            lambda channel_listing: channel_listing
            and channel_listing.maximum_order_price
        )
    )


def resolve_shipping_price(
    root: ChannelContext[models.ShippingMethod], info, **_kwargs
):
    # Price field are dynamically generated in "available_shipping_methods" resolver
    price = getattr(root.node, "price", None)
    if price is not None:
        return price

    if not root.channel_slug:
        return None

    return (
        ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(info.context)
        .load((root.node.id, root.channel_slug))
        .then(lambda channel_listing: channel_listing and channel_listing.price)
    )

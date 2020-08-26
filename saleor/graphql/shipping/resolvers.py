from prices import MoneyRange

from ...shipping import models
from ..channel.types import ChannelContext


def resolve_shipping_zones(channel_slug):
    instances = models.ShippingZone.objects.all()
    shipping_zones = [
        ChannelContext(node=shipping_zone, channel_slug=channel_slug)
        for shipping_zone in instances
    ]
    return shipping_zones


def resolve_price_range(channel_slug):
    # TODO: Add dataloader.
    channel_listing = models.ShippingMethodChannelListing.objects.filter(
        channel__slug=str(channel_slug)
    )
    prices = [shipping.get_total() for shipping in channel_listing]

    return MoneyRange(min(prices), max(prices)) if prices else None

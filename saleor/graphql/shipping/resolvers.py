from prices import MoneyRange

from ...shipping import models
from ..channel import ChannelQsContext


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

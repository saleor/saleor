from prices import MoneyRange

from ...shipping import models
from ...shipping.interface import ShippingMethodData
from ..channel import ChannelQsContext
from ..translations.resolvers import resolve_translation


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


def resolve_shipping_translation(root: ShippingMethodData, info, *, language_code):
    if root.is_external:
        return None
    return resolve_translation(root, info, language_code=language_code)

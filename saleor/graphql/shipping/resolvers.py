from prices import MoneyRange

from ...shipping import models
from ...shipping.interface import ShippingMethodData
from ..channel import ChannelQsContext
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..translations.resolvers import resolve_translation


def resolve_shipping_zones(info, channel_slug):
    if channel_slug:
        instances = models.ShippingZone.objects.using(
            get_database_connection_name(info.context)
        ).filter(channels__slug=channel_slug)
    else:
        instances = models.ShippingZone.objects.using(
            get_database_connection_name(info.context)
        ).all()
    return ChannelQsContext(qs=instances, channel_slug=channel_slug)


def resolve_price_range(info, channel_slug):
    # TODO: Add dataloader.
    channel_listing = models.ShippingMethodChannelListing.objects.using(
        get_database_connection_name(info.context)
    ).filter(channel__slug=str(channel_slug))
    prices = [shipping.get_total() for shipping in channel_listing]

    return MoneyRange(min(prices), max(prices)) if prices else None


def resolve_shipping_translation(
    root: ShippingMethodData, info: ResolveInfo, *, language_code
):
    if root.is_external:
        return None
    return resolve_translation(root, info, language_code=language_code)

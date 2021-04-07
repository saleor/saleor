from ...store import models
from ..channel.types import ChannelContext


def resolve_store_type_name(channel_slug):
    instances = models.Store.objects.all()
    store_type_name = [
        ChannelContext(node=shipping_zone, channel_slug=channel_slug)
        for shipping_zone in instances
    ]
    return store_type_name


def resolve_store_type_description(channel_slug):
    # TODO: Add dataloader.
    channel_listing = models.ShippingMethodChannelListing.objects.filter(
        channel__slug=str(channel_slug)
    )
    prices = [shipping.get_total() for shipping in channel_listing]

    return MoneyRange(min(prices), max(prices)) if prices else None

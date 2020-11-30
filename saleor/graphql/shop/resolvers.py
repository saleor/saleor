from ...shipping.models import ShippingMethod
from ..channel import ChannelContext


def resolve_available_shipping_methods(info, channel_slug: str, address):
    available = ShippingMethod.objects.filter(
        channel_listings__channel__slug=channel_slug
    )
    if address and address.country:
        available = available.filter(
            shipping_zone__countries__contains=address.country,
        )

    if available is None:
        return []
    manager = info.context.plugins
    display_gross = info.context.site.settings.display_gross_prices
    for shipping_method in available:
        shipping_channel_listing = shipping_method.channel_listings.get(
            channel__slug=channel_slug
        )
        taxed_price = manager.apply_taxes_to_shipping(
            shipping_channel_listing.price, address
        )
        if display_gross:
            shipping_method.price = taxed_price.gross
        else:
            shipping_method.price = taxed_price.net

    return [
        ChannelContext(node=shipping, channel_slug=channel_slug)
        for shipping in available
    ]

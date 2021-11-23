from ...account.models import Address
from ...core.tracing import traced_resolver
from ...shipping.models import ShippingMethod, ShippingMethodChannelListing
from ...shipping.postal_codes import filter_shipping_methods_by_postal_code_rules
from ..channel import ChannelContext


@traced_resolver
def resolve_available_shipping_methods(info, channel_slug: str, address):
    available = ShippingMethod.objects.for_channel(channel_slug)
    if address and address.country:
        available = available.filter(
            shipping_zone__countries__contains=address.country,
        )
        available = filter_shipping_methods_by_postal_code_rules(
            available, Address(**address)
        )
        # Address instance needed for apply_taxes_to_shipping method
        address = Address(country=address.country)
    else:
        address = Address()

    if available is None:
        return []
    shipping_mapping = get_shipping_method_to_shipping_price_mapping(
        available, channel_slug
    )
    for shipping_method in available:
        shipping_price = shipping_mapping[shipping_method.pk]
        shipping_method.price = shipping_price

    return [
        ChannelContext(node=shipping, channel_slug=channel_slug)
        for shipping in available
    ]


def get_shipping_method_to_shipping_price_mapping(shipping_methods, channel_slug):
    """Prepare mapping shipping method to price from channel listings."""
    shipping_mapping = {}
    shipping_listings = ShippingMethodChannelListing.objects.filter(
        shipping_method__in=shipping_methods, channel__slug=channel_slug
    )
    for listing in shipping_listings:
        shipping_mapping[listing.shipping_method.id] = listing.price

    return shipping_mapping

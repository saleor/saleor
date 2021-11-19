from ...account.models import Address
from ...core.tracing import traced_resolver
from ...shipping.models import ShippingMethod, ShippingMethodChannelListing
from ...shipping.postal_codes import filter_shipping_methods_by_postal_code_rules
from ...shipping.utils import convert_to_shipping_method_data
from ..channel import ChannelContext


@traced_resolver
def resolve_available_shipping_methods(info, channel_slug: str, address):
    instances = []
    available = ShippingMethod.objects.for_channel(channel_slug)
    if address and address.country:
        available = available.filter(
            shipping_zone__countries__contains=address.country,
        )
        available = filter_shipping_methods_by_postal_code_rules(
            available, Address(**address)
        )

    if available is not None:
        mapping = get_shipping_method_to_listing_mapping(available, channel_slug)
        instances += [
            ChannelContext(
                node=convert_to_shipping_method_data(method, mapping[method.id]),
                channel_slug=channel_slug,
            )
            for method in available
        ]

    return instances


def get_shipping_method_to_listing_mapping(shipping_methods, channel_slug):
    """Prepare mapping shipping method to its channel listings."""
    shipping_mapping = {}
    shipping_listings = ShippingMethodChannelListing.objects.filter(
        shipping_method__in=shipping_methods, channel__slug=channel_slug
    )
    for listing in shipping_listings:
        shipping_mapping[listing.shipping_method_id] = listing

    return shipping_mapping

from django.utils import translation
from django_countries import countries

from ...account.models import Address
from ...shipping.models import ShippingMethod, ShippingMethodChannelListing
from ...shipping.postal_codes import filter_shipping_methods_by_postal_code_rules
from ...shipping.utils import convert_to_shipping_method_data
from ..core.tracing import traced_resolver
from ..core.types import CountryDisplay
from .utils import get_countries_codes_list


@traced_resolver
def resolve_available_shipping_methods(_info, *, channel_slug: str, address):
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
            convert_to_shipping_method_data(method, mapping[method.id])
            for method in available
        ]

    return instances


def resolve_countries(**kwargs):
    countries_filter = kwargs.get("filter", {})
    attached_to_shipping_zones = countries_filter.get("attached_to_shipping_zones")
    language_code = kwargs.get("language_code")
    codes_list = get_countries_codes_list(attached_to_shipping_zones)
    # DEPRECATED: translation.override will be dropped in Saleor 4.0
    with translation.override(language_code):
        return [
            CountryDisplay(code=country[0], country=country[1], vat=None)
            for country in countries
            if country[0] in codes_list
        ]


def get_shipping_method_to_listing_mapping(shipping_methods, channel_slug):
    """Prepare mapping shipping method to its channel listings."""
    shipping_mapping = {}
    shipping_listings = ShippingMethodChannelListing.objects.filter(
        shipping_method__in=shipping_methods, channel__slug=channel_slug
    )
    for listing in shipping_listings:
        shipping_mapping[listing.shipping_method_id] = listing

    return shipping_mapping

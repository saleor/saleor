from django.utils import translation
from django_countries import countries
from django_prices_vatlayer.models import VAT

from ...account.models import Address
from ...core.tracing import traced_resolver
from ...shipping.models import ShippingMethod, ShippingMethodChannelListing
from ...shipping.postal_codes import filter_shipping_methods_by_postal_code_rules
from ..channel import ChannelContext
from ..core.types import CountryDisplay
from .utils import get_countries_codes_list


@traced_resolver
def resolve_available_shipping_methods(info, channel_slug: str, address):
    instances = []
    manager = info.context.plugins
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

    if available is not None:
        display_gross = info.context.site.settings.display_gross_prices
        shipping_mapping = get_shipping_method_to_shipping_price_mapping(
            available, channel_slug
        )
        for shipping_method in available:
            shipping_price = shipping_mapping[shipping_method.pk]
            taxed_price = manager.apply_taxes_to_shipping(
                shipping_price, address, channel_slug
            )
            if display_gross:
                shipping_method.price = taxed_price.gross
            else:
                shipping_method.price = taxed_price.net

        instances += [
            ChannelContext(node=shipping, channel_slug=channel_slug)
            for shipping in available
        ]

    return instances


def resolve_countries(**kwargs):
    countries_filter = kwargs.get("filter", {})
    attached_to_shipping_zones = countries_filter.get("attached_to_shipping_zones")
    language_code = kwargs.get("language_code")
    taxes = {vat.country_code: vat for vat in VAT.objects.all()}
    # DEPRECATED: translation.override will be dropped in Saleor 4.0
    with translation.override(language_code):
        return [
            CountryDisplay(
                code=country[0], country=country[1], vat=taxes.get(country[0])
            )
            for country in countries
            if country[0] in get_countries_codes_list(attached_to_shipping_zones)
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

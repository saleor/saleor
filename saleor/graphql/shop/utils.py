from typing import Optional

from django_countries import countries

from ...shipping.models import ShippingZone


def get_countries_codes_list(attached_to_shipping_zones: Optional[bool] = None):
    """Return set of countries codes.

    If 'True', return countries with shipping zone assigned.
    If 'False', return countries without any shipping zone assigned."
    If the argument is not provided (None), return all countries.
    """

    all_countries_codes = {country[0] for country in countries}
    if attached_to_shipping_zones is not None:
        covered_countries_codes = set()
        for zone in ShippingZone.objects.iterator():
            covered_countries_codes.update({country.code for country in zone.countries})

        if attached_to_shipping_zones:
            return covered_countries_codes

        if not attached_to_shipping_zones:
            return all_countries_codes - covered_countries_codes

    return all_countries_codes

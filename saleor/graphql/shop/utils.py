from typing import Optional

from django.conf import settings
from django_countries import countries

from ...shipping.models import ShippingZone
from ..site.dataloaders import get_site_promise


def get_countries_codes_list(
    attached_to_shipping_zones: Optional[bool] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Return set of countries codes.

    If 'True', return countries with shipping zone assigned.
    If 'False', return countries without any shipping zone assigned."
    If the argument is not provided (None), return all countries.
    """

    all_countries_codes = {country[0] for country in countries}
    if attached_to_shipping_zones is not None:
        covered_countries_codes = set()
        for zone in ShippingZone.objects.using(database_connection_name).iterator():
            covered_countries_codes.update({country.code for country in zone.countries})

        if attached_to_shipping_zones:
            return covered_countries_codes

        if not attached_to_shipping_zones:
            return all_countries_codes - covered_countries_codes

    return all_countries_codes


def get_track_inventory_by_default(info):
    site = get_site_promise(info.context).get()
    if site is not None and site.settings is not None:
        return site.settings.track_inventory_by_default
    return None

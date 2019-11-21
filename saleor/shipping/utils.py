from ..account.i18n import COUNTRY_CHOICES
from .models import ShippingZone


def currently_used_countries(zone_pk=None):
    shipping_zones = ShippingZone.objects.exclude(pk=zone_pk)
    used_countries = {
        (country.code, country.name)
        for shipping_zone in shipping_zones
        for country in shipping_zone.countries
    }
    return used_countries


def get_available_countries(zone_pk=None):
    return set(COUNTRY_CHOICES) - currently_used_countries(zone_pk)


def default_shipping_zone_exists(zone_pk=None):
    return ShippingZone.objects.exclude(pk=zone_pk).filter(default=True)

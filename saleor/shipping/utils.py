from django_countries import countries


def default_shipping_zone_exists(zone_pk=None):
    from .models import ShippingZone

    return ShippingZone.objects.exclude(pk=zone_pk).filter(default=True)


def get_countries_without_shipping_zone():
    """Return countries that are not assigned to any shipping zone."""
    from .models import ShippingZone

    covered_countries = set()
    for zone in ShippingZone.objects.all():
        covered_countries.update({c.code for c in zone.countries})
    return (country[0] for country in countries if country[0] not in covered_countries)

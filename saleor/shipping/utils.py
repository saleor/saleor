from .models import ShippingZone


def default_shipping_zone_exists(zone_pk=None):
    return ShippingZone.objects.exclude(pk=zone_pk).filter(default=True)

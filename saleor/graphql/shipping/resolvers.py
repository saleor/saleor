from ...shipping import models


def resolve_shipping_zones(info):
    return models.ShippingZone.objects.all()

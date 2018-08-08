from ...shipping import models


def resolve_shipping_rates(info):
    return models.ShippingRate.objects.all()

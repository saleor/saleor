from ...shipping import models


def resolve_shipping_methods(info):
    return models.ShippingMethod.objects.all()

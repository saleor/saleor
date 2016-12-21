from django.db.models import Q
from .models import ShippingMethodCountry


def get_shipment_options(country_code):
    shipping_methods_qs = ShippingMethodCountry.objects.select_related(
        'shipping_method').values('price', 'shipping_method__name')
    shipping_methods = shipping_methods_qs.filter(country_code=country_code)
    if not shipping_methods.exists():
        shipping_methods = shipping_methods_qs.filter(country_code='')
    return shipping_methods

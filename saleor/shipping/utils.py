from django.db.models import Q
from .models import ShippingMethodCountry


def get_shipment_options(country_code):
    return ShippingMethodCountry.objects.select_related(
        'shipping_method').filter(
        Q(country_code=country_code) | Q(country_code='')).order_by(
        'price').values('price', 'shipping_method__name')

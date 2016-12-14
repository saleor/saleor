from .models import ShippingMethodCountry, COUNTRY_CODE_CHOICES


def assign_shipment_to_country():
    shippments = {}
    for code in COUNTRY_CODE_CHOICES:
        shippments[code[0]] = ShippingMethodCountry.objects.select_related(
            'shipping_method').filter(country_code=code)
    return shippments


from django.conf import settings
from django.utils.encoding import smart_text

from django_prices_vatlayer.utils import get_tax_for_country


def get_price_with_vat(product, price, country):
    if country and settings.VATLAYER_ACCESS_KEY:
        rate_name = product.product_class.vat_rate_type
        vat = get_tax_for_country(country, rate_name)
        if vat:
            price = vat.apply(price).quantize('0.01')
    return price

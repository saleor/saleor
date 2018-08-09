from prices import MoneyRange

from ..core.utils.taxes import get_taxed_shipping_price
from .models import ShippingMethod


def shipping_price_estimate(price, weight, country_code, taxes):
    """Returns estimated price range for shipping for given order."""
    shipping_methods = ShippingMethod.objects.applicable_shipping_methods(
        price, weight, country_code)
    shipping_methods = shipping_methods.values_list('price', flat=True)
    if not shipping_methods:
        return
    prices = MoneyRange(
        start=min(shipping_methods), stop=max(shipping_methods))
    return get_taxed_shipping_price(prices, taxes)

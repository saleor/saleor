from prices import MoneyRange

from ..core.utils.taxes import (
    DEFAULT_TAX_RATE_NAME, apply_tax_to_price, charge_taxes_on_shipping)


def get_taxed_shipping_price(price, taxes):
    """Calculate shipping price based on settings and taxes."""
    charge_taxes = charge_taxes_on_shipping()
    if not charge_taxes:
        taxes = None
    return apply_tax_to_price(taxes, DEFAULT_TAX_RATE_NAME, price)


def get_shipment_options(country_code, taxes):
    from .models import ShippingMethodCountry
    shipping_methods_qs = ShippingMethodCountry.objects.select_related(
        'shipping_method')
    shipping_methods = shipping_methods_qs.filter(country_code=country_code)
    if not shipping_methods.exists():
        shipping_methods = shipping_methods_qs.filter(country_code='')
    if shipping_methods:
        shipping_methods = shipping_methods.values_list('price', flat=True)
        prices = MoneyRange(
            start=min(shipping_methods), stop=max(shipping_methods))
        return get_taxed_shipping_price(prices, taxes)

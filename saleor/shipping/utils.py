from django.contrib.sites.models import Site
from prices import MoneyRange

from ..core.utils import apply_tax_to_price, DEFAULT_TAX_RATE_NAME


def get_taxed_shipping_price(price, taxes=None):
    """Calculate shipping price based on settings and taxes."""
    charge_taxes = (
        Site.objects.get_current().settings.charge_taxes_on_shipping)
    if not charge_taxes:
        taxes = None
    return apply_tax_to_price(taxes, DEFAULT_TAX_RATE_NAME, price)


def get_shipment_options(country_code, taxes=None):
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

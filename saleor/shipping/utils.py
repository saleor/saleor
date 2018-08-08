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
    from .models import ShippingRate
    shipping_rates = ShippingRate.objects.prefetch_related(
        'shipping_zone')
    shipping_rates = shipping_rates.filter(
        shipping_zone__countries__contains=country_code)
    if shipping_rates:
        shipping_rates = shipping_rates.values_list('price', flat=True)
        prices = MoneyRange(
            start=min(shipping_rates), stop=max(shipping_rates))
        return get_taxed_shipping_price(prices, taxes)

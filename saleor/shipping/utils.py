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
    from ..core.i18n import ANY_COUNTRY, COUNTRY_CODE_CHOICES

    shipping_rates = ShippingRate.objects.prefetch_related(
        'shipping_zone')
    shipping_rates = shipping_rates.filter(
        shipping_zone__countries__contains=country_code)
    if not shipping_rates.exists():
        shipping_rates = shipping_rates.filter(
            shipping_zone__countries__contains=ANY_COUNTRY)
    if shipping_rates:
        shipping_rates = shipping_rates.values_list('price', flat=True)
        prices = MoneyRange(
            start=min(shipping_rates), stop=max(shipping_rates))
        return get_taxed_shipping_price(prices, taxes)


def country_choices():
    from .models import ShippingZone
    from ..core.i18n import ANY_COUNTRY, COUNTRY_CODE_CHOICES
    country_codes = []
    shipping_zones = ShippingZone.objects.all()
    for shipping_zone in shipping_zones:
        for country in shipping_zone.countries:
            country_codes.append(country.code)
    country_codes = set(country_codes)

    if ANY_COUNTRY in country_codes:
        return COUNTRY_CODE_CHOICES
    country_dict = dict(COUNTRY_CODE_CHOICES)
    country_choices = [
        (country_code, country_dict[country_code])
        for country_code in country_codes]
    return country_choices

from decimal import Decimal
from typing import Dict

from django_countries import countries

# List of zero-decimal currencies
# Since there is no public API in Stripe backend or helper function
# in Stripe's Python library, this list is straight out of Stripe's docs
# https://stripe.com/docs/currencies#zero-decimal
ZERO_DECIMAL_CURRENCIES = [
    'BIF', 'CLP', 'DJF', 'GNF', 'JPY', 'KMF', 'KRW', 'MGA',
    'PYG', 'RWF', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF']


def get_amount_for_stripe(amount, currency):
    """Get appropriate amount for stripe.
    Stripe is using currency's smallest unit such as cents for USD and
    stripe requires integer instead of decimal, so multiplying by 100
    and converting to integer is required. But for zero-decimal currencies,
    multiplying by 100 is not needed.
    """
    # Multiply by 100 for non-zero-decimal currencies
    if currency.upper() not in ZERO_DECIMAL_CURRENCIES:
        amount *= 100

    # Using int(Decimal) directly may yield wrong result
    # such as int(Decimal(24.24)*100) will equal to 2423
    return int(amount.to_integral_value())


def get_amount_from_stripe(amount, currency):
    """Get appropriate amount from stripe."""
    amount = Decimal(amount)

    # Divide by 100 for non-zero-decimal currencies
    if currency.upper() not in ZERO_DECIMAL_CURRENCIES:
        # Using Decimal(amount / 100.0) will convert to decimal from float
        # where precision may be lost
        amount /= Decimal(100)

    return amount


def get_currency_for_stripe(currency):
    """Convert Saleor's currency format to Stripe's currency format.
    Stripe's currency is using lowercase while Saleor is using uppercase.
    """
    return currency.lower()


def get_currency_from_stripe(currency):
    """Convert Stripe's currency format to Saleor's currency format.
    Stripe's currency is using lowercase while Saleor is using uppercase.
    """
    return currency.upper()


def get_payment_billing_fullname(payment_information: Dict):
    # Get billing name from payment
    return '%s %s' % (
        payment_information['billing']['last_name'],
        payment_information['billing']['first_name'])


def shipping_to_stripe_dict(shipping: Dict):
    return {
        'line1': shipping['street_address_1'],
        'line2': shipping['street_address_2'],
        'city': shipping['city'],
        'state': shipping['country_area'],
        'postal_code': shipping['postal_code'],
        'country': dict(countries).get(shipping['country'], '')}

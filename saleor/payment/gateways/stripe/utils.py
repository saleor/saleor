from decimal import Decimal


# FIXME: The amount should be dynamically calculated by payment's currency.
# For example, amount will wrong for JPY since JPY does not support cents


def get_amount_for_stripe(amount, currency):
    """Get appropriate amount for stripe.
    Stripe is using currency's smallest unit such as cents for USD.
    Stripe requires integer instead of decimal.
    """
    return int(amount * 100)


def get_amount_from_stripe(amount, currency):
    """Get appropriate amount from stripe.
    Stripe is using currency's smallest unit such as cents for USD.
    Saleor requires decimal instead of float or integer.
    """
    return Decimal(amount / 100.0)

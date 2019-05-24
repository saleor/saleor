from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from prices import TaxedMoney

from . import ZERO_TAXED_MONEY
from .vatlayer import interface as vatlayer_interface
from .avatax import interface as avatax_interface

from ...checkout.models import Checkout
from ...discount.models import SaleQueryset


def get_total_gross(checkout: Checkout, discounts: SaleQueryset) -> TaxedMoney:
    """Calculate total gross for checkout"""

    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_total_gross(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_total_gross(checkout, discounts)

    return checkout.get_total(discounts)


def get_subtotal_gross(checkout: Checkout, discounts: SaleQueryset) -> TaxedMoney:
    """Calculate subtotal gross for checkout"""

    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_subtotal_gross(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_subtotal_gross(checkout, discounts)

    return checkout.get_subtotal(discounts)


def get_shipping_gross(checkout: Checkout, discounts: SaleQueryset) -> TaxedMoney:
    """Calculate shipping gross for checkout"""
    if not checkout.shipping_method:
        return ZERO_TAXED_MONEY
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_shipping_gross(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_shipping_gross(checkout, discounts)
    return checkout.shipping_method.get_total()


def get_lines_with_taxes(checkout: Checkout, discounts):
    lines_taxes = defaultdict(lambda: Decimal("0.0"))

    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_lines_with_taxes(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_lines_with_taxes(checkout, discounts)

    return [(line, lines_taxes[line.variant.sku]) for line in checkout.lines.all()]

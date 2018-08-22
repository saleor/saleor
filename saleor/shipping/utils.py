from django.db.models import Q
from django.utils.translation import pgettext_lazy
from prices import MoneyRange

from ..core.utils.taxes import get_taxed_shipping_price
from ..core.weight import convert_weight, get_default_weight_unit


def get_shipping_price_estimate(price, weight, country_code, taxes):
    """Returns estimated price range for shipping for given order."""
    from .models import ShippingMethod

    shipping_methods = ShippingMethod.objects.applicable_shipping_methods(
        price, weight, country_code)
    shipping_methods = shipping_methods.values_list('price', flat=True)
    if not shipping_methods:
        return
    prices = MoneyRange(
        start=min(shipping_methods), stop=max(shipping_methods))
    return get_taxed_shipping_price(prices, taxes)


def applicable_weight_based_methods(weight, qs):
    """Returns weight based ShippingMethods that can be applied to an order
    with given total weight.
    """
    qs = qs.weight_based()
    min_weight_matched = Q(minimum_order_weight__lte=weight)
    no_weight_limit = Q(maximum_order_weight__isnull=True)
    max_weight_matched = Q(maximum_order_weight__gte=weight)
    return qs.filter(
        min_weight_matched & (no_weight_limit | max_weight_matched))


def applicable_price_based_methods(price, qs):
    """Returns price based ShippingMethods that can be applied to an order
    with given price total.
    """
    qs = qs.price_based()
    min_price_matched = Q(minimum_order_price__lte=price)
    no_price_limit = Q(maximum_order_price__isnull=True)
    max_price_matched = Q(maximum_order_price__gte=price)
    return qs.filter(
        min_price_matched & (no_price_limit | max_price_matched))


def get_price_type_display(min_price, max_price):
    from ..core.utils import format_money

    if max_price is None:
        return pgettext_lazy(
            'Applies to orders more expensive than the min value',
            '%(min_price)s and up') % {'min_price': format_money(min_price)}
    return pgettext_lazy(
        'Applies to order valued within this price range',
        '%(min_price)s to %(max_price)s') % {
            'min_price': format_money(min_price),
            'max_price': format_money(max_price)}


def get_weight_type_display(min_weight, max_weight):
    default_unit = get_default_weight_unit()

    if min_weight.unit != default_unit:
        min_weight = convert_weight(min_weight, default_unit)
    if max_weight and max_weight.unit != default_unit:
        max_weight = convert_weight(max_weight, default_unit)

    if max_weight is None:
        return pgettext_lazy(
            'Applies to orders heavier than the threshold',
            '%(min_weight)s and up') % {'min_weight': min_weight}
    return pgettext_lazy(
        'Applies to orders of total weight within this range',
        '%(min_weight)s to %(max_weight)s' % {
            'min_weight': min_weight, 'max_weight': max_weight})

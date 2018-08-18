from django.db.models import Q
from django.utils.translation import pgettext_lazy
from prices import MoneyRange

from ..core.utils.taxes import get_taxed_shipping_price


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


def get_price_type_display(minimum_order_price, maximum_order_price):
    from ..core.utils import format_money

    if maximum_order_price is None:
        return pgettext_lazy(
            'Applies to orders more expensive than the min value',
            '%(minimum_order_price)s and up') % {
                'minimum_order_price': format_money(minimum_order_price)}
    return pgettext_lazy(
        'Applies to order valued within this price range',
        '%(minimum_order_price)s to %(maximum_order_price)s') % {
            'minimum_order_price': format_money(minimum_order_price),
            'maximum_order_price': format_money(maximum_order_price)}


def get_weight_type_display(minimum_order_weight, maximum_order_weight):
    if maximum_order_weight is None:
        return pgettext_lazy(
            'Applies to orders heavier than the threshold',
            '%(minimum_order_weight)s and up') % {
                'minimum_order_weight': minimum_order_weight}
    return pgettext_lazy(
        'Applies to orders of total weight within this range',
        '%(minimum_order_weight)s to %(maximum_order_weight)s' % {
            'minimum_order_weight': minimum_order_weight,
            'maximum_order_weight': maximum_order_weight})

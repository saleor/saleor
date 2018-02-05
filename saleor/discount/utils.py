from django.db.models import F

from .models import NotApplicable


def increase_voucher_usage(voucher):
    voucher.used = F('used') + 1
    voucher.save(update_fields=['used'])


def decrease_voucher_usage(voucher):
    voucher.used = F('used') - 1
    voucher.save(update_fields=['used'])


def get_product_discounts(product, discounts, **kwargs):
    for discount in discounts:
        try:
            yield discount.modifier_for_product(product, **kwargs)
        except NotApplicable:
            pass


def calculate_discounted_price(product, price, discounts, **kwargs):
    if discounts:
        discounts = list(
            get_product_discounts(product, discounts, **kwargs))
        if discounts:
            price = min(price | discount for discount in discounts)
    return price

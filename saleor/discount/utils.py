from django.db.models import F
from django.utils.translation import pgettext

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
            yield get_product_discount_on_sale(discount, product)
        except NotApplicable:
            pass


def calculate_discounted_price(product, price, discounts, **kwargs):
    if discounts:
        discounts = list(
            get_product_discounts(product, discounts, **kwargs))
        if discounts:
            price = min(price | discount for discount in discounts)
    return price


def is_category_discounted(category, discounted_categories):
    return any([
        category.is_descendant_of(c, include_self=True)
        for c in discounted_categories])


def get_product_discount_on_sale(sale, product):
    discounted_products = {p.pk for p in sale.products.all()}
    discounted_categories = set(sale.categories.all())
    is_product_discounted = (
        product.pk in discounted_products or
        is_category_discounted(product.category, discounted_categories))
    if is_product_discounted:
        return sale.get_discount()
    raise NotApplicable(
        pgettext(
            'Voucher not applicable',
            'Discount not applicable for this product'))

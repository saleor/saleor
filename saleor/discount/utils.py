from django.conf import settings
from django.db.models import F
from django.utils.encoding import smart_text
from django.utils.translation import pgettext
from prices import FixedDiscount, Price


from ..cart.utils import (
    get_category_variants_and_prices, get_product_variants_and_prices)
from .models import NotApplicable
from . import VoucherApplyToProduct, VoucherType


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


def get_voucher_discount_for_checkout(voucher, checkout):
    if voucher.type == VoucherType.VALUE:
        cart_total = checkout.get_subtotal()
        voucher.validate_limit(cart_total)
        return voucher.get_fixed_discount_for(cart_total)
    if voucher.type == VoucherType.SHIPPING:
        if not checkout.is_shipping_required:
            msg = pgettext(
                'Voucher not applicable',
                'Your order does not require shipping.')
            raise NotApplicable(msg)
        shipping_method = checkout.shipping_method
        if not shipping_method:
            msg = pgettext(
                'Voucher not applicable',
                'Please select a shipping method first.')
            raise NotApplicable(msg)
        if (voucher.apply_to and
                shipping_method.country_code != voucher.apply_to):
            msg = pgettext(
                'Voucher not applicable',
                'This offer is only valid in %(country)s.')
            raise NotApplicable(
                msg % {'country': voucher.get_apply_to_display()})
        cart_total = checkout.get_subtotal()
        voucher.validate_limit(cart_total)
        return voucher.get_fixed_discount_for(shipping_method.price)
    if voucher.type in (VoucherType.PRODUCT, VoucherType.CATEGORY):
        if voucher.type == VoucherType.PRODUCT:
            prices = [
                item[1] for item in get_product_variants_and_prices(
                    checkout.cart, voucher.product)]
        else:
            prices = [
                item[1] for item in get_category_variants_and_prices(
                    checkout.cart, voucher.category)]
        if not prices:
            msg = pgettext(
                'Voucher not applicable',
                'This offer is only valid for selected items.')
            raise NotApplicable(msg)
        if voucher.apply_to == VoucherApplyToProduct.ALL_PRODUCTS:
            discounts = (
                voucher.get_fixed_discount_for(price) for price in prices)
            discount_total = sum(
                (discount.amount for discount in discounts),
                Price(0, currency=settings.DEFAULT_CURRENCY))
            return FixedDiscount(discount_total, smart_text(voucher))
        product_total = sum(
            prices, Price(0, currency=settings.DEFAULT_CURRENCY))
        return voucher.get_fixed_discount_for(product_total)
    raise NotImplementedError('Unknown discount type')


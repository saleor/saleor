from __future__ import unicode_literals
from . import logger

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from satchless.item import InsufficientStock


def contains_unavailable_products(cart):
    try:
        [item.product.check_quantity(item.quantity) for item in cart]
    except InsufficientStock:
        return True
    return False


def remove_unavailable_products(cart):
    for item in cart:
        try:
            cart.add(item.product, quantity=item.quantity, replace=True)
        except InsufficientStock as e:
            quantity = e.item.get_stock_quantity()
            cart.add(item.product, quantity=quantity, replace=True)


def get_product_variants_and_prices(cart, product):
    lines = (cart_line for cart_line in cart
             if cart_line.product.product_id == product.id)
    for line in lines:
        for i in range(line.quantity):
            yield line.product, line.get_price_per_item()


def get_category_variants_and_prices(cart, discounted_category):
    products = set((cart_line.product.product for cart_line in cart))
    discounted_products = []
    for product in products:
        for category in product.categories.all():
            is_descendant = category.is_descendant_of(
                discounted_category, include_self=True)
            if is_descendant:
                discounted_products.append(product)
    for product in discounted_products:
        for line in get_product_variants_and_prices(cart, product):
            yield line


def check_product_availability_and_warn(request, cart):
    if contains_unavailable_products(cart):
        msg = _('Sorry. We don\'t have that many items in stock. '
                'Quantity was set to maximum available for now.')
        messages.warning(request, msg)
        remove_unavailable_products(cart)


def get_user_open_cart_token(user):
    user_carts_tokens = list(
        user.carts.open().values_list('token', flat=True))
    if len(user_carts_tokens) > 1:
        logger.warning('%s has more then one open basket')
        from .models import Cart
        user.carts.open().exclude(token=user_carts_tokens[0]).update(
            status=Cart.CANCELED)
    if user_carts_tokens:
        return user_carts_tokens[0]

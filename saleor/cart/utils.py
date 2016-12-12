from __future__ import unicode_literals

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from satchless.item import InsufficientStock

from ..product.forms import get_form_class_for_product


def contains_unavailable_variants(cart):
    try:
        for line in cart.lines.all():
            line.variant.check_quantity(line.quantity)
    except InsufficientStock:
        return True
    return False


def remove_unavailable_variants(cart):
    for line in cart.lines.all():
        try:
            cart.add(line.variant, quantity=line.quantity, replace=True)
        except InsufficientStock as e:
            quantity = e.item.get_stock_quantity()
            cart.add(line.variant, quantity=quantity, replace=True)


def get_product_variants_and_prices(cart, product):
    lines = (cart_line for cart_line in cart
             if cart_line.variant.product_id == product.id)
    for line in lines:
        for i in range(line.quantity):
            yield line.variant, line.get_price_per_item()


def get_category_variants_and_prices(cart, discounted_category):
    products = set((cart_line.variant.product for cart_line in cart))
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
    if contains_unavailable_variants(cart):
        msg = _('Sorry. We don\'t have that many items in stock. '
                'Quantity was set to maximum available for now.')
        messages.warning(request, msg)
        remove_unavailable_variants(cart)


def process_cart_form(request, cart, product):
    form_class = get_form_class_for_product(product)
    form = form_class(cart=cart, product=product,
                      data=request.POST or None, discounts=request.discounts)
    if form.is_valid():
        form.save()
    return form

from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from ..cart.decorators import get_cart_from_request
from ..core.utils import get_paginator_items, to_local_currency
from .forms import get_form_class_for_product
from .models import Category
from .utils import products_with_details


def product_details(request, slug, product_id):
    """Product details page

    The following variables are available to the template:

    product:
        The Product instance itself.

    is_visible:
        Whether the product is visible to regular users (for cases when an
        admin is previewing a product before publishing).

    form:
        The add-to-cart form.

    price_range:
        The PriceRange for the product including all discounts.

    undiscounted_price_range:
        The PriceRange excluding all discounts.

    discount:
        Either a Price instance equal to the discount value or None if no
        discount was available.

    local_price_range:
        The same PriceRange from price_range represented in user's local
        currency. The value will be None if exchange rate is not available or
        the local currency is the same as site's default currency.
    """
    products = products_with_details(user=request.user)
    product = get_object_or_404(products, id=product_id)
    if product.get_slug() != slug:
        return HttpResponsePermanentRedirect(product.get_absolute_url())
    today = datetime.date.today()
    is_visible = (
        product.available_on is None or product.available_on <= today)
    form_class = get_form_class_for_product(product)
    cart = get_cart_from_request(request)

    # add to cart handling
    form = form_class(cart=cart, product=product,
                      data=request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('cart:index')

    # price handling
    price_range = product.get_price_range(discounts=request.discounts)
    undiscounted_price_range = product.get_price_range()
    if undiscounted_price_range.min_price > price_range.min_price:
        discount = undiscounted_price_range.min_price - price_range.min_price
    else:
        discount = None
    local_price_range = to_local_currency(price_range, request.currency)

    template_name = 'product/details_%s.html' % (
        type(product).__name__.lower(),)
    templates = [template_name, 'product/details.html']
    return TemplateResponse(
        request, templates,
        {
            'discount': discount,
            'form': form,
            'is_visible': is_visible,
            'local_price_range': local_price_range,
            'price_range': price_range,
            'product': product,
            'undiscounted_price_range': undiscounted_price_range})


def category_index(request, path, category_id):
    category = get_object_or_404(Category, id=category_id)
    actual_path = category.get_full_path()
    if actual_path != path:
        return redirect('product:category', permanent=True, path=actual_path,
                        category_id=category_id)
    return TemplateResponse(request, 'category/index.html',
                            {'category': category})

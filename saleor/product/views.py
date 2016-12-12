from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from ..cart.decorators import get_cart_from_request
from ..cart.utils import process_purchase
from ..core.utils import get_paginator_items
from .models import Category
from .utils import (products_with_details, get_availability,
                    products_with_availability, get_product_images)


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
    cart = get_cart_from_request(request)

    form = process_purchase(request, cart, product)
    if form.is_valid():
        return redirect('cart:index')

    availability = get_availability(product, discounts=request.discounts,
                                    local_currency=request.currency)

    template_name = 'product/details_%s.html' % (
        type(product).__name__.lower(),)
    templates = [template_name, 'product/details.html']
    product_images = get_product_images(product)
    return TemplateResponse(
        request, templates,
        {
            'availability': availability,
            'product_images': product_images,
            'form': form,
            'is_visible': is_visible,
            'product': product})


def category_index(request, path, category_id):
    category = get_object_or_404(Category, id=category_id)
    children_categories = category.get_children()
    breadcrumbs = category.get_ancestors(include_self=True)
    actual_path = category.get_full_path()
    if actual_path != path:
        return redirect('product:category', permanent=True, path=actual_path,
                        category_id=category_id)
    products = category.products.get_available_products()
    products = products.prefetch_related(
        'images', 'variants', 'variants__stock')
    products_page = get_paginator_items(
        products, settings.PAGINATE_BY, request.GET.get('page'))
    products = products_with_availability(
        products_page, discounts=request.discounts,
        local_currency=request.currency)
    return TemplateResponse(
        request, 'category/index.html',
        {'products': products, 'category': category,
         'children_categories': children_categories,
         'breadcrumbs': breadcrumbs,
         'products_page': products_page})

from __future__ import unicode_literals


from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from ..cart.core import set_cart_cookie
from ..core.utils import get_paginator_items
from .models import Category
from .utils import (products_with_details,
                    products_with_availability,
                    product_display)


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
    data, templates, _ = product_display(request, product)
    return TemplateResponse(request, templates, data)


def product_add_to_cart(request, slug, product_id):
    if not request.method == 'POST':
        return redirect(reverse(
            'product:details',
            kwargs={'product_id': product_id, 'slug': slug}))

    products = products_with_details(user=request.user)
    product = get_object_or_404(products, pk=product_id)

    data, templates, cart = product_display(request, product,
                                            create_cart=True)
    form = data['form']
    if form.is_valid():
        form.save()
        response = redirect('cart:index')
    else:
        response = TemplateResponse(request, templates, data)
    if not request.user.is_authenticated():
        set_cart_cookie(cart, response)
    return response


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

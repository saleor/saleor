from __future__ import unicode_literals

from django.http import HttpResponsePermanentRedirect
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from .forms import get_form_class_for_product
from .models import Product, Category
from ..core.utils import get_paginator_items

from ..cart.views import get_cart_from_request


def product_details(request, slug, product_id):
    products = Product.objects.get_available_products().select_subclasses()
    products = products.prefetch_related('categories', 'images',
                                         'variants__stock',
                                         'variants__variant_images__image',
                                         'attributes__values')
    product = get_object_or_404(products, id=product_id)
    if product.get_slug() != slug:
        return HttpResponsePermanentRedirect(product.get_absolute_url())
    form_class = get_form_class_for_product(product)
    cart = get_cart_from_request(request)
    form = form_class(cart=cart, product=product,
                      data=request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('cart:index')
    template_name = 'product/details_%s.html' % (
        type(product).__name__.lower(),)
    templates = [template_name, 'product/details.html']
    return TemplateResponse(
        request, templates,
        {'product': product, 'form': form})


def category_index(request, path, category_id):
    category = get_object_or_404(Category, id=category_id)
    children_categories = category.get_children()
    breadcrumbs = category.get_ancestors(include_self=True)
    actual_path = category.get_full_path()
    if actual_path != path:
        return redirect('product:category', permanent=True, path=actual_path,
                        category_id=category_id)
    products = category.products.get_available_products().select_subclasses()
    products = products.prefetch_related(
        'images', 'variants', 'variants__stock')
    products = get_paginator_items(
        products, settings.PAGINATE_BY, request.GET.get('page'))
    return TemplateResponse(
        request, 'category/index.html',
        {'products': products, 'category': category,
         'children_categories': children_categories,
         'breadcrumbs': breadcrumbs})

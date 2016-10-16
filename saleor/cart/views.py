from __future__ import unicode_literals

from itertools import chain

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from babeldjango.templatetags.babel import currencyfmt

from .forms import ReplaceCartLineForm
from .decorators import get_or_create_db_cart, get_or_empty_db_cart
from .utils import check_product_availability_and_warn
from ..product.forms import get_form_class_for_product
from ..product.models import Product, ProductVariant


@get_or_empty_db_cart
def index(request, cart):
    cart_lines = cart.lines.select_related('variant')
    check_product_availability_and_warn(request, cart_lines)
    discounts = request.discounts
    cart_lines = []

    for line in cart:
        initial = {'quantity': line.get_quantity()}
        form = ReplaceCartLineForm(None, cart=cart, variant=line.variant,
                                   initial=initial, discounts=discounts)
        cart_lines.append({
            'variant': line.variant,
            'get_price_per_item': line.get_price_per_item(discounts),
            'get_total': line.get_total(discounts=discounts),
            'form': form})

    cart_total = None
    if cart:
        cart_total = cart.get_total(discounts=discounts)

    return TemplateResponse(
        request, 'cart/index.html',
        {'cart_lines': cart_lines,
         'cart_total': cart_total})


@get_or_create_db_cart
def add_to_cart(request, cart, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form_class = get_form_class_for_product(product)

    form = form_class(
        data=request.POST or None, product=product, cart=cart,
        discounts=request.discounts)
    if form.is_valid():
        form.save()
    else:
        flat_error_list = chain(*form.errors.values())
        for error_msg in flat_error_list:
            messages.error(request, error_msg)
    return redirect('cart:index')


@get_or_empty_db_cart
def update(request, cart, product_id):
    if not request.is_ajax():
        return redirect('cart:index')
    variant = get_object_or_404(ProductVariant, pk=product_id)
    discounts = request.discounts
    status = None
    form = ReplaceCartLineForm(request.POST, cart=cart, variant=variant,
                               discounts=discounts)
    if form.is_valid():
        form.save()
        response = {'productId': product_id,
                    'subtotal': 0,
                    'total': 0}
        updated_line = cart.get_line(form.cart_line.variant)
        if updated_line:
            response['subtotal'] = currencyfmt(
                updated_line.get_total(discounts=discounts).gross,
                updated_line.get_total(discounts=discounts).currency)
        if cart:
            response['total'] = currencyfmt(
                cart.get_total(discounts=discounts).gross,
                cart.get_total(discounts=discounts).currency)
        status = 200
    elif request.POST is not None:
        response = {'error': form.errors}
        status = 400
    return JsonResponse(response, status=status)

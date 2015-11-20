from __future__ import unicode_literals
from babeldjango.templatetags.babel import currencyfmt

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from .forms import ReplaceCartLineForm
from . import Cart
from ..cart.utils import (
    contains_unavailable_products, remove_unavailable_products)


def index(request, product_id=None):
    if product_id is not None:
        product_id = int(product_id)
    cart = Cart.for_session_cart(request.cart, discounts=request.discounts)
    if contains_unavailable_products(cart):
        msg = _('Sorry. We don\'t have that many items in stock. '
                'Quantity was set to maximum available for now.')
        messages.warning(request, msg)
        remove_unavailable_products(cart)
    for line in cart:
        data = None
        if line.product.pk == product_id:
            data = request.POST
        initial = {'quantity': line.get_quantity()}
        form = ReplaceCartLineForm(data, cart=cart, product=line.product,
                                   initial=initial)
        line.form = form
        if form.is_valid():
            form.save()
            if request.is_ajax():
                response = {
                    'productId': line.product.pk,
                    'subtotal': currencyfmt(
                        line.get_total().gross,
                        line.get_total().currency),
                    'total': 0}
                if cart:
                    response['total'] = currencyfmt(
                        cart.get_total().gross, cart.get_total().currency)
                return JsonResponse(response)
            return redirect('cart:index')
        elif data is not None:
            if request.is_ajax():
                response = {'error': form.errors}
                return JsonResponse(response, status=400)
    cart_partitioner = cart.partition()
    return TemplateResponse(
        request, 'cart/index.html', {
            'cart': cart_partitioner})

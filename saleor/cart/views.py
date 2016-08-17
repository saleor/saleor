from __future__ import unicode_literals

from itertools import chain
from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from babeldjango.templatetags.babel import currencyfmt

from .core import set_cart_cookie
from .decorators import get_simple_cart
from .models import Cart
from .forms import ReplaceCartLineForm
from .utils import check_product_availability_and_warn
from ..cart.utils import check_product_availability_and_warn
from ..product.forms import get_form_class_for_product
from ..product.models import Product



def get_or_create_db_cart(view):
    @wraps(view)
    @get_simple_cart
    def func(request, *args, **kwargs):
        user = request.user
        simple_cart = kwargs.pop('simple_cart')
        if user.is_authenticated():
            cart, created = Cart.objects.open().get_or_create(
                token=simple_cart.token, user=user)
        else:
            cart, created = Cart.objects.open().anonymous().get_or_create(
                token=simple_cart.token)
        response = view(request, cart, *args, **kwargs)
        if not user.is_authenticated():
            # save basket for anonymous user
            set_cart_cookie(simple_cart, response)
        return response
    return func


def get_or_empty_db_cart(view):
    @wraps(view)
    @get_simple_cart
    def func(request, *args, **kwargs):
        user = request.user
        simple_cart = kwargs.pop('simple_cart')
        if user.is_authenticated():
            queryset = user.carts
        else:
            queryset = Cart.objects.anonymous()
        try:
            cart = queryset.open().get(token=simple_cart.token)
        except Cart.DoesNotExist:
            cart = Cart()

        cart.discounts = request.discounts

        return view(request, cart, *args, **kwargs)
    return func


@get_or_empty_db_cart
def index(request, cart, product_id=None):
    # todo: fix discounts
    if product_id is not None:
        product_id = int(product_id)

    check_product_availability_and_warn(request, cart)

    discounts = request.discounts
    cartlines = []

    for line in cart:
        data = None
        if line.product.pk == product_id:
            data = request.POST

        initial = {'quantity': line.get_quantity()}

        form = ReplaceCartLineForm(data, cart=cart, product=line.product,
                                   initial=initial, discounts=discounts)


        cartlines.append([line, form])
        if form.is_valid():
            form.save()
            if request.is_ajax():
                response = {
                    'productId': line.product.pk,
                    'subtotal': currencyfmt(
                        line.get_total(discounts=discounts).gross,
                        line.get_total(discounts=discounts).currency),
                    'total': 0}
                if cart:
                    response['total'] = currencyfmt(
                        cart.get_total(discounts=discounts).gross,
                        cart.get_total(discounts=discounts).currency)
                return JsonResponse(response)
            return redirect('cart:index')
        elif data is not None:
            if request.is_ajax():
                response = {'error': form.errors}
                return JsonResponse(response, status=400)
    return TemplateResponse(
        request, 'cart/index.html',
        {'cart': cart, 'cartlines': cartlines, 'discounts': discounts})


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

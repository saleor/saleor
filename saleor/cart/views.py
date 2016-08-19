from __future__ import unicode_literals

from itertools import chain
from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from babeldjango.templatetags.babel import currencyfmt

from .core import set_cart_cookie
from .forms import ReplaceCartLineForm
from .models import Cart
from .utils import check_product_availability_and_warn, get_user_open_cart_token
from ..product.forms import get_form_class_for_product
from ..product.models import Product


def get_new_cart_data(cart_queryset=None):
    cart_queryset = cart_queryset or Cart.objects
    cart = cart_queryset.create()
    cart_data = {
        'token': cart.token,
        'total': cart.total,
        'quantity': cart.quantity,
        'current_quantity': 0}
    return cart_data


def assign_anonymous_cart(view):
    """If user is authenticated, assign cart from current session"""

    @wraps(view)
    def func(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        if request.user.is_authenticated():
            cookie = request.get_signed_cookie(Cart.COOKIE_NAME, default=None)
            if cookie:
                try:
                    cart = Cart.objects.open().get(token=cookie)
                except Cart.DoesNotExist:
                    pass
                else:
                    if cart.user is None:
                        request.user.carts.open().update(status=Cart.CANCELED)
                        cart.user = request.user
                        cart.save(update_fields=['user'])
                response.delete_cookie(Cart.COOKIE_NAME)

        return response
    return func


def get_cart_from_request(request, create=False):
    """Returns Cart object for current user. If create option is True,
    new cart will be saved to db"""

    cookie_token = request.get_signed_cookie(
        Cart.COOKIE_NAME, default=None)

    if request.user.is_authenticated():
        user = request.user
        queryset = user.carts
        token = get_user_open_cart_token(request.user)

    else:
        user = None
        queryset = Cart.objects.anonymous()
        token = cookie_token

    try:
        cart = queryset.open().get(token=token)
    except Cart.DoesNotExist:
        if create:
            cart = Cart.objects.create(
                user=user,
                token=cookie_token)
        else:
            cart = Cart()

    cart.discounts = request.discounts
    return cart


def get_or_create_db_cart(view):
    @wraps(view)
    def func(request, *args, **kwargs):
        cart = get_cart_from_request(request, create=True)

        response = view(request, cart, *args, **kwargs)

        if not request.user.is_authenticated():
            # save basket for anonymous user
            set_cart_cookie(cart, response)
        return response
    return func


def get_or_empty_db_cart(view):
    @wraps(view)
    def func(request, *args, **kwargs):
        cart = get_cart_from_request(request)
        return view(request, cart, *args, **kwargs)
    return func


@get_or_empty_db_cart
def index(request, cart, product_id=None):
    if product_id is not None:
        product_id = int(product_id)

    check_product_availability_and_warn(request, cart)

    discounts = request.discounts
    cart_lines = []

    for line in cart:
        data = None
        if line.product.pk == product_id:
            data = request.POST

        initial = {'quantity': line.get_quantity()}

        form = ReplaceCartLineForm(data, cart=cart, product=line.product,
                                   initial=initial, discounts=discounts)

        if form.is_valid():
            form.save()

            if not request.is_ajax():
                return redirect('cart:index')

            response = {
                'productId': product_id,
                'subtotal': 0,
                'total': 0
            }

            updated_line = cart.get_line(form.cart_line.product)

            if updated_line:
                response['subtotal'] = currencyfmt(
                    updated_line.get_total(discounts=discounts).gross,
                    updated_line.get_total(discounts=discounts).currency)

            if cart:
                response['total'] = currencyfmt(
                    cart.get_total(discounts=discounts).gross,
                    cart.get_total(discounts=discounts).currency)

            return JsonResponse(response)

        elif data is not None:
            if request.is_ajax():
                response = {'error': form.errors}
                return JsonResponse(response, status=400)

        cart_lines.append(
            {
                'product': line.product,
                'get_price_per_item': line.get_price_per_item(discounts),
                'get_total': line.get_total(discounts=discounts),
                'form': form
            }
        )

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

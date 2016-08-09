from __future__ import unicode_literals

from functools import wraps
from itertools import chain

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse

from .core import set_cart_cookie
from ..core.forms import SelectCountryForm
from .forms import CartFormset
from .models import Cart
from ..cart.utils import check_product_availability_and_warn
from ..product.forms import get_form_class_for_product
from ..product.models import Product
from ..shipping.models import ShippingCountryBase
from .forms import ReplaceCartLineForm



def get_or_create_db_cart(view):
    @wraps(view)
    def func(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated():
            cart, created = Cart.objects.open().get_or_create(
                token=request.cart.token, user=user)
        else:
            cart, created = Cart.objects.open().anonymous().get_or_create(
                token=request.cart.token)
        response = view(request, cart, *args, **kwargs)
        if not user.is_authenticated():
            # save basket for anonymous user
            set_cart_cookie(request.cart, response)
        return response
    return func


def get_or_empty_db_cart(view):
    @wraps(view)
    def func(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated():
            queryset = user.carts
        else:
            queryset = Cart.objects.anonymous()
        try:
            cart = queryset.open().get(token=request.cart.token)
        except Cart.DoesNotExist:
            cart = Cart()
        return view(request, cart, *args, **kwargs)
    return func


@get_or_empty_db_cart
def index(request, cart, product_id=None):
    # todo: fix discounts
    # todo: handle updating cartline (remove item, change amount)
    check_product_availability_and_warn(request, cart)
    cart_formset = CartFormset(data=request.POST or None, instance=cart)
    shipping_methods = ShippingCountryBase.objects.select_related(
        'shipping_method', 'shippingcountrystandard',
        'shippingcountryexpress').unique_for_country_code(request.country)

    if product_id is not None:
        product_id = int(product_id)

    if cart_formset.is_valid():
        cart_formset.save()
        return redirect('cart:index')
    select_country_form = SelectCountryForm(initial={
        'country_code': request.country})
    cart_partitioner = cart.partition()
    cart = cart_partitioner
    return TemplateResponse(
        request, 'cart/index.html', {
            'cart': cart, 'cart_formset': cart_formset,
            'discounts': request.discounts,
            'shipping_methods': shipping_methods,
            'select_country_form': select_country_form})


@get_or_create_db_cart
def add_to_cart(request, cart, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form_class = get_form_class_for_product(product)

    form = form_class(
        data=request.POST or None, product=product, cart=cart)
    if form.is_valid():
        form.save()
    else:
        flat_error_list = chain(*form.errors.values())
        for error_msg in flat_error_list:
            messages.error(request, error_msg)
    return redirect('cart:index')

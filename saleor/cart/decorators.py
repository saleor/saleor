from __future__ import unicode_literals

from functools import wraps
from uuid import uuid4


from django.conf import settings
from prices import Price

from .models import Cart, SimpleCart
from .utils import check_product_availability_and_warn, get_user_open_cart_token


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


# todo: move to better place
def recalculate_cart_total(request, cart_token):
    # recalculate total inform user
    cart = Cart.objects.get(token=cart_token)
    check_product_availability_and_warn(request, cart)



def get_simple_cart(view):
    @wraps(view)
    def func(request, *args, **kwargs):
        request_cart = None

        if request.user.is_authenticated():
            cart_token = get_user_open_cart_token(request.user)
            cart_queryset = request.user.carts
        else:
            cart_token = request.get_signed_cookie(
                Cart.COOKIE_NAME, default=None)
            cart_queryset = Cart.objects.anonymous()

        cart_queryset = cart_queryset.open().annotate_current_quantity()

        if cart_token is not None:
            cart_queryset_values = cart_queryset.values(
                'current_quantity', 'token', 'total', 'quantity')
            try:
                cart_data = cart_queryset_values.get(token=cart_token)
            except Cart.DoesNotExist:
                cart_data = get_new_cart_data(cart_queryset)
            else:
                if cart_data['quantity'] != cart_data['current_quantity']:
                    recalculate_cart_total(request, cart_data['token'])
            request_cart = SimpleCart(
                token=cart_data['token'], total=cart_data['total'],
                quantity=cart_data['quantity'])
        else:
            # If we don't get any token cart we don't create cart in DB.
            # We don't want to have baskets created by web crawlers.
            # Cart view will create cart if not exists.
            zero = Price(0, currency=settings.DEFAULT_CURRENCY)
            request_cart = SimpleCart(token=uuid4(), total=zero, quantity=0)


        kwargs['simple_cart'] = request_cart
        return view(request, *args, **kwargs)
    return func


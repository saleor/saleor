from __future__ import unicode_literals
from functools import wraps

from .core import set_cart_cookie
from .models import Cart


def get_user_open_cart_token(user):
    cart = Cart.get_user_open_cart(user)
    if cart is not None:
        return cart.token


def find_and_assign_cart(request):
    """Assign cart from cookie to request user and close """
    cookie = request.get_signed_cookie(Cart.COOKIE_NAME, default=None)
    if cookie:
        cart = Cart.objects.open().filter(token=cookie, user=None).first()
        if cart is not None:
            cart.change_user(request.user)
            carts_to_close = Cart.objects.open().filter(user=request.user)
            carts_to_close = carts_to_close.exclude(token=cookie)
            for to_close in carts_to_close:
                to_close.change_status(Cart.CANCELED)


def get_or_create_anonymous_cart_from_token(cart_queryset, token):
    return cart_queryset.open().filter(token=token).get_or_create(user=None)[0]


def get_or_create_user_cart(cart_queryset, user):
    return cart_queryset.open().get_or_create(user=user)[0]


def get_anonymous_cart_from_token(cart_queryset, token):
    return cart_queryset.open().filter(token=token).filter(user=None).first()


def get_user_cart(cart_queryset, user):
    return cart_queryset.open().filter(user=user).first()


def get_or_create_cart(cart_queryset, request):
    if request.user.is_authenticated():
        return get_or_create_user_cart(cart_queryset, request.user)
    else:
        cookie_token = request.get_signed_cookie(Cart.COOKIE_NAME,
                                                 default=None)
        return get_or_create_anonymous_cart_from_token(cart_queryset,
                                                              cookie_token)


def get_cart(cart_queryset, request):
    """If cart found - take it. If not - return not saved object"""
    if request.user.is_authenticated():
        cart = get_user_cart(cart_queryset, request.user)
    else:
        cookie_token = request.get_signed_cookie(Cart.COOKIE_NAME,
                                                 default=None)
        cart = get_anonymous_cart_from_token(cart_queryset,
                                                    cookie_token)
    if cart is not None:
        return cart
    else:
        return Cart()


def get_or_create_db_cart(cart_queryset=Cart.objects.all()):
    """Use this wrapper only in situations which could create new Cart.
    Example: adding to cart"""
    def get_cart(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            cart = get_or_create_cart(cart_queryset, request)
            response = view(request, cart, *args, **kwargs)
            if not request.user.is_authenticated():
                set_cart_cookie(cart, response)
            return response
        return func
    return get_cart


def get_or_empty_db_cart(cart_queryset=Cart.objects.all()):
    def get_cart(view):
        """Get user cart if exists"""
        @wraps(view)
        def func(request, *args, **kwargs):
            cart = get_cart(cart_queryset, request)
            return view(request, cart, *args, **kwargs)
        return func
    return get_cart

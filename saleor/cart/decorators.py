from __future__ import unicode_literals
from functools import wraps

from .core import set_cart_cookie
from .models import Cart


def get_user_open_cart_token(user):
    cart = Cart.get_user_open_cart(user)
    if cart is not None:
        return cart.token


def find_and_assign_cart(request, response):
    """Assign cart from cookie to request user"""
    cookie = request.get_signed_cookie(Cart.COOKIE_NAME, default=None)
    if cookie:
        cart = Cart.objects.open().filter(token=cookie).first()
        if cart is not None and cart.user is None:
            cart.change_user(request.user)
        response.delete_cookie(Cart.COOKIE_NAME)


def get_cart_from_request(request, cart_queryset=Cart.objects.all(),
                          create=False):
    """Returns Cart object for current user. If create option is True,
    new cart will be saved to db"""
    cookie_token = request.get_signed_cookie(
        Cart.COOKIE_NAME, default=None)

    if request.user.is_authenticated():
        user = request.user
        queryset = cart_queryset.filter(user=user)
        token = get_user_open_cart_token(request.user)
    else:
        user = None
        queryset = cart_queryset.filter(user=None)
        token = cookie_token
    try:
        cart = queryset.open().get(token=token)
    except Cart.DoesNotExist:
        if create:
            cart = Cart.objects.create(user=user, token=token)
        else:
            cart = Cart()

    cart.discounts = request.discounts
    return cart


def get_or_create_db_cart(cart_queryset=Cart.objects.all()):
    def get_cart(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            cart = get_cart_from_request(request, cart_queryset=cart_queryset,
                                         create=True)
            response = view(request, cart, *args, **kwargs)
            if not request.user.is_authenticated():
                # save basket for anonymous user
                set_cart_cookie(cart, response)
            return response
        return func
    return get_cart


def get_or_empty_db_cart(cart_queryset=Cart.objects.all()):
    def get_cart(view):
        """Get user cart if exists"""
        @wraps(view)
        def func(request, *args, **kwargs):
            cart = get_cart_from_request(request, cart_queryset=cart_queryset)
            return view(request, cart, *args, **kwargs)
        return func
    return get_cart


def assign_anonymous_cart(view):
    """After login anonymous session cart will be assigned to user"""
    @wraps(view)
    def func(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        if request.user.is_authenticated():
            find_and_assign_cart(request, response)
        return response
    return func

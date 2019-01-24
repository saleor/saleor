from __future__ import unicode_literals

from datetime import timedelta
from functools import wraps
from uuid import UUID

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core import signing, cache
from django.db import transaction
from django.utils.timezone import now
from django.utils.translation import pgettext_lazy
from satchless.item import InsufficientStock

from saleor.cart.models import Cart
from . import CartStatus
# from .models import Cart

COOKIE_NAME = 'cart'

redis = cache.caches['default']


def set_cart_cookie(simple_cart, response):
    ten_years = timedelta(days=(365 * 10))
    response.set_signed_cookie(
        COOKIE_NAME, simple_cart.token, max_age=ten_years.total_seconds())


def contains_unavailable_variants(cart):
    try:
        for line in cart.lines.all():
            line.variant.check_quantity(line.quantity)
    except InsufficientStock:
        return True
    return False


def token_is_valid(token):
    if token is None:
        return False
    if isinstance(token, UUID):
        return True
    try:
        UUID(token)
    except ValueError:
        return False
    return True


def remove_unavailable_variants(cart):
    for line in cart.lines.all():
        try:
            cart.add(line.variant, quantity=line.quantity, replace=True)
        except InsufficientStock as e:
            quantity = e.item.get_stock_quantity()
            cart.add(line.variant, quantity=quantity, replace=True)


def get_product_variants_and_prices(cart, product):
    lines = (cart_line for cart_line in cart.lines.all()
             if cart_line.variant.product_id == product.id)
    for line in lines:
        for dummy_i in range(line.quantity):
            yield line.variant, line.get_price_per_item()


def get_category_variants_and_prices(cart, discounted_category):
    products = {cart_line.variant.product for cart_line in cart.lines.all()}
    discounted_products = set()
    for product in products:
        for category in product.categories.all():
            is_descendant = category.is_descendant_of(
                discounted_category, include_self=True)
            if is_descendant:
                discounted_products.add(product)
    for product in discounted_products:
        for line in get_product_variants_and_prices(cart, product):
            yield line


def check_product_availability_and_warn(request, cart):
    if contains_unavailable_variants(cart):
        msg = pgettext_lazy(
            'Cart warning message',
            'Sorry. We don\'t have that many items in stock. '
            'Quantity was set to maximum available for now.')
        messages.warning(request, msg)
        remove_unavailable_variants(cart)


def find_and_assign_anonymous_cart(queryset=Cart.objects.all()):
    """Assign cart from cookie to request user
    :type request: django.http.HttpRequest
    """
    def get_cart(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            response = view(request, *args, **kwargs)

            if response.status_code > 399:
                return response

            signed_token = request.META.get('HTTP_X_CART_TOKEN', None)
            token = (
                None
                if not signed_token
                else signing.get_cookie_signer(salt='cart').unsign(signed_token)
            )
            #
            from rest_framework_jwt.serializers import jwt_decode_handler
            from jwt_auth.mixins import jwt_get_user_id_from_payload
            User = get_user_model()
            payload = jwt_decode_handler(response.data.get('token', None))
            user_id = jwt_get_user_id_from_payload(payload)
            user = request.user
            if user_id:
                user = User.objects.get(pk=user_id)

            if not token_is_valid(token):
                return response
            cart = get_anonymous_cart_from_token(
                token=token, cart_queryset=queryset)
            if cart is None:
                return response
            if user.is_authenticated():
                with transaction.atomic():
                    cart.change_user(user)
                    carts_to_close = Cart.objects.open().filter(user=user)
                    carts_to_close = carts_to_close.exclude(token=token)
                    carts_to_close.update(
                        status=CartStatus.CANCELED, last_status_change=now())
                response.delete_cookie(COOKIE_NAME)
            return response

        return func
    return get_cart


def get_anonymous_cart_from_token(token, cart_queryset=Cart.objects.all()):
    """Returns open anonymous cart with given token or None if not found.
    :rtype: Cart | None
    """
    return cart_queryset.open().filter(token=token, user=None).first()


def get_user_cart(user, cart_queryset=Cart.objects.all()):
    """Returns open cart for given user or None if not found.
    :type cart_queryset: saleor.cart.models.CartQueryset
    :type user: User
    :rtype: Cart | None
    """
    return cart_queryset.open().filter(user=user).first()


def get_cart_from_request(request, cart_queryset=Cart.objects.all()):
    """Get cart from database or return unsaved Cart
    :type cart_queryset: saleor.cart.models.CartQueryset
    :type request: django.http.HttpRequest
    :rtype: Cart
    """
    if request.user.is_authenticated():
        cart = get_user_cart(request.user, cart_queryset)
        user = request.user
    else:
        token = request.get_signed_cookie(COOKIE_NAME, default=None)
        cart = get_anonymous_cart_from_token(token, cart_queryset)
        user = None
    if cart is not None:
        return cart
    else:
        return Cart(user=user)


def get_or_create_db_cart(cart_queryset=Cart.objects.all()):
    """Get cart or create if necessary. Example: adding items to cart
    :type cart_queryset: saleor.cart.models.CartQueryset
    """
    def get_cart(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            cart = get_or_create_cart_from_request(request, cart_queryset)
            response = view(request, cart, *args, **kwargs)
            if not request.user.is_authenticated():
                set_cart_cookie(cart, response)
            return response
        return func
    return get_cart


def get_or_empty_db_cart(cart_queryset=Cart.objects.all()):
    """Get cart if exists. Prevents creating empty carts in views which not
    need it
    :type cart_queryset: saleor.cart.models.CartQueryset
    """
    def get_cart(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            cart = get_cart_from_request(request, cart_queryset)
            return view(request, cart, *args, **kwargs)
        return func
    return get_cart

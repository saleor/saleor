from __future__ import unicode_literals
from uuid import uuid4

from django.conf import settings

from prices import Price
from . import logger
from .models import Cart, SimpleCart
from .utils import check_product_availability_and_warn


class CartMiddleware(object):
    """Bind cart to a request and stores it in Django session"""

    def get_user_open_cart_token(self, user):
        user_carts_tokens = list(
            user.carts.open().values_list('token', flat=True))
        if len(user_carts_tokens) > 1:
            logger.warning('%s has more then one open basket')
            user.carts.open().exclude(token=user_carts_tokens[0]).update(
                status=Cart.CANCELED)
        if user_carts_tokens:
            return user_carts_tokens[0]

    def get_new_cart_data(self, cart_queryset=None):
        cart_queryset = cart_queryset or Cart.objects
        cart = cart_queryset.create()
        cart_data = {
            'token': cart.token,
            'total': cart.total,
            'quantity': cart.quantity,
            'current_quantity': 0}
        return cart_data

    def recalculate_cart_total(self, request, cart_token):
        # recalculate total inform user
        cart = Cart.objects.get(token=cart_token)
        check_product_availability_and_warn(request, cart)

    def process_request(self, request):
        if request.user.is_authenticated():
            cart_token = self.get_user_open_cart_token(request.user)
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
                cart_data = self.get_new_cart_data(cart_queryset)
            else:
                if cart_data['quantity'] != cart_data['current_quantity']:
                    self.recalculate_cart_total(request, cart_data['token'])
            request.cart = SimpleCart(
                token=cart_data['token'], total=cart_data['total'],
                quantity=cart_data['quantity'])
        else:
            # If we don't get any token cart we don't create cart in DB.
            # We don't want to have baskets created by web crawlers.
            # Cart view will create cart if not exists.
            zero = Price(0, currency=settings.DEFAULT_CURRENCY)
            request.cart = SimpleCart(token=uuid4(), total=zero, quantity=0)

    def process_response(self, request, response):
        simple_cart = getattr(request, 'cart', None)
        if simple_cart is not None:
            user = request.user
            if user.is_authenticated():
                cart_from_cookie = request.get_signed_cookie(
                    Cart.COOKIE_NAME, default=None)
                # if user just logged in we add his anonymous basket
                if cart_from_cookie:
                    try:
                        cart = Cart.objects.open().get(token=simple_cart.token)
                    except Cart.DoesNotExist:
                        pass
                    else:
                        if cart.user is None:
                            user.carts.open().update(status=Cart.CANCELED)
                            cart.user = user
                            cart.save(update_fields=['user'])
                    response.delete_cookie(Cart.COOKIE_NAME)
        return response

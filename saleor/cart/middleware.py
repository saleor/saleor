from __future__ import unicode_literals

from . import SessionCart, CART_SESSION_KEY


class CartMiddleware(object):
    """Bind cart to a request and stores it in Django session"""
    def process_request(self, request):
        try:
            cart_data = request.session[CART_SESSION_KEY]
            cart = SessionCart.from_storage(cart_data)
        except KeyError:
            cart = SessionCart()
        setattr(request, 'cart', cart)

    def process_response(self, request, response):
        if hasattr(request, 'cart') and request.cart.modified:
            request.cart.modified = False
            to_session = request.cart.for_storage()
            request.session[CART_SESSION_KEY] = to_session
        return response

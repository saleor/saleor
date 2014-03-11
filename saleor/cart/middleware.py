from __future__ import unicode_literals

from . import SessionCart, CART_SESSION_KEY


class CartMiddleware(object):
    '''
    Saves the cart instance into the django session.
    '''

    def process_request(self, request):
        try:
            cart_data = request.session[CART_SESSION_KEY]
            cart = SessionCart.from_storage(cart_data)
        except KeyError:
            cart = SessionCart()
        setattr(request, 'cart', cart)

    def process_response(self, request, response):
        if hasattr(request, 'cart'):
            request.session[CART_SESSION_KEY] = request.cart.for_storage()
        return response

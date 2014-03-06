from __future__ import unicode_literals

from . import SessionCart, CART_SESSION_KEY


class CartMiddleware(object):
    '''
    Saves the cart instance into the django session.
    '''

    def process_request(self, request):
        try:
            cart = request.session[CART_SESSION_KEY]
        except KeyError:
            cart = SessionCart()
            cart = cart.as_data()
        setattr(request, 'cart', cart)

    def process_response(self, request, response):
        if hasattr(request, 'cart'):
            request.session[CART_SESSION_KEY] = request.cart
        return response

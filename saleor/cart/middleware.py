from __future__ import unicode_literals

from . import Cart


class CartMiddleware(object):
    '''
    Saves the cart instance into the django session.
    '''
    SESSION_KEY = 'cart'

    def process_request(self, request):
        try:
            cart = request.session[self.SESSION_KEY]
            cart = Cart.from_json(cart)
        except KeyError:
            cart = Cart()
        setattr(request, 'cart', cart)

    def process_response(self, request, response):
        if hasattr(request, 'cart') and request.cart.modified:
            request.cart.modified = False
            request.session[self.SESSION_KEY] = request.cart.to_json()
        return response

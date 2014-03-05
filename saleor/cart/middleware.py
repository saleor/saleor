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
        except KeyError:
            cart = Cart()
            cart = cart.as_data()
        setattr(request, 'cart', cart)

    def process_response(self, request, response):
        if hasattr(request, 'cart') and request.cart['modified']:
            request.cart['modified'] = False
            request.session[self.SESSION_KEY] = request.cart
        return response

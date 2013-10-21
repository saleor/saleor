from . import Cart


class CartMiddleware(object):
    '''
    Saves the cart instance into the django session.
    '''
    def process_request(self, request):
        try:
            cart = request.session[Cart.SESSION_KEY]
        except KeyError:
            cart = Cart()
            request.session[Cart.SESSION_KEY] = cart
        setattr(request, 'cart', cart)

    def process_response(self, request, response):
        if hasattr(request, 'cart') and request.cart.modified:
            request.cart.modified = False
            request.session[Cart.SESSION_KEY] = request.cart
        return response

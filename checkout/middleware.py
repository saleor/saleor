from checkout import get_checkout_from_request, SESSION_KEY

class CheckoutMiddleware(object):

    def process_response(self, request, response):
        checkout = get_checkout_from_request(request, False)
        if checkout.modified:
            checkout.modified = False
            request.session[SESSION_KEY] = checkout
        return response

import braintree
from braintree.resource import Resource

class UnknownPaymentMethod(Resource):
    def image_url(self):
        return "https://assets.braintreegateway.com/payment_method_logo/unknown.png"

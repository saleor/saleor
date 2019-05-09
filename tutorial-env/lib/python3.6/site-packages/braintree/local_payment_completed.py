from braintree.resource import Resource

class LocalPaymentCompleted(Resource):
    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

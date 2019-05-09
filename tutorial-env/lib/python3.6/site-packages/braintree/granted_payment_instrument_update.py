from braintree.resource import Resource

class GrantedPaymentInstrumentUpdate(Resource):

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        self.payment_method_nonce = attributes["payment_method_nonce"]["nonce"]

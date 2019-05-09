from braintree.resource import Resource

class ConnectedMerchantPayPalStatusChanged(Resource):

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

    @property
    def merchant_id(self):
        return self.merchant_public_id

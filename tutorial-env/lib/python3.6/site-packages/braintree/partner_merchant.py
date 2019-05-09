from braintree.configuration import Configuration
from braintree.resource import Resource

class PartnerMerchant(Resource):

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        if "partner_merchant_id" in attributes:
            self.partner_merchant_id = attributes.pop("partner_merchant_id")
        if "private_key" in attributes:
            self.private_key = attributes.pop("private_key")
        if "public_key" in attributes:
            self.public_key = attributes.pop("public_key")
        if "merchant_public_id" in attributes:
            self.merchant_public_id = attributes.pop("merchant_public_id")
        if "client_side_encryption_key" in attributes:
            self.client_side_encryption_key = attributes.pop("client_side_encryption_key")

    def __repr__(self):
        detail_list = ["partner_merchant_id", "public_key", "merchant_public_id", "client_side_encryption_key"]
        return super(PartnerMerchant, self).__repr__(detail_list)

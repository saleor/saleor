from braintree.resource import Resource

class OAuthAccessRevocation(Resource):
    """
    A class representing an OAuth access revocation.
    """

    def __init__(self, attributes):
        Resource.__init__(self, None, attributes)

import braintree
from braintree.util.datetime_parser import parse_datetime
from braintree.resource import Resource

class AchMandate(Resource):

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

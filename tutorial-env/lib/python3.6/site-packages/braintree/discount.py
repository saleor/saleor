from braintree.modification import Modification
from braintree.configuration import Configuration


class Discount(Modification):

    @staticmethod
    def all():
        return Configuration.gateway().discount.all()

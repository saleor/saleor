from .base import Resource
from ..constants.url import URL
import warnings


class Order(Resource):
    def __init__(self, client=None):
        super(Order, self).__init__(client)
        self.base_url = URL.ORDER_URL

    def fetch_all(self, data={}, **kwargs):  # pragma: no cover
        warnings.warn("Will be Deprecated in next release, use all",
                      DeprecationWarning)
        return self.all(data, **kwargs)

    def all(self, data={}, **kwargs):
        """"
        Fetch all Order entities

        Returns:
            Dictionary of Order data
        """
        return super(Order, self).all(data, **kwargs)

    def fetch(self, order_id, data={}, **kwargs):
        """"
        Fetch Order for given Id

        Args:
            order_id : Id for which order object has to be retrieved

        Returns:
            Order dict for given order Id
        """
        return super(Order, self).fetch(order_id, data, **kwargs)

    def fetch_all_payments(self, order_id, data={}, **kwargs):  # pragma: no cover
        warnings.warn("Will be Deprecated in next release, use payments",
                      DeprecationWarning)
        return self.payments(order_id, data, **kwargs)

    def payments(self, order_id, data={}, **kwargs):
        """"
        Fetch Payment for Order Id

        Args:
            order_id : Id for which payment objects has to be retrieved

        Returns:
            Payment dict for given Order Id
        """
        url = "{}/{}/payments".format(self.base_url, order_id)
        return self.get_url(url, data, **kwargs)

    def create(self, data={}, **kwargs):
        """"
        Create Order from given dict

        Args:
            data : Dictionary having keys using which order have to be created
                'amount' :  Amount of Order
                'currency' : Currency used in Order
                'receipt' : Receipt Id for the order
                'notes' : key value pair as notes
                'payment_capture': 0/1 if payment should be auto captured or not

        Returns:
            Order Dict which was created
        """
        url = self.base_url
        return self.post_url(url, data, **kwargs)

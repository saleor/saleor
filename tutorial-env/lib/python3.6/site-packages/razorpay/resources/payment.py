from .base import Resource
from ..constants.url import URL
import warnings


class Payment(Resource):
    def __init__(self, client=None):
        super(Payment, self).__init__(client)
        self.base_url = URL.PAYMENTS_URL

    def fetch_all(self, data={}, **kwargs):  # pragma: no cover
        warnings.warn("Will be Deprecated in next release, use all",
                      DeprecationWarning)
        return self.all(data, **kwargs)

    def all(self, data={}, **kwargs):
        """"
        Fetch all Payment entities

        Returns:
            Dictionary of Payment data
        """
        return super(Payment, self).all(data, **kwargs)

    def fetch(self, payment_id, data={}, **kwargs):
        """"
        Fetch Payment for given Id

        Args:
            payment_id : Id for which payment object has to be retrieved

        Returns:
            Payment dict for given payment Id
        """
        return super(Payment, self).fetch(payment_id, data, **kwargs)

    def capture(self, payment_id, amount, data={}, **kwargs):
        """"
        Capture Payment for given Id

        Args:
            payment_id : Id for which payment object has to be retrieved
            Amount : Amount for which the payment has to be retrieved

        Returns:
            Payment dict after getting captured
        """
        url = "{}/{}/capture".format(self.base_url, payment_id)
        data['amount'] = amount
        return self.post_url(url, data, **kwargs)

    def refund(self, payment_id, amount, data={}, **kwargs):  # pragma: no cover
        """"
        Refund Payment for given Id

        Args:
            payment_id : Id for which payment object has to be refunded
            Amount : Amount for which the payment has to be refunded

        Returns:
            Payment dict after getting refunded
        """
        url = "{}/{}/refund".format(self.base_url, payment_id)
        data['amount'] = amount
        return self.post_url(url, data, **kwargs)

    def transfer(self, payment_id, data={}, **kwargs):
        """"
        Create Transfer for given Payment Id

        Args:
            payment_id : Id for which payment object has to be transfered

        Returns:
            Payment dict after getting transfered
        """
        url = "{}/{}/transfers".format(self.base_url, payment_id)
        return self.post_url(url, data, **kwargs)

    def transfers(self, payment_id, data={}, **kwargs):
        """"
        Fetches all transfer for given Payment Id

        Args:
            payment_id : Id for which payment object has to be refunded
            Amount : Amount for which the payment has to be refunded

        Returns:
            Payment dict after getting refunded
        """
        url = "{}/{}/transfers".format(self.base_url, payment_id)
        return self.get_url(url, data, **kwargs)

    def bank_transfer(self, payment_id, data={}, **kwargs):
        """"
        Bank Transfer Entity for given Payment

        Args:
            payment_id : Id for which bank transfer entity has to be fetched

        Returns:
            Bank Transfer dict
        """
        url = "{}/{}/bank_transfer".format(self.base_url, payment_id)
        return self.get_url(url, data, **kwargs)

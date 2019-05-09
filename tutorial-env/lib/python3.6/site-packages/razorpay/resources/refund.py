from .base import Resource
from ..constants.url import URL
import warnings


class Refund(Resource):
    def __init__(self, client=None):
        super(Refund, self).__init__(client)
        self.base_url = URL.REFUNDS_URL

    def fetch_all(self, data={}, **kwargs):  # pragma: no cover
        warnings.warn("Will be Deprecated in next release, use all",
                      DeprecationWarning)
        return self.all(data, **kwargs)

    def create(self, data={}, **kwargs):
        """
        Create refund for given payment id
        """
        url = self.base_url
        return self.post_url(url, data, **kwargs)

    def all(self, data={}, **kwargs):
        """"
        Fetch All Refund

        Returns:
            Refund dict
        """
        return super(Refund, self).all(data, **kwargs)

    def fetch(self, refund_id, data={}, **kwargs):
        """"
        Refund object for given paymnet Id

        Args:
            refund_id : Refund Id for which refund has to be retrieved

        Returns:
            Refund dict for given refund Id
        """
        return super(Refund, self).fetch(refund_id, data, **kwargs)

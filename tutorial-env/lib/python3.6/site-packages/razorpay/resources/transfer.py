from .base import Resource
from ..constants.url import URL
import warnings


class Transfer(Resource):
    def __init__(self, client=None):
        super(Transfer, self).__init__(client)
        self.base_url = URL.TRANSFER_URL

    def fetch_all(self, data={}, **kwargs):  # pragma: no cover
        warnings.warn("Will be Deprecated in next release, use all",
                      DeprecationWarning)
        return self.all(data, **kwargs)

    def all(self, data={}, **kwargs):
        """"
        Fetch all Transfer entities

        Returns:
            Dictionary of Transfer data
        """
        if 'payment_id' in data:
            url = "/payments/{}/transfers".format(data['payment_id'])

            del data['payment_id']
            return self.get_url(url, data, **kwargs)

        return super(Transfer, self).all(data, **kwargs)

    def fetch(self, transfer_id, data={}, **kwargs):
        """"
        Fetch Transfer for given Id

        Args:
            transfer_id : Id for which transfer object has to be retrieved

        Returns:
            Transfer dict for given transfer Id
        """
        return super(Transfer, self).fetch(transfer_id, data, **kwargs)

    def create(self, data={}, **kwargs):
        """"
        Create Transfer from given dict

        Args:

        Returns:
            Transfer Dict which was created
        """
        url = self.base_url
        return self.post_url(url, data, **kwargs)

    def edit(self, transfer_id, data={}, **kwargs):
        """"
        Edit Transfer from given id

        Args:
            transfer_id : Id for which transfer object has to be edited

        Returns:
            Transfer Dict which was edited
        """
        url = "{}/{}".format(self.base_url, transfer_id)
        return self.patch_url(url, data, **kwargs)

    def reverse(self, transfer_id, data={}, **kwargs):
        """"
        Reverse Transfer from given id

        Args:
            transfer_id : Id for which transfer object has to be reversed

        Returns:
            Transfer Dict which was reversed
        """
        url = "{}/{}/reversals".format(self.base_url, transfer_id)
        return self.post_url(url, data, **kwargs)

    def reversals(self, transfer_id, data={}, **kwargs):
        """"
        Get all Reversal Transfer from given id

        Args:
            transfer_id :
                Id for which reversal transfer object has to be fetched

        Returns:
            Transfer Dict
        """
        url = "{}/{}/reversals".format(self.base_url, transfer_id)
        return self.get_url(url, data, **kwargs)

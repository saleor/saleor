from .base import Resource
from ..constants.url import URL


class VirtualAccount(Resource):
    def __init__(self, client=None):
        super(VirtualAccount, self).__init__(client)
        self.base_url = URL.VIRTUAL_ACCOUNT_URL

    def all(self, data={}, **kwargs):
        """"
        Fetch all Virtual Account entities

        Returns:
            Dictionary of Virtual Account data
        """
        return super(VirtualAccount, self).all(data, **kwargs)

    def fetch(self, virtual_account_id, data={}, **kwargs):
        """"
        Fetch Virtual Account for given Id

        Args:
            virtual_account_id :
                Id for which Virtual Account object has to be retrieved

        Returns:
            Virtual Account dict for given Virtual Account Id
        """
        return super(VirtualAccount, self).fetch(
            virtual_account_id,
            data,
            **kwargs)

    def create(self, data={}, **kwargs):
        """"
        Create Virtual Account from given dict

        Args:
            Param for Creating Virtual Account

        Returns:
            Virtual Account dict
        """
        url = self.base_url
        return self.post_url(url, data, **kwargs)

    def close(self, virtual_account_id, data={}, **kwargs):
        """"
        Close Virtual Account from given Id

        Args:
            virtual_account_id :
                Id for which Virtual Account objects has to be Closed
        """
        url = "{}/{}".format(self.base_url, virtual_account_id)
        data['status'] = 'closed'
        return self.patch_url(url, data, **kwargs)

    def payments(self, virtual_account_id, data={}, **kwargs):
        """"
        Fetch Payment for Virtual Account Id

        Args:
            virtual_account_id :
                Id for which Virtual Account objects has to be retrieved

        Returns:
            Payment dict for given Virtual Account Id
        """
        url = "{}/{}/payments".format(self.base_url, virtual_account_id)
        return self.get_url(url, data, **kwargs)

from .base import Resource
from ..constants.url import URL


class Token(Resource):
    def __init__(self, client=None):
        super(Token, self).__init__(client)
        self.base_url = URL.CUSTOMER_URL

    def fetch(self, customer_id, token_id, data={}, **kwargs):
        """"
        Fetch Token for given Id and given customer Id

        Args:
            customer_id : Customer Id for which tokens have to be fetched
            token_id    : Id for which TOken object has to be fetched

        Returns:
            Token dict for given token Id
        """
        url = "{}/{}/tokens/{}".format(self.base_url, customer_id, token_id)
        return self.get_url(url, data, **kwargs)

    def all(self, customer_id, data={}, **kwargs):
        """"
        Get all tokens for given customer Id

        Args:
            customer_id : Customer Id for which tokens have to be fetched

        Returns:
            Token dicts for given cutomer Id
        """
        url = "{}/{}/tokens".format(self.base_url, customer_id)
        return self.get_url(url, data, **kwargs)

    def delete(self, customer_id, token_id, data={}, **kwargs):
        """"
        Delete Given Token For a Customer

        Args:
            customer_id : Customer Id for which tokens have to be deleted
            token_id    : Id for which TOken object has to be deleted
        Returns:
            Dict for deleted token
        """
        url = "{}/{}/tokens/{}".format(self.base_url, customer_id, token_id)
        return self.delete_url(url, data, **kwargs)

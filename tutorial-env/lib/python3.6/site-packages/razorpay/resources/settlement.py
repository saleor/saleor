from .base import Resource
from ..constants.url import URL


class Settlement(Resource):
    def __init__(self, client=None):
        super(Settlement, self).__init__(client)
        self.base_url = URL.SETTLEMENT_URL

    def all(self, data={}, **kwargs):
        """"
        Fetch all Settlement entities

        Returns:
            Dictionary of Settlement data
        """
        return super(Settlement, self).all(data, **kwargs)

    def fetch(self, settlement_id, data={}, **kwargs):
        """"
        Fetch Settlement data for given Id

        Args:
            settlement_id : Id for which settlement object has to be retrieved

        Returns:
            settlement dict for given settlement id
        """
        return super(Settlement, self).fetch(settlement_id, data, **kwargs)

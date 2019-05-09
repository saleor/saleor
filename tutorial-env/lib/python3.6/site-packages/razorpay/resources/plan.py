from .base import Resource
from ..constants.url import URL


class Plan(Resource):
    def __init__(self, client=None):
        super(Plan, self).__init__(client)
        self.base_url = URL.PLAN_URL

    def create(self, data={}, **kwargs):
        """"
        Create Plan from given dict

        Args:
            data : Dictionary having keys using which Plan has to be created

        Returns:
            Plan Dict which was created
        """
        url = self.base_url
        return self.post_url(url, data, **kwargs)

    def fetch(self, plan_id, data={}, **kwargs):
        """"
        Fetch Plan for given Id

        Args:
            plan_id : Id for which Plan object has to be retrieved

        Returns:
            Plan dict for given subscription Id
        """
        return super(Plan, self).fetch(plan_id, data, **kwargs)

    def all(self, data={}, **kwargs):
        """"
        Fetch all plan entities

        Returns:
            Dictionary of plan data
        """
        return super(Plan, self).all(data, **kwargs)

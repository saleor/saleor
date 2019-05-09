from .base import Resource
from ..constants.url import URL


class Addon(Resource):
    def __init__(self, client=None):
        super(Addon, self).__init__(client)
        self.base_url = URL.ADDON_URL

    def fetch(self, addon_id, data={}, **kwargs):
        """"
        Fetch addon for given Id

        Args:
            addon_id : Id for which addon object has to be retrieved

        Returns:
            addon dict for given subscription Id
        """
        return super(Addon, self).fetch(addon_id, data, **kwargs)

    def delete(self, addon_id, data={}, **kwargs):
        """
        Delete addon for given id

        Args:
            addon_id : Id for which addon object has to be deleted
        """
        return super(Addon, self).delete(addon_id, data, **kwargs)

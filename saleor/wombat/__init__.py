from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import requests
import logging

logger = logging.getLogger('wombat')


class WombatClient(object):
    endpoint = 'https://push.wombat.co'

    def __init__(self):
        try:
            store_id = settings.WOMBAT_STORE_ID
            access_token = settings.WOMBAT_ACCESS_TOKEN
        except AttributeError:
            raise ImproperlyConfigured(
                'Wombat client requires '
                'WOMBAT_STORE_ID and WOMBAT_ACCESS_TOKEN settings'
            )
        else:
            self.store_id = store_id
            self.access_token = access_token

    def push(self, payload):
        auth_headers = {
            'X-Hub-Store': self.store_id,
            'X-Hub-Access-Token': self.access_token
        }
        return requests.post(self.endpoint, headers=auth_headers, data=payload)



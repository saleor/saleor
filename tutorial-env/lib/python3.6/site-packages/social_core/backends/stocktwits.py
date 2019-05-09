"""
Stocktwits OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/stocktwits.html
"""
from .oauth import BaseOAuth2


class StocktwitsOAuth2(BaseOAuth2):
    """Stockwiths OAuth2 backend"""
    name = 'stocktwits'
    AUTHORIZATION_URL = 'https://api.stocktwits.com/api/2/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.stocktwits.com/api/2/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ','
    DEFAULT_SCOPE = ['read', 'publish_messages', 'publish_watch_lists',
                     'follow_users', 'follow_stocks']

    def get_user_id(self, details, response):
        return response['user']['id']

    def get_user_details(self, response):
        """Return user details from Stocktwits account"""
        fullname, first_name, last_name = self.get_user_names(
            response['user']['name']
        )
        return {'username': response['user']['username'],
                'email': '',  # not supplied
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://api.stocktwits.com/api/2/account/verify.json',
            params={'access_token': access_token}
        )

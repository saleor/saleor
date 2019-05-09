"""
Yammer OAuth2 production and staging backends, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/yammer.html
"""
from .oauth import BaseOAuth2


class YammerOAuth2(BaseOAuth2):
    name = 'yammer'
    AUTHORIZATION_URL = 'https://www.yammer.com/dialog/oauth'
    ACCESS_TOKEN_URL = 'https://www.yammer.com/oauth2/access_token'
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires'),
        ('mugshot_url', 'mugshot_url')
    ]

    def get_user_id(self, details, response):
        return response['user']['id']

    def get_user_details(self, response):
        username = response['user']['name']
        fullname, first_name, last_name = self.get_user_names(
            fullname=response['user']['full_name'],
            first_name=response['user']['first_name'],
            last_name=response['user']['last_name']
        )
        email = response['user']['contact']['email_addresses'][0]['address']
        mugshot_url = response['user']['mugshot_url']
        return {
            'username': username,
            'email': email,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
            'picture_url': mugshot_url
        }


class YammerStagingOAuth2(YammerOAuth2):
    name = 'yammer-staging'
    AUTHORIZATION_URL = 'https://www.staging.yammer.com/dialog/oauth'
    ACCESS_TOKEN_URL = 'https://www.staging.yammer.com/oauth2/access_token'
    REQUEST_TOKEN_URL = 'https://www.staging.yammer.com/oauth2/request_token'

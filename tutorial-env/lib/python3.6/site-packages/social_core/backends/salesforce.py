from six.moves.urllib_parse import urlencode

from .oauth import BaseOAuth2


class SalesforceOAuth2(BaseOAuth2):
    """Salesforce OAuth2 authentication backend"""
    name = 'salesforce-oauth2'
    AUTHORIZATION_URL = \
        'https://login.salesforce.com/services/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://login.salesforce.com/services/oauth2/token'
    REVOKE_TOKEN_URL = 'https://login.salesforce.com/services/oauth2/revoke'
    ACCESS_TOKEN_METHOD = 'POST'
    REFRESH_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ' '
    EXTRA_DATA = [
        ('id', 'id'),
        ('instance_url', 'instance_url'),
        ('issued_at', 'issued_at'),
        ('signature', 'signature'),
        ('refresh_token', 'refresh_token'),
    ]

    def get_user_details(self, response):
        """Return user details from a Salesforce account"""
        return {
            'username': response.get('username'),
            'email': response.get('email') or '',
            'first_name': response.get('first_name'),
            'last_name': response.get('last_name'),
            'fullname': response.get('display_name')
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        user_id_url = kwargs.get('response').get('id')
        url = user_id_url + '?' + urlencode({'access_token': access_token})
        try:
            return self.get_json(url)
        except ValueError:
            return None


class SalesforceOAuth2Sandbox(SalesforceOAuth2):
    """Salesforce OAuth2 authentication testing backend"""
    name = 'salesforce-oauth2-sandbox'
    AUTHORIZATION_URL = 'https://test.salesforce.com/services/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://test.salesforce.com/services/oauth2/token'
    REVOKE_TOKEN_URL = 'https://test.salesforce.com/services/oauth2/revoke'

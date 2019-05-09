"""
Phabricator OAuth2 backend, docs at:
    https://secure.phabricator.com/book/phabcontrib/article/using_oauthserver/
"""
from .oauth import BaseOAuth2


class PhabricatorOAuth2(BaseOAuth2):
    """Phabricator OAuth authentication backend"""
    name = 'phabricator'
    API_URL = 'https://secure.phabricator.com'
    AUTHORIZATION_URL = 'https://secure.phabricator.com/oauthserver/auth/'
    ACCESS_TOKEN_URL = 'https://secure.phabricator.com/oauthserver/token/'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def api_url(self, path):
        api_url = self.setting('API_URL') or self.API_URL
        return '{0}{1}'.format(api_url.rstrip('/'), path)

    def authorization_url(self):
        return self.api_url('/oauthserver/auth/')

    def access_token_url(self):
        return self.api_url('/oauthserver/token/')

    def get_user_details(self, response):
        """Return user details from Phabricator"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('realName')
        )

        return {
            'id': response.get('phid'),
            'username': response.get('userName'),
            'email': response.get('primaryEmail', ''),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from API"""
        return self.get_json(self.api_url('/api/user.whoami'), params={
            'access_token': access_token,
        })

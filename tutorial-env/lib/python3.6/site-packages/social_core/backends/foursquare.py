"""
Foursquare OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/foursquare.html
"""
from .oauth import BaseOAuth2


class FoursquareOAuth2(BaseOAuth2):
    name = 'foursquare'
    AUTHORIZATION_URL = 'https://foursquare.com/oauth2/authenticate'
    ACCESS_TOKEN_URL = 'https://foursquare.com/oauth2/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    API_VERSION = '20140128'

    def get_user_id(self, details, response):
        return response['response']['user']['id']

    def get_user_details(self, response):
        """Return user details from Foursquare account"""
        info = response['response']['user']
        email = info['contact']['email']
        fullname, first_name, last_name = self.get_user_names(
            first_name=info.get('firstName', ''),
            last_name=info.get('lastName', '')
        )
        return {'username': first_name + ' ' + last_name,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://api.foursquare.com/v2/users/self',
                             params={'oauth_token': access_token,
                                     'v': self.API_VERSION})

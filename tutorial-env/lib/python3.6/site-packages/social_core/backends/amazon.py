"""
Amazon OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/amazon.html
"""
import ssl

from .oauth import BaseOAuth2


class AmazonOAuth2(BaseOAuth2):
    name = 'amazon'
    ID_KEY = 'user_id'
    AUTHORIZATION_URL = 'https://www.amazon.com/ap/oa'
    ACCESS_TOKEN_URL = 'https://api.amazon.com/auth/o2/token'
    DEFAULT_SCOPE = ['profile']
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'
    SSL_PROTOCOL = ssl.PROTOCOL_TLSv1
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('user_id', 'user_id'),
        ('postal_code', 'postal_code')
    ]

    def get_user_details(self, response):
        """Return user details from amazon account"""
        name = response.get('name') or ''
        fullname, first_name, last_name = self.get_user_names(name)
        return {'username': name,
                'email': response.get('email'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Grab user profile information from amazon."""
        response = self.get_json('https://www.amazon.com/ap/user/profile',
                                 params={'access_token': access_token})
        if 'Profile' in response:
            response = {
                'user_id': response['Profile']['CustomerId'],
                'name': response['Profile']['Name'],
                'email': response['Profile']['PrimaryEmail']
            }
        return response

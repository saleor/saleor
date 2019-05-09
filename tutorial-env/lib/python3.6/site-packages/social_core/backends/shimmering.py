"""
Shimmering Oauth
"""
from .oauth import BaseOAuth2


class ShimmeringOAuth2(BaseOAuth2):
    """Shimmering Verify OAuth2 authentication backend"""
    name = 'shimmering'
    ID_KEY = 'id'
    AUTHORIZATION_URL = 'http://developers.shimmeringverify.com/o/authorize/'
    ACCESS_TOKEN_URL = 'http://developers.shimmeringverify.com/o/token/'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_details(self, response):
        """Return user details from Shimmering"""
        first_name = response.get('first_name')
        last_name = response.get('last_name')
        email = response.get('email')
        username = response.get('username')
        fullname = '{} {}'.format(first_name, last_name)
        return {
            'username': username,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        headers = {'Authorization': 'Bearer %s' % access_token}
        return self.get_json(
            'http://developers.shimmeringverify.com/user_info/',
            headers=headers
        )

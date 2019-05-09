"""
ArcGIS OAuth2 backend
"""
from .oauth import BaseOAuth2


class ArcGISOAuth2(BaseOAuth2):
    name = 'arcgis'
    ID_KEY = 'username'
    AUTHORIZATION_URL = 'https://www.arcgis.com/sharing/rest/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://www.arcgis.com/sharing/rest/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('expires_in', 'expires_in')
    ]

    def get_user_details(self, response):
        """Return user details from ArcGIS account"""
        return {'username': response.get('username'),
                'email': response.get('email'),
                'fullname': response.get('fullName'),
                'first_name': response.get('firstName'),
                'last_name': response.get('lastName')}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://www.arcgis.com/sharing/rest/community/self',
            params={
                'token': access_token,
                'f': 'json'
            }
        )

"""
Coursera OAuth2 backend, docs at:
    https://tech.coursera.org/app-platform/oauth2/
"""
from .oauth import BaseOAuth2


class CourseraOAuth2(BaseOAuth2):
    """Coursera OAuth2 authentication backend"""
    name = 'coursera'
    ID_KEY = 'username'
    AUTHORIZATION_URL = 'https://accounts.coursera.org/oauth2/v1/auth'
    ACCESS_TOKEN_URL = 'https://accounts.coursera.org/oauth2/v1/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    SCOPE_SEPARATOR = ','
    DEFAULT_SCOPE = ['view_profile']

    def _get_username_from_response(self, response):
        elements = response.get('elements', [])
        for element in elements:
            if 'id' in element:
                return element.get('id')

        return None

    def get_user_details(self, response):
        """Return user details from Coursera account"""
        return {'username': self._get_username_from_response(response)}

    def get_user_id(self, details, response):
        """Return a username prepared in get_user_details as uid"""
        return details.get(self.ID_KEY)

    def user_data(self, access_token, *args, **kwargs):
        """Load user data from the service"""
        return self.get_json(
            'https://api.coursera.org/api/externalBasicProfiles.v1?q=me',
            headers=self.get_auth_header(access_token)
        )

    def get_auth_header(self, access_token):
        return {'Authorization': 'Bearer {0}'.format(access_token)}

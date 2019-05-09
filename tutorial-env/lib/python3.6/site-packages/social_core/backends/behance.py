"""
Behance OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/behance.html
"""
from .oauth import BaseOAuth2


class BehanceOAuth2(BaseOAuth2):
    """Behance OAuth authentication backend"""
    name = 'behance'
    AUTHORIZATION_URL = 'https://www.behance.net/v2/oauth/authenticate'
    ACCESS_TOKEN_URL = 'https://www.behance.net/v2/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = '|'
    EXTRA_DATA = [('username', 'username')]
    REDIRECT_STATE = False

    def get_user_id(self, details, response):
        return response['user']['id']

    def get_user_details(self, response):
        """Return user details from Behance account"""
        user = response['user']
        fullname, first_name, last_name = self.get_user_names(
            user['display_name'], user['first_name'], user['last_name']
        )
        return {'username': user['username'],
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': ''}

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        # Pull up the embedded user attributes so they can be found as extra
        # data. See the example token response for possible attributes:
        # http://www.behance.net/dev/authentication#step-by-step
        data = response.copy()
        data.update(response['user'])
        return super(BehanceOAuth2, self).extra_data(user, uid, data, details,
                                                     *args, **kwargs)

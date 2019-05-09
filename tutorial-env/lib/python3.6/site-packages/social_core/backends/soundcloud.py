"""
Soundcloud OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/soundcloud.html
"""
from six.moves.urllib_parse import urlencode

from .oauth import BaseOAuth2


class SoundcloudOAuth2(BaseOAuth2):
    """Soundcloud OAuth authentication backend"""
    name = 'soundcloud'
    AUTHORIZATION_URL = 'https://soundcloud.com/connect'
    ACCESS_TOKEN_URL = 'https://api.soundcloud.com/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ','
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('id', 'id'),
        ('refresh_token', 'refresh_token'),
        ('expires', 'expires')
    ]

    def get_user_details(self, response):
        """Return user details from Soundcloud account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('full_name')
        )
        return {'username': response.get('username'),
                'email': response.get('email') or '',
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://api.soundcloud.com/me.json',
                             params={'oauth_token': access_token})

    def auth_url(self):
        """Return redirect url"""
        state = None
        if self.STATE_PARAMETER or self.REDIRECT_STATE:
            # Store state in session for further request validation. The state
            # value is passed as state parameter (as specified in OAuth2 spec),
            # but also added to redirect_uri, that way we can still verify the
            # request if the provider doesn't implement the state parameter.
            # Reuse token if any.
            name = self.name + '_state'
            state = self.strategy.session_get(name) or self.state_token()
            self.strategy.session_set(name, state)

        params = self.auth_params(state)
        params.update(self.get_scope_argument())
        params.update(self.auth_extra_arguments())
        return self.AUTHORIZATION_URL + '?' + urlencode(params)

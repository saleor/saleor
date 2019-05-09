"""
Strava OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/strava.html
"""
from .oauth import BaseOAuth2


class StravaOAuth(BaseOAuth2):
    name = 'strava'
    AUTHORIZATION_URL = 'https://www.strava.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.strava.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    # Strava doesn't check for parameters in redirect_uri and directly appends
    # the auth parameters to it, ending with an URL like:
    # http://example.com/complete/strava?redirect_state=xxx?code=xxx&state=xxx
    # Check issue #259 for details.
    REDIRECT_STATE = False
    REVOKE_TOKEN_URL = 'https://www.strava.com/oauth/deauthorize'

    def get_user_id(self, details, response):
        return response['athlete']['id']

    def get_user_details(self, response):
        """Return user details from Strava account"""
        # because there is no usernames on strava
        username = response['athlete']['id']
        email = response['athlete'].get('email', '')
        fullname, first_name, last_name = self.get_user_names(
            first_name=response['athlete'].get('firstname', ''),
            last_name=response['athlete'].get('lastname', ''),
        )
        return {'username': str(username),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://www.strava.com/api/v3/athlete',
                             params={'access_token': access_token})

    def revoke_token_params(self, token, uid):
        params = super(StravaOAuth, self).revoke_token_params(token, uid)
        params['access_token'] = token
        return params

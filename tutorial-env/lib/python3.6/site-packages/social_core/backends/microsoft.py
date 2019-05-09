import time

from jwt import DecodeError, ExpiredSignature

from ..exceptions import AuthTokenError
from .oauth import BaseOAuth2

"""
OAuth2 Backend to work with microsoft graph.
"""


class MicrosoftOAuth2(BaseOAuth2):
    name = 'microsoft-graph'
    SCOPE_SEPARATOR = ' '
    AUTHORIZATION_URL = \
        'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
    ACCESS_TOKEN_URL = \
        'https://login.microsoftonline.com/common/oauth2/v2.0/token'

    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    DEFAULT_SCOPE = ['User.Read']

    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        state = self.validate_state()

        response = self.request_access_token(
            self.access_token_url(),
            data=self.auth_complete_params(state),
            headers=self.auth_headers(),
            auth=self.auth_complete_credentials(),
            method=self.ACCESS_TOKEN_METHOD
        )

        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)

    def get_user_id(self, details, response):
        """Use user account id as unique id"""
        return response.get('id')

    def get_user_details(self, response):
        """Return user details from Microsoft online account"""
        email = response.get('mail')
        username = response.get('userPrincipalName')

        if '@' in username:
            if not email:
                email = username
            username = username.split('@', 1)[0]

        return {'username': username,
                'email': email,
                'fullname': response.get('displayName', ''),
                'first_name': response.get('givenName', ''),
                'last_name': response.get('surname', '')}

    def user_data(self, access_token, *args, **kwargs):
        """Return user data by querying Microsoft service"""
        try:
            return self.get_json(
                'https://graph.microsoft.com/v1.0/me',
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                    'Authorization': 'Bearer ' + access_token
                },
                method='GET'
            )
        except (DecodeError, ExpiredSignature) as error:
            raise AuthTokenError(self, error)

    def get_auth_token(self, user_id):
        """Return the access token for the given user, after ensuring that it
        has not expired, or refreshing it if so."""
        user = self.get_user(user_id=user_id)
        access_token = user.social_user.access_token
        expires_on = user.social_user.extra_data['expires_on']
        if expires_on <= int(time.time()):
            new_token_response = self.refresh_token(token=access_token)
            access_token = new_token_response['access_token']
        return access_token

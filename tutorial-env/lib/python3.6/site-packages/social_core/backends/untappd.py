import requests

from .oauth import BaseOAuth2
from ..exceptions import AuthFailed
from ..utils import handle_http_errors


class UntappdOAuth2(BaseOAuth2):
    """Untappd OAuth2 authentication backend"""
    name = 'untappd'
    AUTHORIZATION_URL = 'https://untappd.com/oauth/authenticate/'
    ACCESS_TOKEN_URL = 'https://untappd.com/oauth/authorize/'
    BASE_API_URL = 'https://api.untappd.com'
    USER_INFO_URL = BASE_API_URL + '/v4/user/info/'
    ACCESS_TOKEN_METHOD = 'GET'
    STATE_PARAMETER = False
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('id', 'id'),
        ('bio', 'bio'),
        ('date_joined', 'date_joined'),
        ('location', 'location'),
        ('url', 'url'),
        ('user_avatar', 'user_avatar'),
        ('user_avatar_hd', 'user_avatar_hd'),
        ('user_cover_photo', 'user_cover_photo')
    ]

    def auth_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        params = {
            'client_id': client_id,
            'redirect_url': self.get_redirect_uri(),
            'response_type': self.RESPONSE_TYPE
        }
        return params

    def process_error(self, data):
        """
        All errors from Untappd are contained in the 'meta' key of the
        response.
        """
        response_code = data.get('meta', {}).get('http_code')
        if response_code is not None and response_code != requests.codes.ok:
            raise AuthFailed(self, data['meta']['error_detail'])

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        client_id, client_secret = self.get_key_and_secret()
        code = self.data.get('code')

        self.process_error(self.data)

        # Untapped sends the access token request with URL parameters,
        # not a body
        response = self.request_access_token(
            self.access_token_url(),
            method=self.ACCESS_TOKEN_METHOD,
            params={
                'response_type': 'code',
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_url': self.get_redirect_uri()
            }
        )

        self.process_error(response)

        # Both the access_token and the rest of the response are
        # buried in the 'response' key
        return self.do_auth(
            response['response']['access_token'],
            response=response['response'],
            *args, **kwargs
        )

    def get_user_details(self, response):
        """Return user details from an Untappd account"""
        # Start with the user data as it was returned
        user_data = response['user']

        # Make a few updates to match expected key names
        user_data.update({
            'username': user_data.get('user_name'),
            'email': user_data.get('settings', {}).get('email_address', ''),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'fullname': user_data.get('first_name') + ' ' +
                        user_data.get('last_name')
        })
        return user_data

    def get_user_id(self, details, response):
        """
        Return a unique ID for the current user, by default from
        server response.
        """
        return response['user'].get(self.ID_KEY)

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        response = self.get_json(self.USER_INFO_URL, params={
            'access_token': access_token,
            'compact': 'true'
        })
        self.process_error(response)

        # The response data is buried in the 'response' key
        return response['response']

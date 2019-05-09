"""
Bungie OAuth2 backend
"""
import requests

from social_core.backends.oauth import BaseOAuth2


class BungieOAuth2(BaseOAuth2):
    name = 'bungie'
    ID_KEY = 'membership_id'
    AUTHORIZATION_URL = 'https://www.bungie.net/en/oauth/authorize/'
    ACCESS_TOKEN_URL = 'https://www.bungie.net/platform/app/oauth/token/'
    REFRESH_TOKEN_URL = 'https://www.bungie.net/platform/app/oauth/token/'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('access_token', 'access_token', True),
        ('expires_in', 'expires'),
        ('membership_id', 'membership_id'),
        ('refresh_expires_in', 'refresh_expires_in')
    ]

    def auth_html(self):
        """Abstract Method Inclusion"""
        pass

    def auth_headers(self):
        """Adds X-API-KEY and Origin"""
        return {
            'X-API-KEY': self.setting('API_KEY'),
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.setting('ORIGIN'),
            'Accept': 'application/json'
        }

    def make_bungie_request(self, url, access_token, kwargs):
        """Helper function to get username data keyed off displayName"""
        headers = self.auth_headers()
        headers['Authorization'] = 'Bearer ' + access_token
        return self.get_json(url, headers=headers)

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
        return self.do_auth(response['access_token'],
                            response=response,
                            *args, **kwargs)

    def do_auth(self, access_token, *args, **kwargs):
        """Finish the auth process once the access_token was retrieved"""
        data = self.user_data(access_token, *args, **kwargs)
        response = kwargs.get('response') or {}
        response.update(data or {})
        if 'access_token' not in response:
            response['Response']['access_token']['value'] = access_token
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def user_data(self, access_token, *args, **kwargs):
        """Grab user profile information from Bunige"""
        membership_id = kwargs['response']['membership_id']
        url = 'https://www.bungie.net/Platform/User/GetBungieNetUser/'
        response = self.make_bungie_request(url, access_token, kwargs)
        username = response['Response']['user']['displayName']
        return {'username': username,
                'uid': membership_id}

    def get_user_details(self, response, *args, **kwargs):
        """Return user details from Bungie account"""
        username = response['username']
        return {
            'first_name': username,
            'username': username,
            'uid': response['uid'],
        }

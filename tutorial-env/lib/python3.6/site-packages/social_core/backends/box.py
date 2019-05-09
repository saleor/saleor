"""
Box.net OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/box.html
"""
from .oauth import BaseOAuth2


class BoxOAuth2(BaseOAuth2):
    """Box.net OAuth authentication backend"""
    name = 'box'
    AUTHORIZATION_URL = 'https://www.box.com/api/oauth2/authorize'
    ACCESS_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = 'https://www.box.com/api/oauth2/token'
    REVOKE_TOKEN_URL = 'https://www.box.com/api/oauth2/revoke'
    SCOPE_SEPARATOR = ','
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('id', 'id'),
        ('expires', 'expires'),
    ]

    def do_auth(self, access_token, response=None, *args, **kwargs):
        response = response or {}
        data = self.user_data(access_token)

        data['access_token'] = response.get('access_token')
        data['refresh_token'] = response.get('refresh_token')
        data['expires'] = response.get('expires_in')
        kwargs.update({'backend': self, 'response': data})
        return self.strategy.authenticate(*args, **kwargs)

    def get_user_details(self, response):
        """Return user details Box.net account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name')
        )
        return {'username': response.get('login'),
                'email': response.get('login') or '',
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        params = self.setting('PROFILE_EXTRA_PARAMS', {})
        params['access_token'] = access_token
        return self.get_json('https://api.box.com/2.0/users/me',
                             params=params)

    def refresh_token(self, token, *args, **kwargs):
        params = self.refresh_token_params(token, *args, **kwargs)
        request = self.request(self.REFRESH_TOKEN_URL or self.ACCESS_TOKEN_URL,
                               data=params, headers=self.auth_headers(),
                               method='POST')
        return self.process_refresh_token_response(request, *args, **kwargs)

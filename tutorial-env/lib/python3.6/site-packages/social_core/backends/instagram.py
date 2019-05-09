"""
Instagram OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/instagram.html
"""
import hmac

from hashlib import sha256

from .oauth import BaseOAuth2


class InstagramOAuth2(BaseOAuth2):
    name = 'instagram'
    AUTHORIZATION_URL = 'https://api.instagram.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.instagram.com/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_id(self, details, response):
        # Sometimes Instagram returns 'user', sometimes 'data', but API docs
        # says 'data' http://instagram.com/developer/endpoints/users/#get_users
        user = response.get('user') or response.get('data') or {}
        return user.get('id')

    def get_user_details(self, response):
        """Return user details from Instagram account"""
        # Sometimes Instagram returns 'user', sometimes 'data', but API docs
        # says 'data' http://instagram.com/developer/endpoints/users/#get_users
        user = response.get('user') or response.get('data') or {}
        username = user['username']
        email = user.get('email', '')
        fullname, first_name, last_name = self.get_user_names(
            user.get('full_name', '')
        )
        return {'username': username,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        key, secret = self.get_key_and_secret()
        params = {'access_token': access_token}
        sig = self._generate_sig("/users/self", params, secret)
        params['sig'] = sig
        return self.get_json('https://api.instagram.com/v1/users/self',
                             params=params)

    def _generate_sig(self, endpoint, params, secret):
        sig = endpoint
        for key in sorted(params.keys()):
            sig += '|%s=%s' % (key, params[key])
        return hmac.new(secret.encode(), sig.encode(), sha256).hexdigest()

import hashlib

from ..utils import handle_http_errors
from .base import BaseAuth


class LastFmAuth(BaseAuth):
    """
    Last.Fm authentication backend. Requires two settings:
        SOCIAL_AUTH_LASTFM_KEY
        SOCIAL_AUTH_LASTFM_SECRET

    Don't forget to set the Last.fm callback to something sensible like
        http://your.site/lastfm/complete
    """
    name = 'lastfm'
    AUTH_URL = 'http://www.last.fm/api/auth/?api_key={api_key}'
    EXTRA_DATA = [
        ('key', 'session_key')
    ]

    def auth_url(self):
        return self.AUTH_URL.format(api_key=self.setting('KEY'))

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        key, secret = self.get_key_and_secret()
        token = self.data['token']

        signature = hashlib.md5(''.join(
            ('api_key', key, 'methodauth.getSession', 'token', token, secret)
        ).encode()).hexdigest()

        response = self.get_json('http://ws.audioscrobbler.com/2.0/', data={
            'method': 'auth.getSession',
            'api_key': key,
            'token': token,
            'api_sig': signature,
            'format': 'json'
        }, method='POST')

        kwargs.update({'response': response['session'], 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def get_user_id(self, details, response):
        """Return a unique ID for the current user, by default from server
        response."""
        return response.get('name')

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(response['name'])
        return {
            'username': response['name'],
            'email': '',
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

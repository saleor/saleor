"""
Google App Engine support using User API
"""
from __future__ import absolute_import

from google.appengine.api import users

from .base import BaseAuth
from ..exceptions import AuthException


class GoogleAppEngineAuth(BaseAuth):
    """GoogleAppengine authentication backend"""
    name = 'google-appengine'

    def get_user_id(self, details, response):
        """Return current user id."""
        user = users.get_current_user()
        if user:
            return user.user_id()

    def get_user_details(self, response):
        """Return user basic information (id and email only)."""
        user = users.get_current_user()
        return {'username': user.user_id(),
                'email': user.email(),
                'fullname': '',
                'first_name': '',
                'last_name': ''}

    def auth_url(self):
        """Build and return complete URL."""
        return users.create_login_url(self.redirect_uri)

    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance."""
        if not users.get_current_user():
            raise AuthException('Authentication error')
        kwargs.update({'response': '', 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

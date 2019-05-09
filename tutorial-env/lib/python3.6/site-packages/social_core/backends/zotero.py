"""
Zotero OAuth1 backends, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/zotero.html
"""
from .oauth import BaseOAuth1


class ZoteroOAuth(BaseOAuth1):

    """Zotero OAuth authorization mechanism"""
    name = 'zotero'
    AUTHORIZATION_URL = 'https://www.zotero.org/oauth/authorize'
    REQUEST_TOKEN_URL = 'https://www.zotero.org/oauth/request'
    ACCESS_TOKEN_URL = 'https://www.zotero.org/oauth/access'

    def get_user_id(self, details, response):
        """
        Return user unique id provided by service. For Ubuntu One
        the nickname should be original.
        """
        return details['userID']

    def get_user_details(self, response):
        """Return user details from Zotero API account"""
        access_token = response.get('access_token', {})
        return {
            'username': access_token.get('username', ''),
            'userID': access_token.get('userID', '')
        }

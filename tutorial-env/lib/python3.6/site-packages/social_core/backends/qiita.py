"""
Qiita OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/qiita.html
    http://qiita.com/api/v2/docs#get-apiv2oauthauthorize
"""
import json

from .oauth import BaseOAuth2


class QiitaOAuth2(BaseOAuth2):
    """Qiita OAuth authentication backend"""
    name = 'qiita'

    AUTHORIZATION_URL = 'https://qiita.com/api/v2/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://qiita.com/api/v2/access_tokens'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ' '
    REDIRECT_STATE = True
    EXTRA_DATA = [
        ('description', 'description'),
        ('facebook_id', 'facebook_id'),
        ('followees_count', 'followees_count'),
        ('followers_count', 'followers_count'),
        ('github_login_name', 'github_login_name'),
        ('id', 'id'),
        ('items_count', 'items_count'),
        ('linkedin_id', 'linkedin_id'),
        ('location', 'location'),
        ('name', 'name'),
        ('organization', 'organization'),
        ('profile_image_url', 'profile_image_url'),
        ('twitter_screen_name', 'twitter_screen_name'),
        ('website_url', 'website_url'),
    ]

    def auth_complete_params(self, state=None):
        data = super(QiitaOAuth2, self).auth_complete_params(state)
        if "grant_type" in data:
            del data["grant_type"]
        if "redirect_uri" in data:
            del data["redirect_uri"]
        return json.dumps(data)

    def auth_headers(self):
        return {'Content-Type': 'application/json'}

    def request_access_token(self, *args, **kwargs):
        data = super(QiitaOAuth2, self).request_access_token(*args, **kwargs)
        data.update({'access_token': data['token']})
        return data

    def get_user_details(self, response):
        """Return user details from Qiita account"""
        return {
            'username': response['id'],
            'fullname': response['name'],
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://qiita.com/api/v2/authenticated_user',
           headers={
                'Authorization': 'Bearer {0}'.format(access_token)
            })

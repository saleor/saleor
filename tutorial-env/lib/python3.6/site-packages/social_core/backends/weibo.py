# coding:utf-8
# author:hepochen@gmail.com  https://github.com/hepochen
"""
Weibo OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/weibo.html
"""
from .oauth import BaseOAuth2


class WeiboOAuth2(BaseOAuth2):
    """Weibo (of sina) OAuth authentication backend"""
    name = 'weibo'
    ID_KEY = 'uid'
    AUTHORIZATION_URL = 'https://api.weibo.com/oauth2/authorize'
    REQUEST_TOKEN_URL = 'https://api.weibo.com/oauth2/request_token'
    ACCESS_TOKEN_URL = 'https://api.weibo.com/oauth2/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('id', 'id'),
        ('name', 'username'),
        ('profile_image_url', 'profile_image_url'),
        ('gender', 'gender')
    ]

    def get_user_details(self, response):
        """Return user details from Weibo. API URL is:
        https://api.weibo.com/2/users/show.json/?uid=<UID>&access_token=<TOKEN>
        """
        if self.setting('DOMAIN_AS_USERNAME'):
            username = response.get('domain', '')
        else:
            username = response.get('name', '')
        fullname, first_name, last_name = self.get_user_names(
            first_name=response.get('screen_name', '')
        )
        return {'username': username,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def get_uid(self, access_token):
        """Return uid by access_token"""
        data = self.get_json(
            'https://api.weibo.com/oauth2/get_token_info',
            method='POST',
            params={'access_token': access_token}
        )
        return data['uid']

    def user_data(self, access_token, response=None, *args, **kwargs):
        """Return user data"""
        # If user id was not retrieved in the response, then get it directly
        # from weibo get_token_info endpoint
        uid = response and response.get('uid') or self.get_uid(access_token)
        user_data = self.get_json(
            'https://api.weibo.com/2/users/show.json',
            params={'access_token': access_token, 'uid': uid}
        )
        user_data['uid'] = uid
        return user_data

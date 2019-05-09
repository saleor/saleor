"""
Yandex OpenID and OAuth2 support.

This contribution adds support for Yandex.ru OpenID service in the form
openid.yandex.ru/user. Username is retrieved from the identity url.

If username is not specified, OpenID 2.0 url used for authentication.
"""
from six.moves.urllib_parse import urlsplit

from .open_id import OpenIdAuth
from .oauth import BaseOAuth2


class YandexOpenId(OpenIdAuth):
    """Yandex OpenID authentication backend"""
    name = 'yandex-openid'
    URL = 'http://openid.yandex.ru'

    def get_user_id(self, details, response):
        return details['email'] or response.identity_url

    def get_user_details(self, response):
        """Generate username from identity url"""
        values = super(YandexOpenId, self).get_user_details(response)
        values['username'] = values.get('username') or\
                             urlsplit(response.identity_url)\
                                    .path.strip('/')
        values['email'] = values.get('email', '')
        return values


class YandexOAuth2(BaseOAuth2):
    """Legacy Yandex OAuth2 authentication backend"""
    name = 'yandex-oauth2'
    AUTHORIZATION_URL = 'https://oauth.yandex.com/authorize'
    ACCESS_TOKEN_URL = 'https://oauth.yandex.com/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            response.get('real_name') or response.get('display_name') or ''
        )
        email = response.get('default_email')
        if not email:
            emails = response.get('emails')
            email = emails[0] if emails else ''
        return {'username': response.get('display_name'),
                'email': email,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json('https://login.yandex.ru/info',
                             params={'oauth_token': access_token,
                                     'format': 'json'})


class YaruOAuth2(BaseOAuth2):
    name = 'yaru'
    AUTHORIZATION_URL = 'https://oauth.yandex.com/authorize'
    ACCESS_TOKEN_URL = 'https://oauth.yandex.com/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            response.get('real_name') or response.get('display_name') or ''
        )
        email = response.get('default_email')
        if not email:
            emails = response.get('emails')
            email = emails[0] if emails else ''
        return {'username': response.get('display_name'),
                'email': email,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json('https://login.yandex.ru/info',
                             params={'oauth_token': access_token,
                                     'format': 'json'})

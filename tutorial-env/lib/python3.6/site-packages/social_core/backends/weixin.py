# -*- coding: utf-8 -*-
# author:duoduo3369@gmail.com  https://github.com/duoduo369
"""
Weixin OAuth2 backend
"""
from six.moves.urllib_parse import urlencode
from requests import HTTPError

from .oauth import BaseOAuth2
from ..exceptions import AuthCanceled, AuthUnknownError


class WeixinOAuth2(BaseOAuth2):
    """Weixin OAuth authentication backend"""
    name = 'weixin'
    ID_KEY = 'openid'
    AUTHORIZATION_URL = 'https://open.weixin.qq.com/connect/qrconnect'
    ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['snsapi_login']
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('nickname', 'username'),
        ('headimgurl', 'profile_image_url'),
    ]

    def get_user_details(self, response):
        """Return user details from Weixin. API URL is:
        https://api.weixin.qq.com/sns/userinfo
        """
        if self.setting('DOMAIN_AS_USERNAME'):
            username = response.get('domain', '')
        else:
            username = response.get('nickname', '')
        return {
            'username': username,
            'profile_image_url': response.get('headimgurl', '')
        }

    def user_data(self, access_token, *args, **kwargs):
        data = self.get_json('https://api.weixin.qq.com/sns/userinfo', params={
            'access_token': access_token,
            'openid': kwargs['response']['openid']
        })
        nickname = data.get('nickname')
        if nickname:
            # weixin api has some encode bug, here need handle
            data['nickname'] = nickname.encode(
                'raw_unicode_escape'
            ).decode('utf-8')
        return data

    def auth_params(self, state=None):
        appid, secret = self.get_key_and_secret()
        params = {
            'appid': appid,
            'redirect_uri': self.get_redirect_uri(state)
        }
        if self.STATE_PARAMETER and state:
            params['state'] = state
        if self.RESPONSE_TYPE:
            params['response_type'] = self.RESPONSE_TYPE
        return params

    def auth_complete_params(self, state=None):
        appid, secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'appid': appid,
            'secret': secret,
            'redirect_uri': self.get_redirect_uri(state)
        }

    def refresh_token_params(self, token, *args, **kwargs):
        appid, secret = self.get_key_and_secret()
        return {
            'refresh_token': token,
            'grant_type': 'refresh_token',
            'appid': appid,
            'secret': secret
        }

    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        try:
            response = self.request_access_token(
                self.ACCESS_TOKEN_URL,
                data=self.auth_complete_params(self.validate_state()),
                headers=self.auth_headers(),
                method=self.ACCESS_TOKEN_METHOD
            )
        except HTTPError as err:
            if err.response.status_code == 400:
                raise AuthCanceled(self, response=err.response)
            else:
                raise
        except KeyError:
            raise AuthUnknownError(self)
        if 'errcode' in response:
            raise AuthCanceled(self)
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)


class WeixinOAuth2APP(WeixinOAuth2):
    """
    Weixin OAuth authentication backend

    Can't use in web, only in weixin app
    """
    name = 'weixinapp'
    ID_KEY = 'openid'
    AUTHORIZATION_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def auth_url(self):
        if self.STATE_PARAMETER or self.REDIRECT_STATE:
            # Store state in session for further request validation. The state
            # value is passed as state parameter (as specified in OAuth2 spec),
            # but also added to redirect, that way we can still verify the
            # request if the provider doesn't implement the state parameter.
            # Reuse token if any.
            name = self.name + '_state'
            state = self.strategy.session_get(name)
            if state is None:
                state = self.state_token()
                self.strategy.session_set(name, state)
        else:
            state = None

        params = self.auth_params(state)
        params.update(self.get_scope_argument())
        params.update(self.auth_extra_arguments())
        params = urlencode(sorted(params.items()))
        return '{}#wechat_redirect'.format(
            self.AUTHORIZATION_URL + '?' + params
        )

    def auth_complete_params(self, state=None):
        appid, secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'appid': appid,
            'secret': secret,
        }

    def validate_state(self):
        return None

    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        try:
            response = self.request_access_token(
                self.ACCESS_TOKEN_URL,
                data=self.auth_complete_params(self.validate_state()),
                headers=self.auth_headers(),
                method=self.ACCESS_TOKEN_METHOD
            )
        except HTTPError as err:
            if err.response.status_code == 400:
                raise AuthCanceled(self)
            else:
                raise
        except KeyError:
            raise AuthUnknownError(self)

        if 'errcode' in response:
            raise AuthCanceled(self)
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)

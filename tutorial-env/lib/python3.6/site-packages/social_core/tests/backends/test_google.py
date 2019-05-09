import datetime
import json
import unittest2

from httpretty import HTTPretty

from six.moves.urllib_parse import urlencode

from ...actions import do_disconnect

from ..models import User
from .oauth import OAuth1Test, OAuth2Test
from .open_id import OpenIdTest
from .open_id_connect import OpenIdConnectTestMixin


class GoogleOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.google.GoogleOAuth2'
    user_data_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    expected_username = 'foo'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'profile': 'https://plus.google.com/101010101010101010101',
        'family_name': 'Bar',
        'sub': '101010101010101010101',
        'picture': 'https://lh5.googleusercontent.com/-ui-GqpNh5Ms/'
                   'AAAAAAAAAAI/AAAAAAAAAZw/a7puhHMO_fg/photo.jpg',
        'locale': 'en',
        'email_verified': True,
        'given_name': 'Foo',
        'email': 'foo@bar.com',
        'name': 'Foo Bar',
    })

    def test_login(self):
        self.do_login()
        last_request = HTTPretty.last_request
        self.assertEqual(last_request.method, 'GET')
        self.assertTrue(self.user_data_url.endswith(last_request.path))
        self.assertEqual(
            last_request.headers['Authorization'],
            'Bearer foobar',
        )
        self.assertEqual(last_request.querystring, {})

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

    def test_with_unique_user_id(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GOOGLE_OAUTH2_USE_UNIQUE_USER_ID': True,
        })
        self.do_login()


class GoogleOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.google.GoogleOAuth'
    user_data_url = 'https://www.googleapis.com/userinfo/email'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
        'oauth_callback_confirmed': 'true'
    })
    user_data_body = urlencode({
        'email': 'foobar@gmail.com',
        'isVerified': 'true',
        'id': '101010101010101010101'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

    def test_with_unique_user_id(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GOOGLE_OAUTH_USE_UNIQUE_USER_ID': True
        })
        self.do_login()

    def test_with_anonymous_key_and_secret(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GOOGLE_OAUTH_KEY': None,
            'SOCIAL_AUTH_GOOGLE_OAUTH_SECRET': None
        })
        self.do_login()


JANRAIN_NONCE = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')


class GoogleOpenIdTest(OpenIdTest):
    backend_path = 'social_core.backends.google.GoogleOpenId'
    expected_username = 'FooBar'
    discovery_body = ''.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<xrds:XRDS xmlns:xrds="xri://$xrds" xmlns="xri://$xrd*($v*2.0)">',
        '<XRD>',
        '<Service priority="0">',
        '<Type>http://specs.openid.net/auth/2.0/signon</Type>',
        '<Type>http://openid.net/srv/ax/1.0</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/mode/popup</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/icon</Type>',
        '<Type>http://specs.openid.net/extensions/pape/1.0</Type>',
        '<URI>https://www.google.com/accounts/o8/ud</URI>',
        '</Service>',
        '<Service priority="10">',
        '<Type>http://specs.openid.net/auth/2.0/signon</Type>',
        '<Type>http://openid.net/srv/ax/1.0</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/mode/popup</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/icon</Type>',
        '<Type>http://specs.openid.net/extensions/pape/1.0</Type>',
        '<URI>https://www.google.com/accounts/o8/ud?source=mail</URI>',
        '</Service>',
        '<Service priority="10">',
        '<Type>http://specs.openid.net/auth/2.0/signon</Type>',
        '<Type>http://openid.net/srv/ax/1.0</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/mode/popup</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/icon</Type>',
        '<Type>http://specs.openid.net/extensions/pape/1.0</Type>',
        '<URI>https://www.google.com/accounts/o8/ud?source=gmail.com</URI>',
        '</Service>',
        '<Service priority="10">',
        '<Type>http://specs.openid.net/auth/2.0/signon</Type>',
        '<Type>http://openid.net/srv/ax/1.0</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/mode/popup</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/icon</Type>',
        '<Type>http://specs.openid.net/extensions/pape/1.0</Type>',
        '<URI>',
        'https://www.google.com/accounts/o8/ud?source=googlemail.com',
        '</URI>',
        '</Service>',
        '<Service priority="10">',
        '<Type>http://specs.openid.net/auth/2.0/signon</Type>',
        '<Type>http://openid.net/srv/ax/1.0</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/mode/popup</Type>',
        '<Type>http://specs.openid.net/extensions/ui/1.0/icon</Type>',
        '<Type>http://specs.openid.net/extensions/pape/1.0</Type>',
        '<URI>https://www.google.com/accounts/o8/ud?source=profiles</URI>',
        '</Service>',
        '</XRD>',
        '</xrds:XRDS>'
    ])
    server_response = urlencode({
        'janrain_nonce': JANRAIN_NONCE,
        'openid.assoc_handle': 'assoc-handle',
        'openid.claimed_id': 'https://www.google.com/accounts/o8/id?'
                             'id=some-google-id',
        'openid.ext1.mode': 'fetch_response',
        'openid.ext1.type.email': 'http://axschema.org/contact/email',
        'openid.ext1.type.first_name': 'http://axschema.org/namePerson/first',
        'openid.ext1.type.last_name': 'http://axschema.org/namePerson/last',
        'openid.ext1.type.old_email': 'http://schema.openid.net/contact/email',
        'openid.ext1.value.email': 'foo@bar.com',
        'openid.ext1.value.first_name': 'Foo',
        'openid.ext1.value.last_name': 'Bar',
        'openid.ext1.value.old_email': 'foo@bar.com',
        'openid.identity': 'https://www.google.com/accounts/o8/id?'
                           'id=some-google-id',
        'openid.mode': 'id_res',
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.ns.ext1': 'http://openid.net/srv/ax/1.0',
        'openid.op_endpoint': 'https://www.google.com/accounts/o8/ud',
        'openid.response_nonce': JANRAIN_NONCE + 'by95cT34vX7p9g',
        'openid.return_to': 'http://myapp.com/complete/google/?'
                            'janrain_nonce=' + JANRAIN_NONCE,
        'openid.sig': 'brT2kmu3eCzb1gQ1pbaXdnWioVM=',
        'openid.signed': 'op_endpoint,claimed_id,identity,return_to,'
                         'response_nonce,assoc_handle,ns.ext1,ext1.mode,'
                         'ext1.type.old_email,ext1.value.old_email,'
                         'ext1.type.first_name,ext1.value.first_name,'
                         'ext1.type.last_name,ext1.value.last_name,'
                         'ext1.type.email,ext1.value.email'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class GoogleRevokeTokenTest(GoogleOAuth2Test):
    def test_revoke_token(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GOOGLE_OAUTH2_REVOKE_TOKENS_ON_DISCONNECT': True
        })
        self.do_login()
        user = User.get(self.expected_username)
        user.password = 'password'
        HTTPretty.register_uri(self._method(self.backend.REVOKE_TOKEN_METHOD),
                               self.backend.REVOKE_TOKEN_URL,
                               status=200)
        do_disconnect(self.backend, user)


class GoogleOpenIdConnectTest(OpenIdConnectTestMixin, OAuth2Test):
    backend_path = \
        'social_core.backends.google_openidconnect.GoogleOpenIdConnect'
    user_data_url = \
        'https://www.googleapis.com/plus/v1/people/me/openIdConnect'
    issuer = 'accounts.google.com'
    openid_config_body = json.dumps({
        'issuer': 'https://accounts.google.com',
        'authorization_endpoint': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_endpoint': 'https://www.googleapis.com/oauth2/v4/token',
        'userinfo_endpoint': 'https://www.googleapis.com/oauth2/v3/userinfo',
        'revocation_endpoint': 'https://accounts.google.com/o/oauth2/revoke',
        'jwks_uri': 'https://www.googleapis.com/oauth2/v3/certs',
        'response_types_supported': [
            'code',
            'token',
            'id_token',
            'code token',
            'code id_token',
            'token id_token',
            'code token id_token',
            'none',
        ],
        'subject_types_supported': [
            'public',
        ],
        'id_token_signing_alg_values_supported': [
            'RS256',
        ],
        'scopes_supported': [
            'openid',
            'email',
            'profile',
        ],
        'token_endpoint_auth_methods_supported': [
            'client_secret_post',
            'client_secret_basic',
        ],
        'claims_supported': [
            'aud',
            'email',
            'email_verified',
            'exp',
            'family_name',
            'given_name',
            'iat',
            'iss',
            'locale',
            'name',
            'picture',
            'sub',
        ],
    })

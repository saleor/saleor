# -*- coding: utf-8 -*-
import os
import sys
import json
import datetime
import unittest2
import base64
from calendar import timegm

from jose import jwt
from jose.jwk import RSAKey
from httpretty import HTTPretty

sys.path.insert(0, '..')

from ...exceptions import AuthTokenError


TEST_ROOT = os.path.dirname(os.path.dirname(__file__))

JWK_KEY = {
    'kty': 'RSA',
    'd': 'ZmswNokEvBcxW_Kvcy8mWUQOQCBdGbnM0xR7nhvGHC-Q24z3XAQWlMWbsmGc_R1o' \
         '_F3zK7DBlc3BokdRaO1KJirNmnHCw5TlnBlJrXiWpFBtVglUg98-4sRRO0VWnGXK' \
         'JPOkBQ6b_DYRO3b0o8CSpWowpiV6HB71cjXTqKPZf-aXU9WjCCAtxVjfIxgQFu5I' \
         '-G1Qah8mZeY8HK_y99L4f0siZcbUoaIcfeWBhxi14ODyuSAHt0sNEkhiIVBZE7QZ' \
         'm-SEP1ryT9VAaljbwHHPmg7NC26vtLZhvaBGbTTJnEH0ZubbN2PMzsfeNyoCIHy4' \
         '4QDSpQDCHfgcGOlHY_t5gQ',
    'e': 'AQAB',
    'use': 'sig',
    'kid': 'testkey',
    'alg': 'RS256',
    'n': 'pUfcJ8WFrVue98Ygzb6KEQXHBzi8HavCu8VENB2As943--bHPcQ-nScXnrRFAUg8' \
         'H5ZltuOcHWvsGw_AQifSLmOCSWJAPkdNb0w0QzY7Re8NrPjCsP58Tytp5LicF0Ao' \
         'Ag28UK3JioY9hXHGvdZsWR1Rp3I-Z3nRBP6HyO18pEgcZ91c9aAzsqu80An9X4DA' \
         'b1lExtZorvcd5yTBzZgr-MUeytVRni2lDNEpa6OFuopHXmg27Hn3oWAaQlbymd4g' \
         'ifc01oahcwl3ze2tMK6gJxa_TdCf1y99Yq6oilmVvZJ8kwWWnbPE-oDmOVPVnEyT' \
         'vYVCvN4rBT1DQ-x0F1mo2Q',
}

JWK_PUBLIC_KEY = {key: value for key, value in JWK_KEY.items() if key != 'd'}


class OpenIdConnectTestMixin(object):
    """
    Mixin to test OpenID Connect consumers. Inheriting classes should also
    inherit OAuth2Test.
    """
    client_key = 'a-key'
    client_secret = 'a-secret-key'
    issuer = None  # id_token issuer
    openid_config_body = None
    key = None

    def setUp(self):
        super(OpenIdConnectTestMixin, self).setUp()
        self.key = JWK_KEY.copy()
        self.public_key = JWK_PUBLIC_KEY.copy()

        HTTPretty.register_uri(HTTPretty.GET,
          self.backend.OIDC_ENDPOINT + '/.well-known/openid-configuration',
          status=200,
          body=self.openid_config_body
        )
        oidc_config = json.loads(self.openid_config_body)

        def jwks(_request, _uri, headers):
            return 200, headers, json.dumps({'keys': [self.key]})

        HTTPretty.register_uri(HTTPretty.GET,
                               oidc_config.get('jwks_uri'),
                               status=200,
                               body=json.dumps({'keys': [self.public_key]}))

    def extra_settings(self):
        settings = super(OpenIdConnectTestMixin, self).extra_settings()
        settings.update({
            'SOCIAL_AUTH_{0}_KEY'.format(self.name): self.client_key,
            'SOCIAL_AUTH_{0}_SECRET'.format(self.name): self.client_secret,
            'SOCIAL_AUTH_{0}_ID_TOKEN_DECRYPTION_KEY'.format(self.name):
                self.client_secret
        })
        return settings

    def get_id_token(self, client_key=None, expiration_datetime=None,
                     issue_datetime=None, nonce=None, issuer=None):
        """
        Return the id_token to be added to the access token body.
        """
        return {
            'iss': issuer,
            'nonce': nonce,
            'aud': client_key,
            'azp': client_key,
            'exp': expiration_datetime,
            'iat': issue_datetime,
            'sub': '1234'
        }

    def prepare_access_token_body(self, client_key=None, tamper_message=False,
                                  expiration_datetime=None,
                                  issue_datetime=None, nonce=None,
                                  issuer=None):
        """
        Prepares a provider access token response. Arguments:

        client_id       -- (str) OAuth ID for the client that requested
                                 authentication.
        expiration_time -- (datetime) Date and time after which the response
                                      should be considered invalid.
        """

        body = {'access_token': 'foobar', 'token_type': 'bearer'}
        client_key = client_key or self.client_key
        now = datetime.datetime.utcnow()
        expiration_datetime = expiration_datetime or \
                              (now + datetime.timedelta(seconds=30))
        issue_datetime = issue_datetime or now
        nonce = nonce or 'a-nonce'
        issuer = issuer or self.issuer
        id_token = self.get_id_token(
            client_key,
            timegm(expiration_datetime.utctimetuple()),
            timegm(issue_datetime.utctimetuple()),
            nonce,
            issuer
        )

        body['id_token'] = jwt.encode(
            id_token,
            key=dict(self.key,
                     iat=timegm(issue_datetime.utctimetuple()),
                     nonce=nonce),
            algorithm='RS256',
            access_token='foobar'
        )

        if tamper_message:
            header, msg, sig = body['id_token'].split('.')
            id_token['sub'] = '1235'
            msg = base64.encodestring(json.dumps(id_token).encode()).decode()
            body['id_token'] = '.'.join([header, msg, sig])

        return json.dumps(body)

    def authtoken_raised(self, expected_message, **access_token_kwargs):
        self.access_token_body = self.prepare_access_token_body(
            **access_token_kwargs
        )
        with self.assertRaisesRegexp(AuthTokenError, expected_message):
            self.do_login()

    def test_invalid_signature(self):
        self.authtoken_raised(
            'Token error: Signature verification failed',
            tamper_message=True
        )

    def test_expired_signature(self):
        expiration_datetime = datetime.datetime.utcnow() - \
                              datetime.timedelta(seconds=30)
        self.authtoken_raised('Token error: Signature has expired',
                              expiration_datetime=expiration_datetime)

    def test_invalid_issuer(self):
        self.authtoken_raised('Token error: Invalid issuer',
                              issuer='someone-else')

    def test_invalid_audience(self):
        self.authtoken_raised('Token error: Invalid audience',
                              client_key='someone-else')

    def test_invalid_issue_time(self):
        expiration_datetime = datetime.datetime.utcnow() - \
                              datetime.timedelta(hours=1)
        self.authtoken_raised('Token error: Incorrect id_token: iat',
                              issue_datetime=expiration_datetime)

    def test_invalid_nonce(self):
        self.authtoken_raised(
            'Token error: Incorrect id_token: nonce',
            nonce='something-wrong'
        )

import json
import datetime
from calendar import timegm

import six
from jose import jwk, jwt
from jose.jwt import JWTError, JWTClaimsError, ExpiredSignatureError
from jose.utils import base64url_decode

from social_core.backends.oauth import BaseOAuth2
from social_core.utils import cache
from social_core.exceptions import AuthTokenError


class OpenIdConnectAssociation(object):
    """ Use Association model to save the nonce by force."""

    def __init__(self, handle, secret='', issued=0, lifetime=0, assoc_type=''):
        self.handle = handle  # as nonce
        self.secret = secret.encode()  # not use
        self.issued = issued  # not use
        self.lifetime = lifetime  # not use
        self.assoc_type = assoc_type  # as state


class OpenIdConnectAuth(BaseOAuth2):
    """
    Base class for Open ID Connect backends.
    Currently only the code response type is supported.
    """
    # Override OIDC_ENDPOINT in your subclass to enable autoconfig of OIDC
    OIDC_ENDPOINT = None
    ID_TOKEN_MAX_AGE = 600
    DEFAULT_SCOPE = ['openid', 'profile', 'email']
    EXTRA_DATA = ['id_token', 'refresh_token', ('sub', 'id')]
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'
    REVOKE_TOKEN_METHOD = 'GET'
    ID_KEY = 'sub'
    USERNAME_KEY = 'preferred_username'
    ID_TOKEN_ISSUER = ''
    ACCESS_TOKEN_URL = ''
    AUTHORIZATION_URL = ''
    REVOKE_TOKEN_URL = ''
    USERINFO_URL = ''
    JWKS_URI = ''
    JWT_DECODE_OPTIONS = dict()

    def __init__(self, *args, **kwargs):
        self.id_token = None
        super(OpenIdConnectAuth, self).__init__(*args, **kwargs)

    def authorization_url(self):
        return self.AUTHORIZATION_URL or \
            self.oidc_config().get('authorization_endpoint')

    def access_token_url(self):
        return self.ACCESS_TOKEN_URL or \
            self.oidc_config().get('token_endpoint')

    def revoke_token_url(self, token, uid):
        return self.REVOKE_TOKEN_URL or \
            self.oidc_config().get('revocation_endpoint')

    def id_token_issuer(self):
        return self.ID_TOKEN_ISSUER or \
            self.oidc_config().get('issuer')

    def userinfo_url(self):
        return self.USERINFO_URL or \
            self.oidc_config().get('userinfo_endpoint')

    def jwks_uri(self):
        return self.JWKS_URI or \
            self.oidc_config().get('jwks_uri')

    @cache(ttl=86400)
    def oidc_config(self):
        return self.get_json(self.OIDC_ENDPOINT +
                             '/.well-known/openid-configuration')

    @cache(ttl=86400)
    def get_jwks_keys(self):
        keys = self.get_remote_jwks_keys()

        # Add client secret as oct key so it can be used for HMAC signatures
        # client_id, client_secret = self.get_key_and_secret()
        # keys.append({'key': client_secret, 'kty': 'oct'})
        return keys

    def get_remote_jwks_keys(self):
        response = self.request(self.jwks_uri())
        return json.loads(response.text)['keys']

    def auth_params(self, state=None):
        """Return extra arguments needed on auth process."""
        params = super(OpenIdConnectAuth, self).auth_params(state)
        params['nonce'] = self.get_and_store_nonce(
            self.authorization_url(), state
        )
        return params

    def get_and_store_nonce(self, url, state):
        # Create a nonce
        nonce = self.strategy.random_string(64)
        # Store the nonce
        association = OpenIdConnectAssociation(nonce, assoc_type=state)
        self.strategy.storage.association.store(url, association)
        return nonce

    def get_nonce(self, nonce):
        try:
            return self.strategy.storage.association.get(
                server_url=self.authorization_url(),
                handle=nonce
            )[0]
        except IndexError:
            pass

    def remove_nonce(self, nonce_id):
        self.strategy.storage.association.remove([nonce_id])

    def validate_claims(self, id_token):
        utc_timestamp = timegm(datetime.datetime.utcnow().utctimetuple())

        if 'nbf' in id_token and utc_timestamp < id_token['nbf']:
            raise AuthTokenError(self, 'Incorrect id_token: nbf')

        # Verify the token was issued in the last 10 minutes
        iat_leeway = self.setting('ID_TOKEN_MAX_AGE', self.ID_TOKEN_MAX_AGE)
        if utc_timestamp > id_token['iat'] + iat_leeway:
            raise AuthTokenError(self, 'Incorrect id_token: iat')

        # Validate the nonce to ensure the request was not modified
        nonce = id_token.get('nonce')
        if not nonce:
            raise AuthTokenError(self, 'Incorrect id_token: nonce')

        nonce_obj = self.get_nonce(nonce)
        if nonce_obj:
            self.remove_nonce(nonce_obj.id)
        else:
            raise AuthTokenError(self, 'Incorrect id_token: nonce')

    def find_valid_key(self, id_token):
        for key in self.get_jwks_keys():
            rsakey = jwk.construct(key)
            message, encoded_sig = id_token.rsplit('.', 1)
            decoded_sig = base64url_decode(encoded_sig.encode('utf-8'))
            if rsakey.verify(message.encode('utf-8'), decoded_sig):
                return key

    def validate_and_return_id_token(self, id_token, access_token):
        """
        Validates the id_token according to the steps at
        http://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation.
        """
        client_id, client_secret = self.get_key_and_secret()

        key = self.find_valid_key(id_token)

        if not key:
            raise AuthTokenError(self, 'Signature verification failed')

        alg = key['alg']
        rsakey = jwk.construct(key)

        try:
            claims = jwt.decode(
                id_token,
                rsakey.to_pem().decode('utf-8'),
                algorithms=[alg],
                audience=client_id,
                issuer=self.id_token_issuer(),
                access_token=access_token,
                options=self.JWT_DECODE_OPTIONS,
            )
        except ExpiredSignatureError:
            raise AuthTokenError(self, 'Signature has expired')
        except JWTClaimsError as error:
            raise AuthTokenError(self, str(error))
        except JWTError:
            raise AuthTokenError(self, 'Invalid signature')

        self.validate_claims(claims)

        return claims

    def request_access_token(self, *args, **kwargs):
        """
        Retrieve the access token. Also, validate the id_token and
        store it (temporarily).
        """
        response = self.get_json(*args, **kwargs)
        self.id_token = self.validate_and_return_id_token(
            response['id_token'],
            response['access_token']
        )
        return response

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(self.userinfo_url(), headers={
            'Authorization': 'Bearer {0}'.format(access_token)
        })

    def get_user_details(self, response):
        username_key = self.setting('USERNAME_KEY', default=self.USERNAME_KEY)
        return {
            'username': response.get(username_key),
            'email': response.get('email'),
            'fullname': response.get('name'),
            'first_name': response.get('given_name'),
            'last_name': response.get('family_name'),
        }

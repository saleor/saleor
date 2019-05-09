import json
import unittest2

from .oauth import OAuth1Test, OAuth2Test
from .open_id_connect import OpenIdConnectTestMixin


class GlobusOpenIdConnectTest(OpenIdConnectTestMixin, OAuth2Test):
    backend_path = \
        'social_core.backends.globus.GlobusOpenIdConnect'
    issuer = 'https://auth.globus.org'
    openid_config_body = json.dumps({
        'issuer': 'https://auth.globus.org',
        'authorization_endpoint': 'https://auth.globus.org/v2/oauth2/authorize',
        'userinfo_endpoint': 'https://auth.globus.org/v2/oauth2/userinfo',
        'token_endpoint': 'https://auth.globus.org/v2/oauth2/token',
        'revocation_endpoint': 'https://auth.globus.org/v2/oauth2/token/revoke',
        'jwks_uri': 'https://auth.globus.org/jwk.json',
        'response_types_supported': [
            'code',
            'token',
            'token id_token',
            'id_token'
        ],
        'id_token_signing_alg_values_supported': [
            'RS512'
        ],
        'scopes_supported': [
            'openid',
            'email',
            'profile'
        ],
        'token_endpoint_auth_methods_supported': [
            'client_secret_basic'
        ],
        'claims_supported': [
            'at_hash',
            'aud',
            'email',
            'exp',
            'name',
            'nonce',
            'preferred_username',
            'iat',
            'iss',
            'sub'
        ],
        'subject_types_supported' : ['public']
    })

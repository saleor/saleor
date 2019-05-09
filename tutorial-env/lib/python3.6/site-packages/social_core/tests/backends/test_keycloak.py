import json
import time
import unittest

import jwt

from .oauth import OAuth2Test


_PRIVATE_KEY_HEADERLESS = '''
MIIEowIBAAKCAQEAvyo2hx1L3ALHeUd/6xk/lIhTyZ/HJZ+Sss/ge6T6gPdES4Dw
BvwGlAp21iEbmjmizsv6+ZsyuKZUiC1J4A90lmIA57aYXHHoh9GBWQZzXeCNgghP
JpGYYSCN+1qeD4nbwD9cQBtPrGBpPpPtv2a/xdPqDm5ko6adMhmbm8e4Me/ppWPi
0U+skWQJepBhjEt3x+AOMKDv2TUBWOc3mYFNkr9qNOPe7FxnqUk6ZtkI3QNjZTky
AU7cat87u1vT5thAxVY18i1GfSZwtQbU3Ba6hXI5SIHB1lS88SJ9/+E/flJJPD2N
Nzv2z3HAVuTUOYi48fnXFHpJLGv+mGLNtE77hwIDAQABAoIBAQCUyQYno2Wnl4Ip
orys/rm9oV2VUAZwAgLrqV/O3Fkch1dgbLpktUNpdbuIbbxODQ3qZliwbVrM3Khu
VNFq0pyrbxvFPRjY2s9g5m8GGz8vkdaRnmX8XtV6wxu+xoi/D006FBZ4zsj0IRXI
3tnsXsxj7Mv+72zk8ojmtYend4qlUfzBVTpMRDc4XDC4Ya91fgFgfibtUE1qc8Ap
ctCzk9wZgN9SOKXHcKANhqC8BmQv7NspI0RT0Oq0n/U921P/+y1M++Z0Z2vQvjiR
GvDpSlnmlLB3S3E7zHbmksyUyK4Ab7xYi51yFKgrYjtaM3QLCTlSmTQBM8EhjZNG
VJvgEI4BAoGBAOQzd4PdB3jW6OnUXDrzWqfCAgpMxWtAmP5h+LrmsrV+upXggRnv
iNzTqiq0QpdrgYrikFGDkGEsqfrnd7IkskDMT8PMuncmDkuF67kg6G4/vzyz5QyA
jolf6qmHQPMCfxtCPUZZOUcuRKnj5KVIGfJu2gu5Z2lEysuV5ZQE0OiNAoGBANZz
wqLhqN376MT3YEbsOcWXYBDXX+FzWAYHsxf4APHJrNr6pkM4dTsvXU2tQIUV4N3c
SJvMVSI91VL8mdgQxHKaECUizye19brJ1BysbeFjBCK+Y6bYMd8n0Hdxxi/ZyeF9
AzfIPQN2uZSzU/I+Nt0tlz/SCoL4Qi3FQpgtLoFjAoGAb8XVsDy+wC1jf8SIOEei
C7E3FpxrxhCp309VaRY+Si98bJS+J1nwC1mRa8FHLKt3k/NNBOAQA8jAqShetF7N
AHgSSbEpU9rL/anmv5Kixf1rSexDMFB3gEn+wnKBGYYLg+p54M8rAvZio2QARgR+
0QQCwONbB3Cuc/FDtbB2MrECgYAhSqtGmf2bKIZEPZsGp5l4YT2an7TUzRE3Lm7R
I8ERyBs7i3nQKa2ZWIsFigXgIztbdd0Xwqrcu/in/2rqrf+xQtWKzlKWeZsCOl7h
bKtKOBLmSeQyfJGRcR7dzB3WQ9shVETxnfZK2V2KBiTcEGh4AaHfWH4lQuETNfJW
qXz0vQKBgDVz+ZvULA/OZWXrOI1il7KoahWdb9vr8VhWgHKnDW7hInDFh6SEQHn6
mSNns0AssDwr4TheET7klb7AvbBKrNSP/Tz9AzkwMz148T2ffkPFMZRuvRT+eQ5Z
ey4gIBKESJF6X9fefiawCrI3+PC7x9x0ngP9R4t/OzDWVAYn9gmd
'''.strip()

_PRIVATE_KEY = '''
-----BEGIN RSA PRIVATE KEY-----
{_PRIVATE_KEY_HEADERLESS}
-----END RSA PRIVATE KEY-----
'''.format(
    _PRIVATE_KEY_HEADERLESS=_PRIVATE_KEY_HEADERLESS
)

_PUBLIC_KEY_HEADERLESS = '''
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvyo2hx1L3ALHeUd/6xk/
lIhTyZ/HJZ+Sss/ge6T6gPdES4DwBvwGlAp21iEbmjmizsv6+ZsyuKZUiC1J4A90
lmIA57aYXHHoh9GBWQZzXeCNgghPJpGYYSCN+1qeD4nbwD9cQBtPrGBpPpPtv2a/
xdPqDm5ko6adMhmbm8e4Me/ppWPi0U+skWQJepBhjEt3x+AOMKDv2TUBWOc3mYFN
kr9qNOPe7FxnqUk6ZtkI3QNjZTkyAU7cat87u1vT5thAxVY18i1GfSZwtQbU3Ba6
hXI5SIHB1lS88SJ9/+E/flJJPD2NNzv2z3HAVuTUOYi48fnXFHpJLGv+mGLNtE77
hwIDAQAB
'''.strip()

_PUBLIC_KEY = '''
-----BEGIN PUBLIC KEY-----
{_PUBLIC_KEY_HEADERLESS}
-----END PUBLIC KEY-----
'''.format(
    _PUBLIC_KEY_HEADERLESS=_PUBLIC_KEY_HEADERLESS
)

_KEY = 'example'
_SECRET = '1234abcd-1234-abcd-1234-abcd1234adcd'

_AUTHORIZATION_URL = 'https://sso.example.com/auth/realms/example/protocol/openid-connect/auth'
_ACCESS_TOKEN_URL = 'https://sso.example.com/auth/realms/example/protocol/openid-connect/token'

_ALGORITHM = 'RS256'
_AUTH_TIME = int(time.time())
_PAYLOAD = {
    'preferred_username': 'john.doe',
    'email': 'john.doe@example.com',
    'name': 'John Doe',
    'given_name': 'John',
    'family_name': 'Doe',

    'iss': 'https://sso.example.com',
    'sub': 'john.doe',
    'aud': _KEY,
    'exp': _AUTH_TIME + 3600,
    'iat': _AUTH_TIME,
}


def _encode(
    payload,
    key=_PRIVATE_KEY,
    algorithm=_ALGORITHM
):
    return jwt.encode(payload, key=key, algorithm=algorithm).decode('utf-8')


def _decode(
    token,
    key=_PUBLIC_KEY,
    algorithms=_ALGORITHM,
    audience=_KEY,
):
    return jwt.decode(token, key=key, algorithms=algorithms, audience=audience)


class KeycloakOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.keycloak.KeycloakOAuth2'
    expected_username = 'john.doe'
    access_token_body = json.dumps({
        'token_type': 'Bearer',
        'id_token': _encode(_PAYLOAD),
        'access_token': _encode(_PAYLOAD),
    })

    def extra_settings(self):
        return {
            'SOCIAL_AUTH_KEYCLOAK_KEY': _KEY,
            'SOCIAL_AUTH_KEYCLOAK_SECRET': _SECRET,
            'SOCIAL_AUTH_KEYCLOAK_PUBLIC_KEY': _PUBLIC_KEY_HEADERLESS,
            'SOCIAL_AUTH_KEYCLOAK_ALGORITHM': _ALGORITHM,
            'SOCIAL_AUTH_KEYCLOAK_AUTHORIZATION_URL': _AUTHORIZATION_URL,
            'SOCIAL_AUTH_KEYCLOAK_ACCESS_TOKEN_URL': _ACCESS_TOKEN_URL,
        }

    def test_encode_decode(self):
        token = _encode(_PAYLOAD)
        self.assertEqual(_PAYLOAD, _decode(token))

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

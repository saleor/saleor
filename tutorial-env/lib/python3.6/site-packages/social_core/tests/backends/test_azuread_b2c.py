"""
Copyright (c) 2017 Noderabbit Inc., d.b.a. Appsembler

All rights reserved.

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import json
import jwt

from time import time
from httpretty import HTTPretty
from jwt.algorithms import RSAAlgorithm

from .oauth import OAuth2Test


# Dummy private and private keys:
RSA_PUBLIC_JWT_KEY = {
    # https://github.com/jpadilla/pyjwt/blob/06f461a/tests/keys/jwk_rsa_pub.json
    'kty': 'RSA',
    'kid': 'bilbo.baggins@hobbiton.example',
    'use': 'sig',
    'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw',
    'e': 'AQAB'
}

RSA_PRIVATE_JWT_KEY = {
    # https://github.com/jpadilla/pyjwt/blob/06f461a/tests/keys/jwk_rsa_key.json
    'kty': 'RSA',
    'kid': 'bilbo.baggins@hobbiton.example',
    'use': 'sig',
    'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw',
    'e': 'AQAB',
    'd': 'bWUC9B-EFRIo8kpGfh0ZuyGPvMNKvYWNtB_ikiH9k20eT-O1q_I78eiZkpXxXQ0UTEs2LsNRS-8uJbvQ-A1irkwMSMkK1J3XTGgdrhCku9gRldY7sNA_AKZGh-Q661_42rINLRCe8W-nZ34ui_qOfkLnK9QWDDqpaIsA-bMwWWSDFu2MUBYwkHTMEzLYGqOe04noqeq1hExBTHBOBdkMXiuFhUq1BU6l-DqEiWxqg82sXt2h-LMnT3046AOYJoRioz75tSUQfGCshWTBnP5uDjd18kKhyv07lhfSJdrPdM5Plyl21hsFf4L_mHCuoFau7gdsPfHPxxjVOcOpBrQzwQ',
    'p': '3Slxg_DwTXJcb6095RoXygQCAZ5RnAvZlno1yhHtnUex_fp7AZ_9nRaO7HX_-SFfGQeutao2TDjDAWU4Vupk8rw9JR0AzZ0N2fvuIAmr_WCsmGpeNqQnev1T7IyEsnh8UMt-n5CafhkikzhEsrmndH6LxOrvRJlsPp6Zv8bUq0k',
    'q': 'uKE2dh-cTf6ERF4k4e_jy78GfPYUIaUyoSSJuBzp3Cubk3OCqs6grT8bR_cu0Dm1MZwWmtdqDyI95HrUeq3MP15vMMON8lHTeZu2lmKvwqW7anV5UzhM1iZ7z4yMkuUwFWoBvyY898EXvRD-hdqRxHlSqAZ192zB3pVFJ0s7pFc',
    'dp': 'B8PVvXkvJrj2L-GYQ7v3y9r6Kw5g9SahXBwsWUzp19TVlgI-YV85q1NIb1rxQtD-IsXXR3-TanevuRPRt5OBOdiMGQp8pbt26gljYfKU_E9xn-RULHz0-ed9E9gXLKD4VGngpz-PfQ_q29pk5xWHoJp009Qf1HvChixRX59ehik',
    'dq': 'CLDmDGduhylc9o7r84rEUVn7pzQ6PF83Y-iBZx5NT-TpnOZKF1pErAMVeKzFEl41DlHHqqBLSM0W1sOFbwTxYWZDm6sI6og5iTbwQGIC3gnJKbi_7k_vJgGHwHxgPaX2PnvP-zyEkDERuf-ry4c_Z11Cq9AqC2yeL6kdKT1cYF8',
    'qi': '3PiqvXQN0zwMeE-sBvZgi289XP9XCQF3VWqPzMKnIgQp7_Tugo6-NZBKCQsMf3HaEGBjTVJs_jcK8-TRXvaKe-7ZMaQj8VfBdYkssbu0NKDDhjJ-GtiseaDVWt7dcH0cfwxgFUHpQh7FoCrjFJ6h6ZEpMF6xmujs4qMpPz8aaI4'
}


class AzureADOAuth2Test(OAuth2Test):
    AUTH_KEY = 'abcdef12-1234-9876-0000-abcdef098765'
    EXPIRES_IN = 3600
    AUTH_TIME = int(time())
    EXPIRES_ON = AUTH_TIME + EXPIRES_IN

    backend_path = 'social_core.backends.azuread_b2c.AzureADB2COAuth2'
    expected_username = 'FooBar'
    refresh_token_body = json.dumps({
        'access_token': 'foobar-new-token',
        'token_type': 'bearer',
        'expires_in': EXPIRES_IN,
        'refresh_token': 'foobar-new-refresh-token',
        'scope': 'identity'
    })

    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'id_token': jwt.encode(
            key=RSAAlgorithm.from_jwk(json.dumps(RSA_PRIVATE_JWT_KEY)),
            headers={
                'kid': RSA_PRIVATE_JWT_KEY['kid'],
            },
            algorithm='RS256',
            payload={
                'aud': AUTH_KEY,
                'auth_time': AUTH_TIME,
                'country': 'Axphain',
                'emails': [
                    'foobar@example.com'
                ],
                'exp': EXPIRES_ON,
                'family_name': 'Bar',
                'given_name': 'Foo',
                'iat': AUTH_TIME,
                'iss': 'https://login.microsoftonline.com/9a9a9a9a-1111-5555-0000-bc24adfdae00/v2.0/',
                'name': 'FooBar',
                'nbf': AUTH_TIME,
                'oid': '11223344-5566-7788-9999-aabbccddeeff',
                'postalCode': '00000',
                'sub': '11223344-5566-7788-9999-aabbccddeeff',
                'tfp': 'B2C_1_SignIn',
                'ver': '1.0',
        }).decode('ascii'),
        'expires_in': EXPIRES_IN,
        'expires_on': EXPIRES_ON,
        'not_before': AUTH_TIME,
    })

    def extra_settings(self):
        settings = super(AzureADOAuth2Test, self).extra_settings()
        settings.update({
            'SOCIAL_AUTH_' + self.name + '_POLICY': 'b2c_1_signin',
            'SOCIAL_AUTH_' + self.name + '_KEY': self.AUTH_KEY,
            'SOCIAL_AUTH_' + self.name + '_TENANT_ID': 'footenant.onmicrosoft.com',
        })
        return settings

    def setUp(self):
        super(AzureADOAuth2Test, self).setUp()

        keys_url = 'https://login.microsoftonline.com/footenant.onmicrosoft.com/discovery/v2.0/keys?p=b2c_1_signin'
        keys_body = json.dumps({
            'keys': [{
                # Dummy public key that pairs with `access_token_body` key:
                # https://github.com/jpadilla/pyjwt/blob/06f461a/tests/keys/jwk_rsa_pub.json
                'kty': 'RSA',
                'kid': 'bilbo.baggins@hobbiton.example',
                'use': 'sig',
                'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-X'
                     'V2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_Ns'
                     'YOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHY'
                     'pPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCu'
                     'EHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_'
                     'mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw',
                'e': 'AQAB',
        }],
        })
        HTTPretty.register_uri(HTTPretty.GET, keys_url, status=200, body=keys_body)

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

    def test_refresh_token(self):
        user, social = self.do_refresh_token()
        self.assertEqual(social.extra_data['access_token'], 'foobar-new-token')


import json

from jose import jwt
from httpretty import HTTPretty

from .oauth import OAuth2Test

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
    'kid': 'foobar',
    'alg': 'RS256',
    'n': 'pUfcJ8WFrVue98Ygzb6KEQXHBzi8HavCu8VENB2As943--bHPcQ-nScXnrRFAUg8' \
         'H5ZltuOcHWvsGw_AQifSLmOCSWJAPkdNb0w0QzY7Re8NrPjCsP58Tytp5LicF0Ao' \
         'Ag28UK3JioY9hXHGvdZsWR1Rp3I-Z3nRBP6HyO18pEgcZ91c9aAzsqu80An9X4DA' \
         'b1lExtZorvcd5yTBzZgr-MUeytVRni2lDNEpa6OFuopHXmg27Hn3oWAaQlbymd4g' \
         'ifc01oahcwl3ze2tMK6gJxa_TdCf1y99Yq6oilmVvZJ8kwWWnbPE-oDmOVPVnEyT' \
         'vYVCvN4rBT1DQ-x0F1mo2Q'
}

JWK_PUBLIC_KEY = {key: value for key, value in JWK_KEY.items() if key != 'd'}

DOMAIN = 'foobar.auth0.com'


class Auth0OAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.auth0.Auth0OAuth2'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'expires_in': 86400,
        'id_token': jwt.encode({
            'nickname': 'foobar',
            'email': 'foobar@auth0.com',
            'name': 'John Doe',
            'picture': 'http://example.com/image.png',
            'sub': '123456',
            'iss': 'https://{}/'.format(DOMAIN),
        }, JWK_KEY, algorithm='RS256')
    })
    expected_username = 'foobar'
    jwks_url = 'https://foobar.auth0.com/.well-known/jwks.json'

    def extra_settings(self):
        settings = super(Auth0OAuth2Test, self).extra_settings()
        settings['SOCIAL_AUTH_' + self.name + '_DOMAIN'] = DOMAIN
        return settings

    def auth_handlers(self, start_url):
        HTTPretty.register_uri(HTTPretty.GET,
                               self.jwks_url,
                               body=json.dumps({'keys': [JWK_PUBLIC_KEY]}),
                               content_type='application/json')
        return super(Auth0OAuth2Test, self).auth_handlers(start_url)

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

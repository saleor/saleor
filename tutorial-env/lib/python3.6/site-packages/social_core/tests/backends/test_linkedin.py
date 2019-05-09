import json

from six.moves.urllib_parse import urlencode


from .oauth import OAuth1Test, OAuth2Test


class BaseLinkedinTest(object):
    user_data_url = 'https://api.linkedin.com/v1/people/~:' \
                        '(first-name,id,last-name)'
    expected_username = 'FooBar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'lastName': 'Bar',
        'id': '1010101010',
        'firstName': 'Foo'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class LinkedinOAuth1Test(BaseLinkedinTest, OAuth1Test):
    backend_path = 'social_core.backends.linkedin.LinkedinOAuth'
    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
        'oauth_callback_confirmed': 'true'
    })


class LinkedinOAuth2Test(BaseLinkedinTest, OAuth2Test):
    backend_path = 'social_core.backends.linkedin.LinkedinOAuth2'


class LinkedinMobileOAuth2Test(BaseLinkedinTest, OAuth2Test):
    backend_path = 'social_core.backends.linkedin.LinkedinMobileOAuth2'

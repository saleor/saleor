import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class ReadabilityOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.readability.ReadabilityOAuth'
    user_data_url = 'https://www.readability.com/api/rest/v1/users/_current'
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
    user_data_body = json.dumps({
        'username': 'foobar',
        'first_name': 'Foo',
        'last_name': 'Bar',
        'has_active_subscription': False,
        'tags': [],
        'is_publisher': False,
        'email_into_address': 'foobar+sharp@inbox.readability.com',
        'kindle_email_address': None,
        'avatar_url': 'https://secure.gravatar.com/avatar/'
                      '5280f15cedf540b544eecc30fcf3027c?d='
                      'https://www.readability.com/media/images/'
                      'avatar.png&s=36',
        'date_joined': '2013-03-18 02:51:02'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class SkyrockOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.skyrock.SkyrockOAuth'
    user_data_url = 'https://api.skyrock.com/v2/user/get.json'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
    })
    user_data_body = json.dumps({
        'locale': 'en_US',
        'city': '',
        'has_blog': False,
        'web_messager_enabled': True,
        'email': 'foo@bar.com',
        'username': 'foobar',
        'firstname': 'Foo',
        'user_url': '',
        'address1': '',
        'address2': '',
        'has_profile': False,
        'allow_messages_from': 'everybody',
        'is_online': False,
        'postalcode': '',
        'lang': 'en',
        'id_user': 10101010,
        'name': 'Bar',
        'gender': 0,
        'avatar_url': 'http://www.skyrock.com/img/avatars/default-0.jpg',
        'nb_friends': 0,
        'country': 'US',
        'birth_date': '1980-06-10'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

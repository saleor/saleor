import json

from .oauth import OAuth2Test


class ChatworkOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.chatwork.ChatworkOAuth2'
    user_data_url = 'https://api.chatwork.com/v2/me'
    expected_username = 'hogehoge'
    access_token_body = json.dumps({
        'access_token': 'pyopyopyopyopyopyopyopyopyopyo',
        'token_type': 'Bearer',
        'expires_in': '1501138041000',
        'refresh_token': 'pyopyopyopyopyopyo',
        'scope': 'rooms.all:read_write'
    })

    user_data_body = json.dumps({
        'account_id': 123,
        'room_id': 322,
        'name': 'Foo Bar',
        'chatwork_id': 'hogehoge',
        'organization_id': 101,
        'organization_name': 'Foo foobar',
        'department': 'Support',
        'title': 'CMO',
        'url': 'http://www.example.com',
        'introduction': '',
        'mail': 'hogehoge@example.com',
        'tel_organization': '',
        'tel_extension': '',
        'tel_mobile': '',
        'skype': '',
        'facebook': '',
        'twitter': '',
        'avatar_image_url': 'https://www.example.com/hogehoge.jpg',
        'login_mail': 'hogehoge@example.com'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

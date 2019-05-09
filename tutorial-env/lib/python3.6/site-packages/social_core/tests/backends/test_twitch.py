import json
from .oauth import OAuth2Test


class TwitchOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.twitch.TwitchOAuth2'
    user_data_url = 'https://api.twitch.tv/kraken/user/'
    expected_username = 'test_user1'
    access_token_body = json.dumps({
        'access_token': 'foobar',
    })
    user_data_body = json.dumps({
        'type': 'user',
        'name': 'test_user1',
        'created_at': '2011-06-03T17:49:19Z',
        'updated_at': '2012-06-18T17:19:57Z',
        '_links': {
            'self': 'https://api.twitch.tv/kraken/users/test_user1'
        },
        'logo': 'http://static-cdn.jtvnw.net/jtv_user_pictures/'
                'test_user1-profile_image-62e8318af864d6d7-300x300.jpeg',
        '_id': 22761313,
        'display_name': 'test_user1',
        'email': 'asdf@asdf.com',
        'partnered': True,
        'bio': 'test bio woo I\'m a test user'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

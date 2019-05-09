import json

from .oauth import OAuth2Test


class SpotifyOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.spotify.SpotifyOAuth2'
    user_data_url = 'https://api.spotify.com/v1/me'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'display_name': None,
        'external_urls': {
            'spotify': 'https://open.spotify.com/user/foobar'
        },
        'followers': {
            'href': None,
            'total': 0
        },
        'href': 'https://api.spotify.com/v1/users/foobar',
        'id': 'foobar',
        'images': [],
        'type': 'user',
        'uri': 'spotify:user:foobar'
        })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

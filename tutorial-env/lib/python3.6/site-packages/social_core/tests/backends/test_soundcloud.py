import json

from .oauth import OAuth2Test


class SoundcloudOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.soundcloud.SoundcloudOAuth2'
    user_data_url = 'https://api.soundcloud.com/me.json'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'website': None,
        'myspace_name': None,
        'public_favorites_count': 0,
        'followings_count': 0,
        'full_name': 'Foo Bar',
        'id': 10101010,
        'city': None,
        'track_count': 0,
        'playlist_count': 0,
        'discogs_name': None,
        'private_tracks_count': 0,
        'followers_count': 0,
        'online': True,
        'username': 'foobar',
        'description': None,
        'subscriptions': [],
        'kind': 'user',
        'quota': {
            'unlimited_upload_quota': False,
            'upload_seconds_left': 7200,
            'upload_seconds_used': 0
        },
        'website_title': None,
        'primary_email_confirmed': False,
        'permalink_url': 'http://soundcloud.com/foobar',
        'private_playlists_count': 0,
        'permalink': 'foobar',
        'upload_seconds_left': 7200,
        'country': None,
        'uri': 'https://api.soundcloud.com/users/10101010',
        'avatar_url': 'https://a1.sndcdn.com/images/'
                      'default_avatar_large.png?ca77017',
        'plan': 'Free'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

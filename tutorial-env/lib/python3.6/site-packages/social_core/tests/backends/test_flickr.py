from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class FlickrOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.flickr.FlickrOAuth'
    expected_username = 'foobar'
    access_token_body = urlencode({
        'oauth_token_secret': 'a-secret',
        'username': 'foobar',
        'oauth_token': 'foobar',
        'user_nsid': '10101010@N01'
    })
    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
        'oauth_callback_confirmed': 'true'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

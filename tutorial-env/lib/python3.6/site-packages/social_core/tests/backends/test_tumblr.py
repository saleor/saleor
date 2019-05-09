import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class TumblrOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.tumblr.TumblrOAuth'
    user_data_url = 'http://api.tumblr.com/v2/user/info'
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
        'meta': {
            'status': 200,
            'msg': 'OK'
        },
        'response': {
            'user': {
                'following': 1,
                'blogs': [{
                    'updated': 0,
                    'description': '',
                    'drafts': 0,
                    'title': 'Untitled',
                    'url': 'http://foobar.tumblr.com/',
                    'messages': 0,
                    'tweet': 'N',
                    'share_likes': True,
                    'posts': 0,
                    'primary': True,
                    'queue': 0,
                    'admin': True,
                    'followers': 0,
                    'ask': False,
                    'facebook': 'N',
                    'type': 'public',
                    'facebook_opengraph_enabled': 'N',
                    'name': 'foobar'
                }],
                'default_post_format': 'html',
                'name': 'foobar',
                'likes': 0
            }
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

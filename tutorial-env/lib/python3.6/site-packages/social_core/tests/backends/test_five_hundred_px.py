import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class FiveHundredPxOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.five_hundred_px.FiveHundredPxOAuth'
    user_data_url = 'https://api.500px.com/v1/users'
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
        'user': {
            'id': 10101010,
            'username': 'foobar',
            'firstname': '',
            'lastname': '',
            'birthday': None,
            'sex': 1,
            'city': '',
            'state': '',
            'country': '',
            'registration_date': '2011-11-11T00:00:00-00:00',
            'about': '',
            'usertype': 0,
            'domain': 'UserName.500px.com',
            'fotomoto_on': False,
            'locale': 'en',
            'show_nude': False,
            'allow_sale_requests': 1,
            'fullname': 'UserName',
            'userpic_url': 'https://graph.facebook.com/v2.7/'
                           '1000000000/picture?height=100&width=100',
            'userpic_https_url': 'https://graph.facebook.com/v2.7/'
                                 '1000000000/picture?'
                                 'height=100&width=100',
            'cover_url': None,
            'upgrade_status': 0,
            'store_on': False,
            'photos_count': 0,
            'galleries_count': 0,
            'affection': 51,
            'in_favorites_count': 0,
            'friends_count': 2,
            'followers_count': 3,
            'analytics_code': None,
            'invite_pending': False,
            'invite_accepted': False,
            'email': 'user@user.com',
            'shadow_email': 'user@user.com',
            'upload_limit': 20,
            'upload_limit_expiry': '2021-11-11T00:00:00-00:00',
            'upgrade_type': 0,
            'upgrade_status_expiry': '2011-11-21',
            'portfolio_enabled': False,
            'auth': {
                'facebook': 1,
                'twitter': 0,
                'google_oauth2': 1
            },
            'presubmit_for_licensing': None,
            'contacts': {
                'facebook': '1000000000'
            },
            'equipment': {},
            'avatars': {
                'default': {
                    'http': 'https://graph.facebook.com/v2.7/'
                            '1000000000/picture?height=100&width=100',
                    'https': 'https://graph.facebook.com/v2.7/'
                             '1000000000/picture?height=100&width=100'
                },
                'large': {
                    'http': 'https://graph.facebook.com/v2.7/'
                            '1000000000/picture?height=100&width=100',
                    'https': 'https://graph.facebook.com/v2.7/'
                             '1000000000/picture?height=100&width=100'
                },
                'small': {
                    'http': 'https://graph.facebook.com/v2.7/'
                            '1000000000/picture?height=100&width=100',
                    'https': 'https://graph.facebook.com/v2.7/'
                             '1000000000/picture?height=100&width=100'
                },
                'tiny': {
                    'http': 'https://graph.facebook.com/v2.7/'
                            '1000000000/picture?height=100&width=100',
                    'https': 'https://graph.facebook.com/v2.7/'
                             '1000000000/picture?height=100&width=100'
                }
            }
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

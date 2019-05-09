import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class TwitterOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.twitter.TwitterOAuth'
    user_data_url = 'https://api.twitter.com/1.1/account/' \
                        'verify_credentials.json'
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
        'follow_request_sent': False,
        'profile_use_background_image': True,
        'id': 10101010,
        'description': 'Foo bar baz qux',
        'verified': False,
        'entities': {
            'description': {
                'urls': []
            }
        },
        'profile_image_url_https': 'https://twimg0-a.akamaihd.net/'
                                   'profile_images/532018826/'
                                   'n587119531_1939735_9305_normal.jpg',
        'profile_sidebar_fill_color': '252429',
        'profile_text_color': '666666',
        'followers_count': 77,
        'profile_sidebar_border_color': '181A1E',
        'location': 'Fooland',
        'default_profile_image': False,
        'listed_count': 4,
        'status': {
            'favorited': False,
            'contributors': None,
            'retweeted_status': {
                'favorited': False,
                'contributors': None,
                'truncated': False,
                'source': 'web',
                'text': '"Foo foo foo foo',
                'created_at': 'Fri Dec 21 18:12:00 +0000 2012',
                'retweeted': True,
                'in_reply_to_status_id': None,
                'coordinates': None,
                'id': 101010101010101010,
                'entities': {
                    'user_mentions': [],
                    'hashtags': [],
                    'urls': []
                },
                'in_reply_to_status_id_str': None,
                'place': None,
                'id_str': '101010101010101010',
                'in_reply_to_screen_name': None,
                'retweet_count': 8,
                'geo': None,
                'in_reply_to_user_id_str': None,
                'in_reply_to_user_id': None
            },
            'truncated': False,
            'source': 'web',
            'text': 'RT @foo: "Foo foo foo foo',
            'created_at': 'Fri Dec 21 18:24:10 +0000 2012',
            'retweeted': True,
            'in_reply_to_status_id': None,
            'coordinates': None,
            'id': 101010101010101010,
            'entities': {
                'user_mentions': [{
                    'indices': [3, 10],
                    'id': 10101010,
                    'screen_name': 'foo',
                    'id_str': '10101010',
                    'name': 'Foo'
                }],
                'hashtags': [],
                'urls': []
            },
            'in_reply_to_status_id_str': None,
            'place': None,
            'id_str': '101010101010101010',
            'in_reply_to_screen_name': None,
            'retweet_count': 8,
            'geo': None,
            'in_reply_to_user_id_str': None,
            'in_reply_to_user_id': None
        },
        'utc_offset': -10800,
        'statuses_count': 191,
        'profile_background_color': '1A1B1F',
        'friends_count': 151,
        'profile_background_image_url_https': 'https://twimg0-a.akamaihd.net/'
                                              'images/themes/theme9/bg.gif',
        'profile_link_color': '2FC2EF',
        'profile_image_url': 'http://a0.twimg.com/profile_images/532018826/'
                             'n587119531_1939735_9305_normal.jpg',
        'is_translator': False,
        'geo_enabled': False,
        'id_str': '74313638',
        'profile_background_image_url': 'http://a0.twimg.com/images/themes/'
                                        'theme9/bg.gif',
        'screen_name': 'foobar',
        'lang': 'en',
        'profile_background_tile': False,
        'favourites_count': 2,
        'name': 'Foo',
        'notifications': False,
        'url': None,
        'created_at': 'Tue Sep 15 00:26:17 +0000 2009',
        'contributors_enabled': False,
        'time_zone': 'Buenos Aires',
        'protected': False,
        'default_profile': False,
        'following': False
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class TwitterOAuth1IncludeEmailTest(OAuth1Test):
    backend_path = 'social_core.backends.twitter.TwitterOAuth'
    user_data_url = 'https://api.twitter.com/1.1/account/' \
                        'verify_credentials.json?include_email=true'
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
        'follow_request_sent': False,
        'profile_use_background_image': True,
        'id': 10101010,
        'description': 'Foo bar baz qux',
        'verified': False,
        'entities': {
            'description': {
                'urls': []
            }
        },
        'profile_image_url_https': 'https://twimg0-a.akamaihd.net/'
                                   'profile_images/532018826/'
                                   'n587119531_1939735_9305_normal.jpg',
        'profile_sidebar_fill_color': '252429',
        'profile_text_color': '666666',
        'followers_count': 77,
        'profile_sidebar_border_color': '181A1E',
        'location': 'Fooland',
        'default_profile_image': False,
        'listed_count': 4,
        'status': {
            'favorited': False,
            'contributors': None,
            'retweeted_status': {
                'favorited': False,
                'contributors': None,
                'truncated': False,
                'source': 'web',
                'text': '"Foo foo foo foo',
                'created_at': 'Fri Dec 21 18:12:00 +0000 2012',
                'retweeted': True,
                'in_reply_to_status_id': None,
                'coordinates': None,
                'id': 101010101010101010,
                'entities': {
                    'user_mentions': [],
                    'hashtags': [],
                    'urls': []
                },
                'in_reply_to_status_id_str': None,
                'place': None,
                'id_str': '101010101010101010',
                'in_reply_to_screen_name': None,
                'retweet_count': 8,
                'geo': None,
                'in_reply_to_user_id_str': None,
                'in_reply_to_user_id': None
            },
            'truncated': False,
            'source': 'web',
            'text': 'RT @foo: "Foo foo foo foo',
            'created_at': 'Fri Dec 21 18:24:10 +0000 2012',
            'retweeted': True,
            'in_reply_to_status_id': None,
            'coordinates': None,
            'id': 101010101010101010,
            'entities': {
                'user_mentions': [{
                    'indices': [3, 10],
                    'id': 10101010,
                    'screen_name': 'foo',
                    'id_str': '10101010',
                    'name': 'Foo'
                }],
                'hashtags': [],
                'urls': []
            },
            'in_reply_to_status_id_str': None,
            'place': None,
            'id_str': '101010101010101010',
            'in_reply_to_screen_name': None,
            'retweet_count': 8,
            'geo': None,
            'in_reply_to_user_id_str': None,
            'in_reply_to_user_id': None
        },
        'utc_offset': -10800,
        'statuses_count': 191,
        'profile_background_color': '1A1B1F',
        'friends_count': 151,
        'profile_background_image_url_https': 'https://twimg0-a.akamaihd.net/'
                                              'images/themes/theme9/bg.gif',
        'profile_link_color': '2FC2EF',
        'profile_image_url': 'http://a0.twimg.com/profile_images/532018826/'
                             'n587119531_1939735_9305_normal.jpg',
        'is_translator': False,
        'geo_enabled': False,
        'id_str': '74313638',
        'profile_background_image_url': 'http://a0.twimg.com/images/themes/'
                                        'theme9/bg.gif',
        'screen_name': 'foobar',
        'lang': 'en',
        'profile_background_tile': False,
        'favourites_count': 2,
        'name': 'Foo',
        'notifications': False,
        'url': None,
        'created_at': 'Tue Sep 15 00:26:17 +0000 2009',
        'contributors_enabled': False,
        'time_zone': 'Buenos Aires',
        'protected': False,
        'default_profile': False,
        'following': False,
        'email': 'foo@bar.bas'
    })

    def test_login(self):
        user = self.do_login()
        self.assertEquals(user.email, 'foo@bar.bas')

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

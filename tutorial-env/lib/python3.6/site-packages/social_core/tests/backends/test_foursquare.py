import json

from .oauth import OAuth2Test


class FoursquareOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.foursquare.FoursquareOAuth2'
    user_data_url = 'https://api.foursquare.com/v2/users/self'
    expected_username = 'FooBar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'notifications': [{
            'item': {
                'unreadCount': 0
            },
            'type': 'notificationTray'
        }],
        'meta': {
            'errorType': 'deprecated',
            'code': 200,
            'errorDetail': 'Please provide an API version to avoid future '
                           'errors.See http://bit.ly/vywCav'
        },
        'response': {
            'user': {
                'photo': 'https://is0.4sqi.net/userpix_thumbs/'
                         'BYKIT01VN4T4BISN.jpg',
                'pings': False,
                'homeCity': 'Foo, Bar',
                'id': '1010101',
                'badges': {
                    'count': 0,
                    'items': []
                },
                'friends': {
                    'count': 1,
                    'groups': [{
                        'count': 0,
                        'items': [],
                        'type': 'friends',
                        'name': 'Mutual friends'
                    }, {
                        'count': 1,
                        'items': [{
                            'bio': '',
                            'gender': 'male',
                            'firstName': 'Baz',
                            'relationship': 'friend',
                            'photo': 'https://is0.4sqi.net/userpix_thumbs/'
                                     'BYKIT01VN4T4BISN.jpg',
                            'lists': {
                                'groups': [{
                                    'count': 1,
                                    'items': [],
                                    'type': 'created'
                                }]
                            },
                            'homeCity': 'Baz, Qux',
                            'lastName': 'Qux',
                            'tips': {
                                'count': 0
                            },
                            'id': '10101010'
                        }],
                        'type': 'others',
                        'name': 'Other friends'
                    }]
                },
                'referralId': 'u-1010101',
                'tips': {
                    'count': 0
                },
                'type': 'user',
                'todos': {
                    'count': 0
                },
                'bio': '',
                'relationship': 'self',
                'lists': {
                    'groups': [{
                        'count': 1,
                        'items': [],
                        'type': 'created'
                    }]
                },
                'photos': {
                    'count': 0,
                    'items': []
                },
                'checkinPings': 'off',
                'scores': {
                    'max': 0,
                    'checkinsCount': 0,
                    'goal': 50,
                    'recent': 0
                },
                'checkins': {
                    'count': 0
                },
                'firstName': 'Foo',
                'gender': 'male',
                'contact': {
                    'email': 'foo@bar.com'
                },
                'lastName': 'Bar',
                'following': {
                    'count': 0
                },
                'requests': {
                    'count': 0
                },
                'mayorships': {
                    'count': 0,
                    'items': []
                }
            }
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

import json

from .oauth import OAuth2Test


class DisqusOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.disqus.DisqusOAuth2'
    user_data_url = 'https://disqus.com/api/3.0/users/details.json'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'code': 0,
        'response': {
            'username': 'foobar',
            'numFollowers': 0,
            'isFollowing': False,
            'numFollowing': 0,
            'name': 'Foo Bar',
            'numPosts': 0,
            'url': '',
            'isAnonymous': False,
            'rep': 1.231755,
            'about': '',
            'isFollowedBy': False,
            'connections': {},
            'emailHash': '5280f14cedf530b544aecc31fcfe0240',
            'reputation': 1.231755,
            'avatar': {
                'small': {
                    'permalink': 'https://disqus.com/api/users/avatars/'
                                 'foobar.jpg',
                    'cache': 'https://securecdn.disqus.com/uploads/'
                             'users/453/4556/avatar32.jpg?1285535379'
                },
                'isCustom': False,
                'permalink': 'https://disqus.com/api/users/avatars/foobar.jpg',
                'cache': 'https://securecdn.disqus.com/uploads/users/453/'
                         '4556/avatar92.jpg?1285535379',
                'large': {
                    'permalink': 'https://disqus.com/api/users/avatars/'
                                 'foobar.jpg',
                    'cache': 'https://securecdn.disqus.com/uploads/users/'
                             '453/4556/avatar92.jpg?1285535379'
                }
            },
            'profileUrl': 'http://disqus.com/foobar/',
            'numLikesReceived': 0,
            'isPrimary': True,
            'joinedAt': '2010-09-26T21:09:39',
            'id': '1010101',
            'location': ''
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

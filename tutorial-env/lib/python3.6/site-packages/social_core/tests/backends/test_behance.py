import json

from .oauth import OAuth2Test


class BehanceOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.behance.BehanceOAuth2'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'valid': 1,
        'user': {
            'username': 'foobar',
            'city': 'Foo City',
            'first_name': 'Foo',
            'last_name': 'Bar',
            'display_name': 'Foo Bar',
            'url': 'http://www.behance.net/foobar',
            'country': 'Fooland',
            'company': '',
            'created_on': 1355152329,
            'state': '',
            'fields': [
                'Programming',
                'Web Design',
                'Web Development'
            ],
            'images': {
                '32': 'https://www.behance.net/assets/img/profile/'
                      'no-image-32.jpg',
                '50': 'https://www.behance.net/assets/img/profile/'
                      'no-image-50.jpg',
                '115': 'https://www.behance.net/assets/img/profile/'
                       'no-image-138.jpg',
                '129': 'https://www.behance.net/assets/img/profile/'
                       'no-image-138.jpg',
                '138': 'https://www.behance.net/assets/img/profile/'
                       'no-image-138.jpg',
                '78': 'https://www.behance.net/assets/img/profile/'
                      'no-image-78.jpg'
            },
            'id': 1010101,
            'occupation': 'Software Developer'
        }
    })
    expected_username = 'foobar'

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

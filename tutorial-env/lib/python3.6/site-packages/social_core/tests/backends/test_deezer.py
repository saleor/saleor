import json

from .oauth import OAuth2Test


class DeezerOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.deezer.DeezerOAuth2'
    user_data_url = 'http://api.deezer.com/user/me'
    expected_username = 'foobar'
    access_token_body = 'access_token=foobar&expires=0'
    user_data_body = json.dumps({
        'id': '1',
        'name': 'foobar',
        'lastname': '',
        'firstname': '',
        'status': 0,
        'birthday': '1970-01-01',
        'inscription_date': '2015-01-01',
        'gender': 'M',
        'link': 'https://www.deezer.com/profile/1',
        'picture': 'https://api.deezer.com/user/1/image',
        'picture_small': 'https://cdns-images.dzcdn.net/images/user//56x56-000000-80-0-0.jpg',
        'picture_medium': 'https://cdns-images.dzcdn.net/images/user//250x250-000000-80-0-0.jpg',
        'picture_big': 'https://cdns-images.dzcdn.net/images/user//500x500-000000-80-0-0.jpg',
        'country': 'FR',
        'lang': 'FR',
        'is_kid': False,
        'tracklist': 'https://api.deezer.com/user/1/flow',
        'type': 'user'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

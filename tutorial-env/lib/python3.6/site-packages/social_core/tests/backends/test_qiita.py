import json

from .oauth import OAuth2Test


class QiitaOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.qiita.QiitaOAuth2'
    user_data_url = 'https://qiita.com/api/v2/authenticated_user'
    expected_username = 'foobar'

    access_token_body = json.dumps({
        'token': 'foobar',
        'token_type': 'bearer'
    })

    user_data_body = json.dumps({
        'id': 'foobar',
        'name': 'Foo Bar'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

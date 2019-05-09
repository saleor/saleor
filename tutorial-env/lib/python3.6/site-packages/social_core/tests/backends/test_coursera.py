import json

from .oauth import OAuth2Test


class CourseraOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.coursera.CourseraOAuth2'
    user_data_url = \
        'https://api.coursera.org/api/externalBasicProfiles.v1?q=me'
    expected_username = '560e7ed2076e0d589e88bd74b6aad4b7'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'Bearer',
        'expires_in': 1795
    })
    request_token_body = json.dumps({
        'code': 'foobar-code',
        'client_id': 'foobar-client-id',
        'client_secret': 'foobar-client-secret',
        'redirect_uri': 'http://localhost:8000/accounts/coursera/',
        'grant_type': 'authorization_code'
    })
    user_data_body = json.dumps({
        'token_type': 'Bearer',
        'paging': None,
        'elements': [{
            'id': '560e7ed2076e0d589e88bd74b6aad4b7'
        }],
        'access_token': 'foobar',
        'expires_in': 1800,
        'linked': None
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

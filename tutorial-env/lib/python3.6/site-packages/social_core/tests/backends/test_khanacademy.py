import json

from six.moves.urllib_parse import urlencode


from .oauth import OAuth1Test


class KhanAcademyOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.khanacademy.KhanAcademyOAuth1'
    user_data_url = 'https://www.khanacademy.org/api/v1/user'
    expected_username = 'foo@bar.com'
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
        "email": "foo@bar.com",
        "user_id": "http://googleid.khanacademy.org/11111111111111",
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

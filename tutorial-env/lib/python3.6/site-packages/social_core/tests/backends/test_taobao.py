import json

from .oauth import OAuth2Test


class TaobaoOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.taobao.TAOBAOAuth'
    user_data_url = 'https://eco.taobao.com/router/rest'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'w2_expires_in': 0,
        'taobao_user_id': '1',
        'taobao_user_nick': 'foobar',
        'w1_expires_in': 1800,
        're_expires_in': 0,
        'r2_expires_in': 0,
        'expires_in': 86400,
        'r1_expires_in': 1800
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

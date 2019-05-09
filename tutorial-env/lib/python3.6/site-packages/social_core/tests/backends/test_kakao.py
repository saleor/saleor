import json

from .oauth import OAuth2Test


class KakaoOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.kakao.KakaoOAuth2'
    user_data_url = 'https://kapi.kakao.com/v1/user/me'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar'
    })
    user_data_body = json.dumps({
        'id': '101010101',
        'properties': {
            'nickname': 'foobar',
            'thumbnail_image': 'http://mud-kage.kakao.co.kr/14/dn/btqbh1AKmRf/'
                               'ujlHpQhxtMSbhKrBisrxe1/o.jpg',
            'profile_image': 'http://mud-kage.kakao.co.kr/14/dn/btqbjCnl06Q/'
                             'wbMJSVAUZB7lzSImgGdsoK/o.jpg'
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

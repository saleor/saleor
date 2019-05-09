from xml.dom import minidom

from .oauth import BaseOAuth2


class NaverOAuth2(BaseOAuth2):
    """Naver OAuth authentication backend"""
    name = 'naver'
    AUTHORIZATION_URL = 'https://nid.naver.com/oauth2.0/authorize'
    ACCESS_TOKEN_URL = 'https://nid.naver.com/oauth2.0/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('id', 'id'),
    ]

    def get_user_id(self, details, response):
        return response.get('id')

    def get_user_details(self, response):
        """Return user details from Naver account"""
        return {
            'username': response.get('username'),
            'email': response.get('email'),
            'fullname': response.get('username'),
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        response = self.request(
            'https://openapi.naver.com/v1/nid/getUserProfile.xml',
            headers={
                'Authorization': 'Bearer {0}'.format(access_token),
                'Content_Type': 'text/xml'
            }
        )

        dom = minidom.parseString(response.text.encode('utf-8').strip())

        return {
            'id': self._dom_value(dom, 'id'),
            'email': self._dom_value(dom, 'email'),
            'username': self._dom_value(dom, 'name'),
            'nickname': self._dom_value(dom, 'nickname'),
            'gender': self._dom_value(dom, 'gender'),
            'age': self._dom_value(dom, 'age'),
            'birthday': self._dom_value(dom, 'birthday'),
            'profile_image': self._dom_value(dom, 'profile_image')
        }

    def auth_headers(self):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',
            'code': self.data.get('code'),
            'client_id': client_id,
            'client_secret': client_secret,
        }

    def _dom_value(self, dom, key):
        return dom.getElementsByTagName(key)[0].childNodes[0].data

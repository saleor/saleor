from .oauth import BaseOAuth2


class WunderlistOAuth2(BaseOAuth2):
    """Wunderlist OAuth2 authentication backend"""
    name = 'wunderlist'
    AUTHORIZATION_URL = 'https://www.wunderlist.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.wunderlist.com/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def get_user_details(self, response):
        """Return user details from Wunderlist account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name')
        )
        return {'username': str(response.get('id')),
                'email': response.get('email'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        headers = {
            'X-Access-Token': access_token,
            'X-Client-ID': self.setting('KEY')}
        return self.get_json(
            'https://a.wunderlist.com/api/v1/user', headers=headers)

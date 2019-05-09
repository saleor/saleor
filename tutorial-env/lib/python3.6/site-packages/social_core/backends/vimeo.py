from .oauth import BaseOAuth1, BaseOAuth2


class VimeoOAuth1(BaseOAuth1):
    """Vimeo OAuth authentication backend"""
    name = 'vimeo'
    AUTHORIZATION_URL = 'https://vimeo.com/oauth/authorize'
    REQUEST_TOKEN_URL = 'https://vimeo.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://vimeo.com/oauth/access_token'

    def get_user_id(self, details, response):
        return response.get('person', {}).get('id')

    def get_user_details(self, response):
        """Return user details from Twitter account"""
        person = response.get('person', {})
        fullname, first_name, last_name = self.get_user_names(
            person.get('display_name', '')
        )
        return {'username': person.get('username', ''),
                'email': '',
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        return self.get_json(
            'https://vimeo.com/api/rest/v2',
            params={'format': 'json', 'method': 'vimeo.people.getInfo'},
            auth=self.oauth_auth(access_token)
        )


class VimeoOAuth2(BaseOAuth2):
    """Vimeo OAuth2 authentication backend"""
    name = 'vimeo-oauth2'
    AUTHORIZATION_URL = 'https://api.vimeo.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.vimeo.com/oauth/access_token'
    REFRESH_TOKEN_URL = 'https://api.vimeo.com/oauth/request_token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ','
    API_ACCEPT_HEADER = {'Accept': 'application/vnd.vimeo.*+json;version=3.0'}

    def get_redirect_uri(self, state=None):
        """
        Build redirect with redirect_state parameter.

        @Vimeo API 3 requires exact redirect uri without additional
        additional state parameter included
        """
        return self.redirect_uri

    def get_user_id(self, details, response):
        """Return user id"""
        try:
            user_id = response.get('user', {})['uri'].split('/')[-1]
        except KeyError:
            user_id = None
        return user_id

    def get_user_details(self, response):
        """Return user details from account"""
        user = response.get('user', {})
        fullname, first_name, last_name = self.get_user_names(
            user.get('name', '')
        )
        return {'username': fullname,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        return self.get_json(
            'https://api.vimeo.com/me',
            params={'access_token': access_token},
            headers=VimeoOAuth2.API_ACCEPT_HEADER,
        )

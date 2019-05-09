from .oauth import BaseOAuth2


class UniverseOAuth2(BaseOAuth2):
    """Universe Ticketing OAuth2 authentication backend"""
    name = 'universe'
    AUTHORIZATION_URL = 'https://www.universe.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.universe.com/oauth/token'
    BASE_API_URL = 'https://www.universe.com/api'
    USER_INFO_URL = BASE_API_URL + '/v2/current_user'
    ACCESS_TOKEN_METHOD = 'POST'
    STATE_PARAMETER = True
    REDIRECT_STATE = True
    EXTRA_DATA = [
        ('id', 'id'),
        ('slug', 'slug'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

    def get_user_id(self, details, response):
        return response['current_user'][self.ID_KEY]

    def get_user_details(self, response):
        """Return user details from a Universe account"""
        # Start with the user data as it was returned
        user_details = response['current_user']
        user_details['username'] = user_details['email']
        return user_details

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(self.USER_INFO_URL, headers={
            'Authorization': 'Bearer {}'.format(access_token)
        })

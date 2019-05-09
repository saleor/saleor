from .oauth import BaseOAuth2


class GoClioOAuth2(BaseOAuth2):
    name = 'goclio'
    AUTHORIZATION_URL = 'https://app.goclio.com/oauth/authorize/'
    ACCESS_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = 'https://app.goclio.com/oauth/token/'
    REDIRECT_STATE = False
    STATE_PARAMETER = False

    def get_user_details(self, response):
        """Return user details from GoClio account"""
        user = response.get('user', {})
        username = user.get('id', None)
        email = user.get('email', None)
        first_name, last_name = (user.get('first_name', None),
                                 user.get('last_name', None))
        fullname = '%s %s' % (first_name, last_name)

        return {'username': username,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://app.goclio.com/api/v2/users/who_am_i',
            params={'access_token': access_token}
        )

    def get_user_id(self, details, response):
        return response.get('user', {}).get('id')

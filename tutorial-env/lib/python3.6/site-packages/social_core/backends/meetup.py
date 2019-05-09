"""
Meetup OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/meetup.html
"""
from .oauth import BaseOAuth2


class MeetupOAuth2(BaseOAuth2):
    """Meetup OAuth2 authentication backend"""
    name = 'meetup'
    AUTHORIZATION_URL = 'https://secure.meetup.com/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://secure.meetup.com/oauth2/access'
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['basic']
    SCOPE_SEPARATOR = ','
    REDIRECT_STATE = False
    STATE_PARAMETER = 'state'

    def get_user_details(self, response):
        """Return user details from Meetup account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name')
        )

        return {'username': response.get('username'),
                'email': response.get('email') or '',
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://api.meetup.com/2/member/self',
                             params={'access_token': access_token})

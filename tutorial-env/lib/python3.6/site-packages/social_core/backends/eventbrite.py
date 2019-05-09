from .oauth import BaseOAuth2


class EventbriteOAuth2(BaseOAuth2):
    """Eventbrite OAuth2 authentication backend"""
    name = 'eventbrite'
    AUTHORIZATION_URL = 'https://www.eventbrite.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.eventbrite.com/oauth/token'
    METADATA_URL = 'https://www.eventbriteapi.com/v3/users/me'
    ACCESS_TOKEN_METHOD = 'POST'
    STATE_PARAMETER = False
    REDIRECT_STATE = False

    def get_user_details(self, response):
        """Return user details from an Eventbrite metadata response"""
        email = next(iter(filter(lambda x: x['primary'], response['emails'])))['email']

        return {
            'username': email,
            'email': email,
            'first_name': response['first_name'],
            'last_name': response['last_name']
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data and datacenter information from service"""
        return self.get_json(self.METADATA_URL, headers={
          'Authorization': 'Bearer ' + access_token
        })

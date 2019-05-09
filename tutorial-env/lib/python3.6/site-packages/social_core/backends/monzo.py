from .oauth import BaseOAuth2


class MonzoOAuth2(BaseOAuth2):
    """
    Monzo OAuth2 authentication backend.
    """

    name = 'monzo'

    AUTHORIZATION_URL = 'https://auth.getmondo.co.uk/'
    ACCESS_TOKEN_URL = 'https://api.monzo.com/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            response['accounts'][0]['description'],
        )

        return {
            'username': str(response.get('user_id')),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
        }

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(
            'https://api.monzo.com/accounts',
            headers={'Authorization': 'Bearer {0}'.format(access_token)},
        )

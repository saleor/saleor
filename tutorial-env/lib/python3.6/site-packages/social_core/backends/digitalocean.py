from .oauth import BaseOAuth2


class DigitalOceanOAuth(BaseOAuth2):
    """
    DigitalOcean OAuth authentication backend.

    Docs: https://developers.digitalocean.com/documentation/oauth/
    """
    name = 'digitalocean'
    AUTHORIZATION_URL = 'https://cloud.digitalocean.com/v1/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://cloud.digitalocean.com/v1/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ' '
    EXTRA_DATA = [
        ('expires_in', 'expires_in')
    ]

    def get_user_id(self, details, response):
        """Return user unique id provided by service"""
        return response['account'].get('uuid')

    def get_user_details(self, response):
        """Return user details from DigitalOcean account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name') or '')

        return {'username': response['account'].get('email'),
                'email': response['account'].get('email'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, token, *args, **kwargs):
        """Loads user data from service"""
        url = 'https://api.digitalocean.com/v2/account'
        auth_header = {"Authorization": "Bearer %s" % token}
        try:
            return self.get_json(url, headers=auth_header)
        except ValueError:
            return None

from .oauth import BaseOAuth2


class ClasslinkOAuth(BaseOAuth2):
    """
    Classlink OAuth authentication backend.

    Docs: https://developer.classlink.com/docs/oauth2-workflow
    """
    name = 'classlink'
    AUTHORIZATION_URL = 'https://launchpad.classlink.com/oauth2/v2/auth'
    ACCESS_TOKEN_URL = 'https://launchpad.classlink.com/oauth2/v2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['profile']
    REDIRECT_STATE = False
    SCOPE_SEPARATOR = ' '

    def get_user_id(self, details, response):
        """Return user unique id provided by service"""
        return response['UserId']

    def get_user_details(self, response):
        """Return user details from Classlink account"""
        fullname, first_name, last_name = self.get_user_names(
            first_name=response.get('FirstName'),
            last_name=response.get('LastName')
        )

        return {
            'username': response.get('Email') or response.get('LoginId'),
            'email': response.get('Email'),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
        }

    def user_data(self, token, *args, **kwargs):
        """Loads user data from service"""
        url = 'https://nodeapi.classlink.com/v2/my/info'
        auth_header = {"Authorization": "Bearer %s" % token}
        try:
            return self.get_json(url, headers=auth_header)
        except ValueError:
            return None

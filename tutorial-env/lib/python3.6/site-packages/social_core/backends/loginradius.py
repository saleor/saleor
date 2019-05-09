"""
LoginRadius BaseOAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/loginradius.html
"""
from .oauth import BaseOAuth2


class LoginRadiusAuth(BaseOAuth2):
    """LoginRadius BaseOAuth2 authentication backend."""
    name = 'loginradius'
    ID_KEY = 'ID'
    ACCESS_TOKEN_URL = 'https://api.loginradius.com/api/v2/access_token'
    PROFILE_URL = 'https://api.loginradius.com/api/v2/userprofile'
    ACCESS_TOKEN_METHOD = 'GET'
    REDIRECT_STATE = False
    STATE_PARAMETER = False

    def uses_redirect(self):
        """Return False because we return HTML instead."""
        return False

    def auth_html(self):
        key, secret = self.get_key_and_secret()
        tpl = self.setting('TEMPLATE', 'loginradius.html')
        return self.strategy.render_html(tpl=tpl, context={
            'backend': self,
            'LOGINRADIUS_KEY': key,
            'LOGINRADIUS_REDIRECT_URL': self.get_redirect_uri()
        })

    def request_access_token(self, *args, **kwargs):
        return self.get_json(params={
            'token': self.data.get('token'),
            'secret': self.setting('SECRET')
        }, *args, **kwargs)

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service. Implement in subclass."""
        return self.get_json(
            self.PROFILE_URL,
            params={'access_token': access_token},
            data=self.auth_complete_params(self.validate_state()),
            headers=self.auth_headers(),
            method=self.ACCESS_TOKEN_METHOD
        )

    def get_user_details(self, response):
        """Must return user details in a know internal struct:
            {'username': <username if any>,
             'email': <user email if any>,
             'fullname': <user full name if any>,
             'first_name': <user first name if any>,
             'last_name': <user last name if any>}
        """
        profile = {
            'username': response['NickName'] or '',
            'email': response['Email'][0]['Value'] or '',
            'fullname': response['FullName'] or '',
            'first_name': response['FirstName'] or '',
            'last_name': response['LastName'] or ''
        }
        return profile

    def get_user_id(self, details, response):
        """Return a unique ID for the current user, by default from server
        response. Since LoginRadius handles multiple providers, we need to
        distinguish them to prevent conflicts."""
        return '{0}-{1}'.format(response.get('Provider'),
                                response.get(self.ID_KEY))

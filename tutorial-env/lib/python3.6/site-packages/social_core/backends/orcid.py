"""
ORCID OAuth2 Application backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/orcid.html
"""
from .oauth import BaseOAuth2


class ORCIDOAuth2(BaseOAuth2):
    """ORCID OAuth2 authentication backend"""
    name = 'orcid'
    ID_KEY = 'orcid'
    AUTHORIZATION_URL = 'https://orcid.org/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://orcid.org/oauth/token'
    USER_DATA_URL = 'https://pub.orcid.org/v2.0/{}'
    DEFAULT_SCOPE = ['/authenticate']
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('orcid', 'id'),
        ('expires_in', 'expires'),
        ('refresh_token', 'refresh_token')
    ]

    def auth_params(self, state=None):
        params = super(ORCIDOAuth2, self).auth_params(state)
        return params

    def get_user_details(self, response):
        """Return user details from ORCID account"""
        fullname= response.get('name', '')
        first_name = last_name = email = ''
        person = response.get('person')
        if person:
            name = person.get('name')
            if name:
                first_name = name.get('given-names', {}).get('value', '')
                last_name = name.get('family-name', {}).get('value', '')

            emails = person.get('emails')
            if emails:
                emails_list = emails.get('email')
                if emails_list and len(emails_list) > 0:
                    email = emails_list[0].get('email', '')

                    if len(emails_list) > 1:
                        for email_dict in emails_list:
                            if email_dict.get('primary','') == True:
                                email = email_dict.get('email', '')
                                break
                    else:
                        mail = emails_list[0].get('email', '')

        return {'username': response.get('orcid'),
                'email': email,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        params = self.setting('PROFILE_EXTRA_PARAMS', {})
        params['access_token'] = access_token
        try:
            return self.get_json(self.USER_DATA_URL.format(
                            kwargs['response']['orcid']),
                            headers={'Content-Type': 'application/json'},
                            params=params)
        except ValueError as e:
            return None


class ORCIDOAuth2Sandbox(ORCIDOAuth2):
    """ORCID OAuth2 Sandbox authentication backend"""
    name = 'orcid-sandbox'
    AUTHORIZATION_URL = 'https://sandbox.orcid.org/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://sandbox.orcid.org/oauth/token'
    USER_DATA_URL = 'https://pub.sandbox.orcid.org/v2.0/{}'


class ORCIDMemberOAuth2(ORCIDOAuth2):
    """ORCID OAuth2 authentication backend that uses ORCID Member API"""
    USER_DATA_URL = 'https://api.orcid.org/v2.0/{}'
    DEFAULT_SCOPE = ['/authenticate', '/read-limited']


class ORCIDMemberOAuth2Sandbox(ORCIDOAuth2Sandbox):
    """ORCID OAuth2 Sandbox authentication backend that uses ORCID Member Sandbox API"""
    USER_DATA_URL = 'https://api.sandbox.orcid.org/v2.0/{}'
    DEFAULT_SCOPE = ['/authenticate', '/read-limited']

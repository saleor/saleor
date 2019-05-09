"""
NationBuilder OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/nationbuilder.html
"""
from .oauth import BaseOAuth2


class NationBuilderOAuth2(BaseOAuth2):
    """NationBuilder OAuth2 authentication backend"""
    name = 'nationbuilder'
    AUTHORIZATION_URL = 'https://{slug}.nationbuilder.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://{slug}.nationbuilder.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    SCOPE_SEPARATOR = ','
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires')
    ]

    def authorization_url(self):
        return self.AUTHORIZATION_URL.format(slug=self.slug)

    def access_token_url(self):
        return self.ACCESS_TOKEN_URL.format(slug=self.slug)

    @property
    def slug(self):
        return self.setting('SLUG')

    def get_user_details(self, response):
        """Return user details from Github account"""
        email = response.get('email') or ''
        username = email.split('@')[0] if email else ''
        return {'username': username,
                'email': email,
                'fullname': response.get('full_name') or '',
                'first_name': response.get('first_name') or '',
                'last_name': response.get('last_name') or ''}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = 'https://{slug}.nationbuilder.com/api/v1/people/me'.format(
            slug=self.slug
        )
        return self.get_json(url, params={
            'access_token': access_token
        })['person']

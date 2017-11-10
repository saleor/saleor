from __future__ import unicode_literals


class AuthenticationBackends:
    GOOGLE = 'google-oauth2'
    FACEBOOK = 'facebook'

    BACKENDS = (
        (FACEBOOK, 'Facebook-Oauth2'),
        (GOOGLE, 'Google-Oauth2'))

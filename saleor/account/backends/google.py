from social_core.backends.google import GoogleOAuth2

from ...site import AuthenticationBackends
from . import BaseBackend


class CustomGoogleOAuth2(BaseBackend, GoogleOAuth2):
    DB_NAME = AuthenticationBackends.GOOGLE

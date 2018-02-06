from social_core.backends.google import GoogleOAuth2

from . import BaseBackend
from saleor.site import AuthenticationBackends


class CustomGoogleOAuth2(BaseBackend, GoogleOAuth2):
    DB_NAME = AuthenticationBackends.GOOGLE

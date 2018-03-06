from social_core.backends.facebook import FacebookOAuth2

from . import BaseBackend
from ...site import AuthenticationBackends


class CustomFacebookOAuth2(BaseBackend, FacebookOAuth2):
    DB_NAME = AuthenticationBackends.FACEBOOK

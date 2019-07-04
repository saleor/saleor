from social_core.backends.facebook import FacebookOAuth2

from ...site import AuthenticationBackends
from . import BaseBackend


class CustomFacebookOAuth2(BaseBackend, FacebookOAuth2):
    DB_NAME = AuthenticationBackends.FACEBOOK

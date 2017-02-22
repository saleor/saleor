from social_core.backends.google import GoogleOAuth2

from . import BaseBackend
from ...site.models import GOOGLE


class CustomGoogleOAuth2(BaseBackend, GoogleOAuth2):
    DB_NAME = GOOGLE

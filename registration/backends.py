from django.contrib.auth import get_user_model
from registration.models import ExternalUserData

User = get_user_model()


class Backend(object):

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class EmailPasswordBackend(Backend):
    """Authentication backend that expects an email in username parameter"""

    def authenticate(self, username=None, password=None, **_kwargs):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user


class ExternalLoginBackend(Backend):
    """Authenticate with external service id"""

    def authenticate(self, external_username=None, external_service=None,
                     **_kwargs):
        try:
            return ExternalUserData.objects.select_related('user').get(
                provider=external_service, username=external_username
            ).user
        except ExternalUserData.DoesNotExist:
            return None


class TrivialBackend(Backend):
    """Authenticate with user instance"""

    def authenticate(self, user=None, **_kwargs):
        if isinstance(user, User):
            return user

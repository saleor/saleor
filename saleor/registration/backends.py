from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .models import ExternalUserData

User = get_user_model()


class Backend(ModelBackend):

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class EmailPasswordBackend(Backend):
    """Authentication backend that expects an email in username parameter."""

    def authenticate(self, username=None, password=None, **_kwargs):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user


class ExternalLoginBackend(Backend):
    """Authenticate with external service id."""

    def authenticate(self, service=None, username=None, **_kwargs):
        try:
            user_data = (ExternalUserData.objects
                                         .select_related('user')
                                         .get(service=service,
                                              username=username))
            return user_data.user
        except ExternalUserData.DoesNotExist:
            return None


class TrivialBackend(Backend):
    """Authenticate with user instance."""

    def authenticate(self, user=None, **_kwargs):
        if isinstance(user, User):
            return user

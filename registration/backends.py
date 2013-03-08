from django.contrib.auth import get_user_model
from registration.models import ExternalUserID

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


class FacebookBackend(Backend):
    """Authenticate with facebook id"""

    def authenticate(self, facebook_uid=None, **_kwargs):
        try:
            return ExternalUserID.objects.select_related('user').get(
                provider='facebook', username=facebook_uid
            ).user
        except ExternalUserID.DoesNotExist:
            return


class TrivialBackend(Backend):
    """Authenticate with user instance"""

    def authenticate(self, user=None, **_kwargs):
        if isinstance(user, User):
            return user

from ..account.models import User
from .jwt import get_token_from_request, get_user_from_access_token


class JSONWebTokenBackend:
    def authenticate(self, request=None, **kwargs):
        if request is None:
            return None

        token = get_token_from_request(request)
        if not token:
            return None
        return get_user_from_access_token(token)

    def get_user(self, user_id):
        try:
            return User.objects.get(email=user_id, is_active=True)
        except User.DoesNotExist:
            return None

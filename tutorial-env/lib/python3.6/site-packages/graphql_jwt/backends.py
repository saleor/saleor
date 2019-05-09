from .shortcuts import get_user_by_token
from .utils import get_credentials, get_user_by_natural_key


class JSONWebTokenBackend(object):

    def authenticate(self, request=None, skip_jwt_backend=False, **kwargs):
        if request is None or skip_jwt_backend:
            return None

        token = get_credentials(request, **kwargs)

        if token is not None:
            return get_user_by_token(token, request)

        return None

    def get_user(self, user_id):
        return get_user_by_natural_key(user_id)

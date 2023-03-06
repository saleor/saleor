import jwt
from django.contrib.auth.backends import ModelBackend

from ..account.models import User
from ..graphql.account.dataloaders import UserByEmailLoader
from ..graphql.plugins.dataloaders import AnonymousPluginManagerLoader
from .auth import get_token_from_request
from .jwt import (
    JWT_ACCESS_TYPE,
    JWT_THIRDPARTY_ACCESS_TYPE,
    PERMISSIONS_FIELD,
    is_saleor_token,
    jwt_decode,
)
from .permissions import get_permissions_from_codenames, get_permissions_from_names


class JSONWebTokenBackend(ModelBackend):
    def authenticate(self, request=None, **kwargs):
        return load_user_from_request(request)

    def get_user(self, user_id):
        try:
            return User.objects.get(email=user_id, is_active=True)
        except User.DoesNotExist:
            return None

    def _get_user_permissions(self, user_obj):
        # overwrites base method to force using our permission field
        return user_obj.effective_permissions

    def _get_group_permissions(self, user_obj):
        # overwrites base method to force using our permission field
        return user_obj.effective_permissions

    def _get_permissions(self, user_obj, obj, from_name):
        """Return the permissions of `user_obj` from `from_name`.

        `from_name` can be either "group" or "user" to return permissions from
        `_get_group_permissions` or `_get_user_permissions` respectively.
        """
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        perm_cache_name = "_effective_permissions_cache"
        if not getattr(user_obj, perm_cache_name, None):
            perms = getattr(self, f"_get_{from_name}_permissions")(user_obj)
            perms = perms.values_list("content_type__app_label", "codename").order_by()
            setattr(user_obj, perm_cache_name, {f"{ct}.{name}" for ct, name in perms})
        return getattr(user_obj, perm_cache_name)


class PluginBackend(JSONWebTokenBackend):
    def authenticate(self, request=None, **kwargs):
        if request is None:
            return None
        manager = AnonymousPluginManagerLoader(request).load("Anonymous").get()
        return manager.authenticate_user(request)


def load_user_from_request(request):
    if request is None:
        return None
    jwt_token = get_token_from_request(request)
    if not jwt_token or not is_saleor_token(jwt_token):
        return None
    payload = jwt_decode(jwt_token)

    jwt_type = payload.get("type")
    if jwt_type not in [JWT_ACCESS_TYPE, JWT_THIRDPARTY_ACCESS_TYPE]:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    permissions = payload.get(PERMISSIONS_FIELD, None)

    user = UserByEmailLoader(request).load(payload["email"]).get()
    user_jwt_token = payload.get("token")
    if not user_jwt_token:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    elif not user:
        raise jwt.InvalidTokenError(
            "Invalid token. User does not exist or is inactive."
        )
    if user.jwt_token_key != user_jwt_token:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )

    if permissions is not None:
        token_permissions = get_permissions_from_names(permissions)
        token_codenames = [perm.codename for perm in token_permissions]
        user.effective_permissions = get_permissions_from_codenames(token_codenames)
        user.is_staff = True if user.effective_permissions else False

    if payload.get("is_staff"):
        user.is_staff = True
    return user

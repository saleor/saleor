from django.contrib.auth.backends import ModelBackend

from ..account.models import User
from ..graphql.account.dataloaders import load_user_from_token
from ..graphql.plugins.dataloaders import AnonymousPluginManagerLoader
from .auth import get_token_from_request


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
            perms = getattr(self, "_get_%s_permissions" % from_name)(user_obj)
            perms = perms.values_list("content_type__app_label", "codename").order_by()
            setattr(
                user_obj, perm_cache_name, {"%s.%s" % (ct, name) for ct, name in perms}
            )
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
    return load_user_from_token(request, jwt_token)

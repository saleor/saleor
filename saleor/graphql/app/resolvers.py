import graphene

from ...app import models
from ...core.jwt import create_access_token_for_app
from ...core.permissions import AppPermission
from ...core.tracing import traced_resolver
from ..decorators import permission_required
from .enums import AppTypeEnum


@traced_resolver
def resolve_apps_installations(info, **_kwargs):
    return models.AppInstallation.objects.all()


@traced_resolver
def resolve_apps(info, **_kwargs):
    return models.App.objects.all()


@traced_resolver
def resolve_access_token(info, root, **_kwargs):
    if root.type != AppTypeEnum.THIRDPARTY.value:
        return None

    user = info.context.user
    if user.is_anonymous:
        return None
    return create_access_token_for_app(root, user)


@permission_required(AppPermission.MANAGE_APPS)
def _resolve_app(info, id):
    from .types import App

    return graphene.Node.get_node_from_global_id(info, id, App)

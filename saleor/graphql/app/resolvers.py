from ...app import models
from ...core.jwt import create_access_token_for_app
from ...core.permissions import AppPermission
from ...core.tracing import traced_resolver
from ..core.utils import from_global_id_or_error
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


@traced_resolver
@permission_required(AppPermission.MANAGE_APPS)
def resolve_app(_info, id):
    if not id:
        return None
    _, id = from_global_id_or_error(id, "App")
    return models.App.objects.filter(id=id).first()

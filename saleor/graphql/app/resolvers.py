from ...app import models
from ...core.jwt import create_access_token_for_app
from ...core.permissions import AppPermission
from ..core.utils import from_global_id_or_error
from ..decorators import permission_required
from .enums import AppTypeEnum


def resolve_apps_installations(info, **_kwargs):
    return models.AppInstallation.objects.all()


def resolve_apps(info, **_kwargs):
    return models.App.objects.all()


def resolve_access_token(info, root, **_kwargs):
    if root.type != AppTypeEnum.THIRDPARTY.value:
        return None

    user = info.context.user
    if user.is_anonymous:
        return None
    return create_access_token_for_app(root, user)


@permission_required(AppPermission.MANAGE_APPS)
def resolve_app(_info, id):
    if not id:
        return None
    _, id = from_global_id_or_error(id, "App")
    return models.App.objects.filter(id=id).first()

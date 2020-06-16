from ...app import models
from ...core.jwt import create_access_token_for_app
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

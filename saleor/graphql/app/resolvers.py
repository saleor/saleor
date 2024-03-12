from urllib.parse import urljoin, urlparse

from django.db.models import Exists, OuterRef

from ...app import models
from ...app.types import AppExtensionTarget
from ...core.jwt import (
    create_access_token_for_app,
    create_access_token_for_app_extension,
)
from ..core.context import get_database_connection_name
from ..core.utils import from_global_id_or_error
from .enums import AppTypeEnum


def resolve_apps_installations(info):
    return models.AppInstallation.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_apps(info):
    return (
        models.App.objects.using(get_database_connection_name(info.context))
        .filter(is_installed=True, removed_at__isnull=True)
        .all()
    )


def resolve_access_token_for_app(info, root):
    if root.type != AppTypeEnum.THIRDPARTY.value:
        return None

    user = info.context.user
    if not user or not user.is_staff:
        return None
    database_connection_name = get_database_connection_name(info.context)
    return create_access_token_for_app(
        root, user, database_connection_name=database_connection_name
    )


def resolve_access_token_for_app_extension(info, root, app):
    user = info.context.user
    if not user:
        return None
    database_connection_name = get_database_connection_name(info.context)
    extension_permissions = root.permissions.using(database_connection_name).all()
    user_permissions = user.effective_permissions.using(database_connection_name)
    if set(extension_permissions).issubset(user_permissions):
        return create_access_token_for_app_extension(
            app_extension=root,
            permissions=extension_permissions,
            user=user,
            app=app,
            database_connection_name=database_connection_name,
        )
    return None


def resolve_app(info, id):
    if not id:
        return None
    _, id = from_global_id_or_error(id, "App")
    return (
        models.App.objects.using(get_database_connection_name(info.context))
        .filter(id=id, is_installed=True, removed_at__isnull=True)
        .first()
    )


def resolve_app_extensions(info):
    connection = get_database_connection_name(info.context)
    apps = (
        models.App.objects.using(connection)
        .filter(is_active=True, removed_at__isnull=True)
        .values("pk")
    )
    return models.AppExtension.objects.using(connection).filter(
        Exists(apps.filter(id=OuterRef("app_id")))
    )


def resolve_app_extension_url(root):
    """Return an extension url.

    Apply url stitching when these 3 conditions are met:
        - url starts with /
        - target == "POPUP"
        - appUrl is defined
    """
    target = root.get("target", AppExtensionTarget.POPUP)
    app_url = root["app_url"]
    url = root["url"]
    if url.startswith("/") and app_url and target == AppExtensionTarget.POPUP:
        parsed_url = urlparse(app_url)
        new_path = urljoin(parsed_url.path, url[1:])
        return parsed_url._replace(path=new_path).geturl()
    return url

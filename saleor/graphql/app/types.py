from datetime import timedelta

import graphene
from graphene_federation import key

from ...app import models
from ...core.jwt import (
    JWT_ACCESS_TYPE,
    PERMISSION_LIMITS_FIELD,
    jwt_encode,
    jwt_user_payload,
)
from ...core.permissions import PERMISSIONS_ENUMS, AppPermission, get_permissions
from ..core.connection import CountableDjangoObjectType
from ..core.types import Permission
from ..core.types.common import Job
from ..meta.deprecated.resolvers import resolve_meta, resolve_private_meta
from ..meta.types import ObjectWithMetadata
from ..utils import format_permissions_for_display
from ..webhook.types import Webhook
from .enums import AppTypeEnum


class Manifest(graphene.ObjectType):
    identifier = graphene.String(required=True)
    version = graphene.String(required=True)
    name = graphene.String(required=True)
    about = graphene.String()
    permissions = graphene.List(Permission)
    app_url = graphene.String()
    configuration_url = graphene.String()
    token_target_url = graphene.String()
    data_privacy = graphene.String()
    data_privacy_url = graphene.String()
    homepage_url = graphene.String()
    support_url = graphene.String()

    class Meta:
        description = "The manifest definition."


class AppToken(CountableDjangoObjectType):
    name = graphene.String(description="Name of the authenticated token.")
    auth_token = graphene.String(description="Last 4 characters of the token.")

    class Meta:
        description = "Represents token data."
        model = models.AppToken
        interfaces = [graphene.relay.Node]
        permissions = (AppPermission.MANAGE_APPS,)
        only_fields = ["name", "auth_token"]

    @staticmethod
    def resolve_auth_token(root: models.AppToken, _info, **_kwargs):
        return root.auth_token[-4:]


@key(fields="id")
class App(CountableDjangoObjectType):
    permissions = graphene.List(
        Permission, description="List of the app's permissions."
    )
    created = graphene.DateTime(
        description="The date and time when the app was created."
    )
    is_active = graphene.Boolean(
        description="Determine if app will be set active or not."
    )
    name = graphene.String(description="Name of the app.")
    type = AppTypeEnum(description="Type of the app.")
    tokens = graphene.List(AppToken, description="Last 4 characters of the tokens.")
    webhooks = graphene.List(
        Webhook, description="List of webhooks assigned to this app."
    )

    about_app = graphene.String(description="Description of this app.")

    data_privacy = graphene.String(
        description="Description of the data privacy defined for this app."
    )
    data_privacy_url = graphene.String(
        description="Url to details about the privacy policy on the app owner page."
    )
    homepage_url = graphene.String(description="Homepage of the app.")
    support_url = graphene.String(description="Support page for the app.")
    configuration_url = graphene.String(
        description="Url to iframe with the configuration for the app."
    )
    app_url = graphene.String(description="Url to iframe with the app.")
    version = graphene.String(description="Version number of the app.")
    access_token = graphene.String(
        description="JWT token used to authenticate by thridparty app."
    )

    class Meta:
        description = "Represents app data."
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        only_fields = [
            "name",
            "permissions",
            "created",
            "is_active",
            "tokens",
            "id",
            "tokens",
        ]

    @staticmethod
    def resolve_permissions(root: models.App, _info, **_kwargs):
        permissions = root.permissions.prefetch_related("content_type").order_by(
            "codename"
        )
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_tokens(root: models.App, _info, **_kwargs):
        return root.tokens.all()

    @staticmethod
    def resolve_meta(root: models.App, info):
        return resolve_meta(root, info)

    @staticmethod
    def resolve_private_meta(root: models.App, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)

    @staticmethod
    def resolve_webhooks(root: models.App, _info):
        return root.webhooks.all()

    @staticmethod
    def resolve_access_token(root: models.App, info):
        if root.type != AppTypeEnum.THIRDPARTY.value:
            return None

        user = info.context.user
        if user.is_anonymous:
            return None

        permissions_dict = {
            enum.codename: enum.name
            for permission_enum in PERMISSIONS_ENUMS
            for enum in permission_enum
        }
        app_permissions = root.permissions.all()
        app_permission_enums = {
            permissions_dict[perm.codename] for perm in app_permissions
        }

        if user.is_superuser:
            user_permissions = get_permissions()
        else:
            user_permissions = user.user_permissions.all()

        user_permission_enums = {
            permissions_dict[perm.codename] for perm in user_permissions
        }
        app_id = graphene.Node.to_global_id("App", root.id)
        additional_payload = {
            "app": app_id,
            PERMISSION_LIMITS_FIELD: list(app_permission_enums & user_permission_enums),
        }
        payload = jwt_user_payload(
            user,
            JWT_ACCESS_TYPE,
            exp_delta=timedelta(hours=1),
            additional_payload=additional_payload,
        )
        return jwt_encode(payload)


class AppInstallation(CountableDjangoObjectType):
    class Meta:
        model = models.AppInstallation
        description = "Represents ongoing installation of app."
        interfaces = [graphene.relay.Node, Job]
        permissions = (AppPermission.MANAGE_APPS,)
        only_fields = [
            "status",
            "created_at",
            "updated_at",
            "app_name",
            "manifest_url",
            "message",
        ]

import graphene
from graphene_federation import key

from ...app import models
from ...core.permissions import AppPermission
from ..core.connection import CountableDjangoObjectType
from ..core.types import Permission
from ..core.types.common import Job
from ..meta.types import ObjectWithMetadata
from ..utils import format_permissions_for_display
from ..webhook.types import Webhook
from .enums import AppTypeEnum
from .resolvers import resolve_access_token


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
        return root.tokens.all()  # type: ignore

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)

    @staticmethod
    def resolve_webhooks(root: models.App, _info):
        return root.webhooks.all()

    @staticmethod
    def resolve_access_token(root: models.App, info):
        return resolve_access_token(info, root)


class AppInstallation(CountableDjangoObjectType):
    class Meta:
        model = models.AppInstallation
        description = "Represents ongoing installation of app."
        interfaces = [graphene.relay.Node, Job]
        permissions = (AppPermission.MANAGE_APPS,)
        only_fields = [
            "app_name",
            "manifest_url",
        ]

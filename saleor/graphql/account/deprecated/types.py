import graphene
from graphene_federation import key

from ....app.models import App, AppToken
from ....core.permissions import AppPermission
from ...core.connection import CountableDjangoObjectType
from ...core.types import FilterInputObjectType, Permission
from ...meta.deprecated.resolvers import resolve_meta, resolve_private_meta
from ...meta.types import ObjectWithMetadata
from ...utils import format_permissions_for_display
from .filters import ServiceAccountFilter


class ServiceAccountFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ServiceAccountFilter


class ServiceAccountToken(CountableDjangoObjectType):
    name = graphene.String(description="Name of the authenticated token.")
    auth_token = graphene.String(description="Last 4 characters of the token.")

    class Meta:
        description = "Represents token data."
        model = AppToken
        interfaces = [graphene.relay.Node]
        permissions = (AppPermission.MANAGE_APPS,)
        only_fields = ["name", "auth_token"]

    @staticmethod
    def resolve_auth_token(root: AppToken, _info, **_kwargs):
        return root.auth_token[-4:]


@key(fields="id")
class ServiceAccount(CountableDjangoObjectType):
    permissions = graphene.List(
        Permission, description="List of the service's permissions."
    )
    created = graphene.DateTime(
        description="The date and time when the service account was created."
    )
    is_active = graphene.Boolean(
        description="Determine if service account will be set active or not."
    )
    name = graphene.String(description="Name of the service account.")

    tokens = graphene.List(
        ServiceAccountToken, description="Last 4 characters of the tokens."
    )

    class Meta:
        description = "Represents service account data."
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = App
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
    def resolve_permissions(root: App, _info, **_kwargs):
        permissions = root.permissions.prefetch_related("content_type").order_by(
            "codename"
        )
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_tokens(root: App, _info, **_kwargs):
        return root.tokens.all()

    @staticmethod
    def resolve_meta(root: App, info):
        return resolve_meta(root, info)

    @staticmethod
    def resolve_private_meta(root: App, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)

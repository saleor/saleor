import graphene
from graphene.types.resolver import get_default_resolver
from graphene_django import DjangoObjectType

from ...channel import models
from ...core.permissions import ChannelPermissions
from ..core.connection import CountableDjangoObjectType
from ..decorators import permission_required
from ..meta.types import ObjectWithMetadata
from ..translations.resolvers import resolve_translation
from . import ChannelContext
from .dataloaders import ChannelWithHasOrdersByIdLoader


class ChannelContextType(DjangoObjectType):
    """A Graphene type that supports resolvers' root as ChannelContext objects."""

    class Meta:
        abstract = True

    @staticmethod
    def resolver_with_context(
        attname, default_value, root: ChannelContext, info, **args
    ):
        resolver = get_default_resolver()
        return resolver(attname, default_value, root.node, info, **args)

    @staticmethod
    def resolve_id(root: ChannelContext, _info):
        return root.node.pk

    @classmethod
    def is_type_of(cls, root: ChannelContext, info):
        return super().is_type_of(root.node, info)

    @staticmethod
    def resolve_translation(root: ChannelContext, info, language_code):
        # Resolver for TranslationField; needs to be manually specified.
        return resolve_translation(root.node, info, language_code)


class ChannelContextTypeWithMetadata(ChannelContextType):
    """A Graphene type for that uses ChannelContext as root in resolvers.

    Same as ChannelContextType, but for types that implement ObjectWithMetadata
    interface.
    """

    class Meta:
        abstract = True

    @staticmethod
    def resolve_metadata(root: ChannelContext, info):
        # Used in metadata API to resolve metadata fields from an instance.
        return ObjectWithMetadata.resolve_metadata(root.node, info)

    @staticmethod
    def resolve_private_metadata(root: ChannelContext, info):
        # Used in metadata API to resolve private metadata fields from an instance.
        return ObjectWithMetadata.resolve_private_metadata(root.node, info)


class Channel(CountableDjangoObjectType):
    has_orders = graphene.Boolean(
        required=True, description="Whether a channel has associated orders."
    )

    class Meta:
        description = "Represents channel."
        model = models.Channel
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "name", "slug", "currency_code", "is_active"]

    @staticmethod
    @permission_required(ChannelPermissions.MANAGE_CHANNELS)
    def resolve_has_orders(root: models.Channel, info):
        return (
            ChannelWithHasOrdersByIdLoader(info.context)
            .load(root.id)
            .then(lambda channel: channel.has_orders)
        )

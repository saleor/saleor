from typing import Type, Union, cast

import graphene
from django.db.models import Model
from graphene.types.resolver import get_default_resolver

from ...channel import models
from ...core.permissions import ChannelPermissions
from ..core.descriptions import ADDED_IN_31
from ..core.fields import PermissionsField
from ..core.types import CountryDisplay, ModelObjectType
from ..meta.types import ObjectWithMetadata
from ..translations.resolvers import resolve_translation
from . import ChannelContext
from .dataloaders import ChannelWithHasOrdersByIdLoader


class ChannelContextTypeForObjectType(graphene.ObjectType):
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

    @staticmethod
    def resolve_translation(root: ChannelContext, info, *, language_code):
        # Resolver for TranslationField; needs to be manually specified.
        return resolve_translation(root.node, info, language_code=language_code)


class ChannelContextType(ChannelContextTypeForObjectType, ModelObjectType):
    """A Graphene type that supports resolvers' root as ChannelContext objects."""

    class Meta:
        abstract = True

    @classmethod
    def is_type_of(cls, root: Union[ChannelContext, Model], _info):
        # Unwrap node from ChannelContext if it didn't happen already
        if isinstance(root, ChannelContext):
            root = cast(Model, root.node)

        if isinstance(root, cls):
            return True

        if cls._meta.model._meta.proxy:
            model = root._meta.model
        else:
            model = cast(Type[Model], root._meta.model._meta.concrete_model)

        return model == cls._meta.model


class ChannelContextTypeWithMetadataForObjectType(ChannelContextTypeForObjectType):
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
    def resolve_metafield(root: ChannelContext, info, *, key: str):
        # Used in metadata API to resolve metadata fields from an instance.
        return ObjectWithMetadata.resolve_metafield(root.node, info, key=key)

    @staticmethod
    def resolve_metafields(root: ChannelContext, info, *, keys=None):
        # Used in metadata API to resolve metadata fields from an instance.
        return ObjectWithMetadata.resolve_metafields(root.node, info, keys=keys)

    @staticmethod
    def resolve_private_metadata(root: ChannelContext, info):
        # Used in metadata API to resolve private metadata fields from an instance.
        return ObjectWithMetadata.resolve_private_metadata(root.node, info)

    @staticmethod
    def resolve_private_metafield(root: ChannelContext, info, *, key: str):
        # Used in metadata API to resolve private metadata fields from an instance.
        return ObjectWithMetadata.resolve_private_metafield(root.node, info, key=key)

    @staticmethod
    def resolve_private_metafields(root: ChannelContext, info, *, keys=None):
        # Used in metadata API to resolve private metadata fields from an instance.
        return ObjectWithMetadata.resolve_private_metafields(root.node, info, keys=keys)


class ChannelContextTypeWithMetadata(
    ChannelContextTypeWithMetadataForObjectType, ChannelContextType
):
    """A Graphene type for that uses ChannelContext as root in resolvers.

    Same as ChannelContextType, but for types that implement ObjectWithMetadata
    interface.
    """

    class Meta:
        abstract = True


class Channel(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    is_active = graphene.Boolean(required=True)
    slug = graphene.String(required=True)
    currency_code = graphene.String(required=True)
    slug = graphene.String(required=True)
    has_orders = PermissionsField(
        graphene.Boolean,
        description="Whether a channel has associated orders.",
        permissions=[
            ChannelPermissions.MANAGE_CHANNELS,
        ],
        required=True,
    )
    default_country = graphene.Field(
        CountryDisplay,
        description=(
            "Default country for the channel. Default country can be "
            "used in checkout to determine the stock quantities or calculate taxes "
            "when the country was not explicitly provided." + ADDED_IN_31
        ),
        required=True,
    )

    class Meta:
        description = "Represents channel."
        model = models.Channel
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_has_orders(root: models.Channel, info):
        return (
            ChannelWithHasOrdersByIdLoader(info.context)
            .load(root.id)
            .then(lambda channel: channel.has_orders)
        )

    @staticmethod
    def resolve_default_country(root: models.Channel, _info):
        return CountryDisplay(
            code=root.default_country.code, country=root.default_country.name
        )

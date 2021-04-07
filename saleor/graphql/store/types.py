import graphene
from graphene import relay

from ...core.permissions import StorePermissions
from ...core.weight import convert_weight_to_default_weight_unit
from ...store import models
from ..channel import ChannelQsContext
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.types import (
    ChannelContext,
    ChannelContextType,
    ChannelContextTypeWithMetadata,
)
from ..core.connection import CountableDjangoObjectType
from ..decorators import permission_required
from ..meta.types import ObjectWithMetadata
from .resolvers import resolve_store_type_name, resolve_store_type_description


class StoreType(ChannelContextTypeWithMetadata, CountableDjangoObjectType):
    name = graphene.String(description="Name of strore type.")
    description = graphene.String(description="Description of a store type.")

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Represents a shipping zone in the shop. Zones are the concept used only "
            "for grouping shipping methods in the dashboard, and are never exposed to "
            "the customers directly."
        )
        model = models.Store
        interfaces = [relay.Node, ObjectWithMetadata]
        only_fields = ["default", "id", "name", "description"]

    @staticmethod
    def resolve_store_type_name(root: ChannelContext[models.Store], *_args):
        return resolve_store_type_name(root.channel_slug)

    @staticmethod
    def resolve_store_type_description(root: ChannelContext[models.ShippingZone], *_args):
        return resolve_store_type_description(root.channel__slug)

    
from graphene import relay

from ....product import models
from ...channel.dataloaders import (
    ChannelByProductChannelListingIDLoader,
    ChannelByProductVariantChannelListingIDLoader,
)
from ...core.connection import CountableDjangoObjectType


class ProductChannelListing(CountableDjangoObjectType):
    class Meta:
        description = "Represents product channel listing."
        model = models.ProductChannelListing
        interfaces = [relay.Node]
        only_fields = ["id", "channel", "is_published", "publication_date"]

    @staticmethod
    def resolve_channel(root: models.ProductChannelListing, info, **_kwargs):
        return ChannelByProductChannelListingIDLoader(info.context).load(root.id)


class ProductVariantChannelListing(CountableDjangoObjectType):
    class Meta:
        description = "Represents product varaint channel listing."
        model = models.ProductVariantChannelListing
        interfaces = [relay.Node]
        only_fields = ["id", "channel", "price"]

    @staticmethod
    def resolve_channel(root: models.ProductVariantChannelListing, info, **_kwargs):
        return ChannelByProductVariantChannelListingIDLoader(info.context).load(root.id)

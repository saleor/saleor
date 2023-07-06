import graphene
from graphene import relay

from ....discount import models
from ....permission.enums import DiscountPermissions
from ...channel import ChannelQsContext
from ...channel.dataloaders import ChannelByIdLoader
from ...channel.types import (
    Channel,
    ChannelContext,
    ChannelContextType,
    ChannelContextTypeWithMetadata,
)
from ...core import ResolveInfo
from ...core.connection import CountableConnection, create_connection_slice
from ...core.context import get_database_connection_name
from ...core.descriptions import ADDED_IN_31
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.fields import ConnectionField, PermissionsField
from ...core.types import ModelObjectType, NonNullList
from ...meta.types import ObjectWithMetadata
from ...product.types import (
    CategoryCountableConnection,
    CollectionCountableConnection,
    ProductCountableConnection,
    ProductVariantCountableConnection,
)
from ...translations.fields import TranslationField
from ...translations.types import SaleTranslation
from ..dataloaders import (
    SaleChannelListingBySaleIdAndChanneSlugLoader,
    SaleChannelListingBySaleIdLoader,
)
from ..enums import SaleType


class SaleChannelListing(ModelObjectType[models.SaleChannelListing]):
    id = graphene.GlobalID(required=True, description="The ID of the channel listing.")
    channel = graphene.Field(
        Channel,
        required=True,
        description="The channel in which the sale is available.",
    )
    discount_value = graphene.Float(
        required=True,
        description="The value of the discount applied to the sale in the channel.",
    )
    currency = graphene.String(
        required=True,
        description="The currency in which the discount value is specified.",
    )

    class Meta:
        description = "Represents sale channel listing."
        model = models.SaleChannelListing
        interfaces = [relay.Node]

    @staticmethod
    def resolve_channel(root: models.SaleChannelListing, info: ResolveInfo):
        return ChannelByIdLoader(info.context).load(root.channel_id)


class Sale(ChannelContextTypeWithMetadata, ModelObjectType[models.Sale]):
    id = graphene.GlobalID(required=True, description="The ID of the sale.")
    name = graphene.String(required=True, description="The name of the sale.")
    type = SaleType(required=True, description="Type of the sale, fixed or percentage.")
    start_date = graphene.DateTime(
        required=True, description="The start date and time of the sale."
    )
    end_date = graphene.DateTime(description="The end date and time of the sale.")
    created = graphene.DateTime(
        required=True, description="The date and time when the sale was created."
    )
    updated_at = graphene.DateTime(
        required=True, description="The date and time when the sale was updated."
    )
    categories = ConnectionField(
        CategoryCountableConnection,
        description="List of categories this sale applies to.",
    )
    collections = ConnectionField(
        CollectionCountableConnection,
        description="List of collections this sale applies to.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
    )
    products = ConnectionField(
        ProductCountableConnection,
        description="List of products this sale applies to.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
    )
    variants = ConnectionField(
        ProductVariantCountableConnection,
        description="List of product variants this sale applies to." + ADDED_IN_31,
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
    )
    translation = TranslationField(
        SaleTranslation,
        type_name="sale",
        resolver=ChannelContextType.resolve_translation,
    )
    channel_listings = PermissionsField(
        NonNullList(SaleChannelListing),
        description="List of channels available for the sale.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
    )
    discount_value = graphene.Float(description="Sale value.")
    currency = graphene.String(description="Currency code for sale.")

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Sales allow creating discounts for categories, collections or products "
            "and are visible to all the customers."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Sale

    @staticmethod
    def resolve_created(root: models.Sale, _info: ResolveInfo):
        return root.created_at

    @staticmethod
    def resolve_categories(
        root: ChannelContext[models.Sale], info: ResolveInfo, **kwargs
    ):
        qs = root.node.categories.all()
        return create_connection_slice(qs, info, kwargs, CategoryCountableConnection)

    @staticmethod
    def resolve_channel_listings(root: ChannelContext[models.Sale], info: ResolveInfo):
        return SaleChannelListingBySaleIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_collections(
        root: ChannelContext[models.Sale], info: ResolveInfo, **kwargs
    ):
        qs = root.node.collections.all()
        qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)
        return create_connection_slice(qs, info, kwargs, CollectionCountableConnection)

    @staticmethod
    def resolve_products(
        root: ChannelContext[models.Sale], info: ResolveInfo, **kwargs
    ):
        qs = root.node.products.all()
        qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)
        return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

    @staticmethod
    def resolve_variants(
        root: ChannelContext[models.Sale], info: ResolveInfo, **kwargs
    ):
        readonly_qs = root.node.variants.using(
            get_database_connection_name(info.context)
        ).all()

        readonly_qs = ChannelQsContext(qs=readonly_qs, channel_slug=root.channel_slug)
        return create_connection_slice(
            readonly_qs, info, kwargs, ProductVariantCountableConnection
        )

    @staticmethod
    def resolve_discount_value(root: ChannelContext[models.Sale], info: ResolveInfo):
        if not root.channel_slug:
            return None

        return (
            SaleChannelListingBySaleIdAndChanneSlugLoader(info.context)
            .load((root.node.id, root.channel_slug))
            .then(
                lambda channel_listing: channel_listing.discount_value
                if channel_listing
                else None
            )
        )

    @staticmethod
    def resolve_currency(root: ChannelContext[models.Sale], info: ResolveInfo):
        if not root.channel_slug:
            return None

        return (
            SaleChannelListingBySaleIdAndChanneSlugLoader(info.context)
            .load((root.node.id, root.channel_slug))
            .then(
                lambda channel_listing: channel_listing.currency
                if channel_listing
                else None
            )
        )


class SaleCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        node = Sale

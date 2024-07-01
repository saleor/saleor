import graphene
from graphene import relay

from ....discount import DiscountValueType, models
from ....permission.enums import DiscountPermissions
from ....product.models import Category, Collection, Product, ProductVariant
from ...channel import ChannelQsContext
from ...channel.dataloaders import ChannelBySlugLoader
from ...channel.types import (
    Channel,
    ChannelContext,
    ChannelContextType,
    ChannelContextTypeWithMetadata,
)
from ...core import ResolveInfo
from ...core.connection import CountableConnection, create_connection_slice
from ...core.context import get_database_connection_name
from ...core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_TYPE
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.fields import ConnectionField, PermissionsField
from ...core.scalars import DateTime
from ...core.types import BaseObjectType, ModelObjectType, NonNullList
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
    PredicateByPromotionIdLoader,
    PromotionRulesByPromotionIdAndChannelSlugLoader,
    PromotionRulesByPromotionIdLoader,
    SaleChannelListingByPromotionIdLoader,
)
from ..enums import SaleType


class SaleChannelListing(BaseObjectType):
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
        description = (
            "Represents sale channel listing."
            + DEPRECATED_IN_3X_TYPE
            + " Use `PromotionRule` type instead."
        )
        interfaces = [relay.Node]
        doc_category = DOC_CATEGORY_DISCOUNTS


class Sale(ChannelContextTypeWithMetadata, ModelObjectType[models.Promotion]):
    id = graphene.GlobalID(required=True, description="The ID of the sale.")
    name = graphene.String(required=True, description="The name of the sale.")
    type = SaleType(required=True, description="Type of the sale, fixed or percentage.")
    start_date = DateTime(
        required=True, description="The start date and time of the sale."
    )
    end_date = DateTime(description="The end date and time of the sale.")
    created = DateTime(
        required=True, description="The date and time when the sale was created."
    )
    updated_at = DateTime(
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
            + DEPRECATED_IN_3X_TYPE
            + " Use `Promotion` type instead."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Promotion
        doc_category = DOC_CATEGORY_DISCOUNTS

    @staticmethod
    def resolve_id(root: ChannelContext[models.Promotion], _info: ResolveInfo):
        return root.node.old_sale_id

    @staticmethod
    def resolve_created(root: ChannelContext[models.Promotion], _info: ResolveInfo):
        return root.node.created_at

    @staticmethod
    def resolve_type(root: ChannelContext[models.Promotion], info: ResolveInfo):
        def _get_type(rules):
            # We ensure, that old sales have at least one rule associated.
            return rules[0].reward_value_type or DiscountValueType.FIXED

        return (
            PromotionRulesByPromotionIdLoader(info.context)
            .load(root.node.id)
            .then(_get_type)
        )

    @staticmethod
    def resolve_categories(
        root: ChannelContext[models.Promotion], info: ResolveInfo, **kwargs
    ):
        def _get_categories(predicates):
            if category_ids := predicates.get("categoryPredicate"):
                qs = Category.objects.using(
                    get_database_connection_name(info.context)
                ).filter(id__in=category_ids)
                return create_connection_slice(
                    qs, info, kwargs, CategoryCountableConnection
                )

        return (
            PredicateByPromotionIdLoader(info.context)
            .load(root.node.id)
            .then(_get_categories)
        )

    @staticmethod
    def resolve_channel_listings(
        root: ChannelContext[models.Promotion], info: ResolveInfo
    ):
        return SaleChannelListingByPromotionIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_collections(
        root: ChannelContext[models.Promotion], info: ResolveInfo, **kwargs
    ):
        def _get_collections(predicates):
            if collection_ids := predicates.get("collectionPredicate"):
                qs = Collection.objects.using(
                    get_database_connection_name(info.context)
                ).filter(id__in=collection_ids)
                qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)
                return create_connection_slice(
                    qs, info, kwargs, CollectionCountableConnection
                )

        return (
            PredicateByPromotionIdLoader(info.context)
            .load(root.node.id)
            .then(_get_collections)
        )

    @staticmethod
    def resolve_products(
        root: ChannelContext[models.Promotion], info: ResolveInfo, **kwargs
    ):
        def _get_products(predicates):
            if product_ids := predicates.get("productPredicate"):
                qs = Product.objects.using(
                    get_database_connection_name(info.context)
                ).filter(id__in=product_ids)
                qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)
                return create_connection_slice(
                    qs, info, kwargs, ProductCountableConnection
                )

        return (
            PredicateByPromotionIdLoader(info.context)
            .load(root.node.id)
            .then(_get_products)
        )

    @staticmethod
    def resolve_variants(
        root: ChannelContext[models.Promotion], info: ResolveInfo, **kwargs
    ):
        def _get_variants(predicates):
            if variant_ids := predicates.get("variantPredicate"):
                qs = ProductVariant.objects.using(
                    get_database_connection_name(info.context)
                ).filter(id__in=variant_ids)
                qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)
                return create_connection_slice(
                    qs, info, kwargs, ProductVariantCountableConnection
                )

        return (
            PredicateByPromotionIdLoader(info.context)
            .load(root.node.id)
            .then(_get_variants)
        )

    @staticmethod
    def resolve_discount_value(
        root: ChannelContext[models.Promotion], info: ResolveInfo
    ):
        if not root.channel_slug:
            return None

        def _get_reward_value(rules):
            if rules:
                return rules[0].reward_value

        return (
            PromotionRulesByPromotionIdAndChannelSlugLoader(info.context)
            .load((root.node.id, root.channel_slug))
            .then(_get_reward_value)
        )

    @staticmethod
    def resolve_currency(root: ChannelContext[models.Promotion], info: ResolveInfo):
        if not root.channel_slug:
            return None

        def _get_currency(channel):
            if channel:
                return channel.currency_code

        return (
            ChannelBySlugLoader(info.context)
            .load(root.channel_slug)
            .then(_get_currency)
        )


class SaleCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        node = Sale

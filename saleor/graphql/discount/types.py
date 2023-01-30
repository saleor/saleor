import graphene
from graphene import relay

from ...discount import models
from ...permission.enums import DiscountPermissions, OrderPermissions
from ..channel import ChannelQsContext
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.types import (
    Channel,
    ChannelContext,
    ChannelContextType,
    ChannelContextTypeWithMetadata,
)
from ..core import ResolveInfo, types
from ..core.connection import CountableConnection, create_connection_slice
from ..core.context import get_database_connection_name
from ..core.descriptions import ADDED_IN_31
from ..core.fields import ConnectionField, PermissionsField
from ..core.scalars import PositiveDecimal
from ..core.types import ModelObjectType, Money, NonNullList
from ..meta.types import ObjectWithMetadata
from ..product.types import (
    CategoryCountableConnection,
    CollectionCountableConnection,
    ProductCountableConnection,
    ProductVariantCountableConnection,
)
from ..translations.fields import TranslationField
from ..translations.types import SaleTranslation, VoucherTranslation
from .dataloaders import (
    SaleChannelListingBySaleIdAndChanneSlugLoader,
    SaleChannelListingBySaleIdLoader,
    VoucherChannelListingByVoucherIdAndChanneSlugLoader,
    VoucherChannelListingByVoucherIdLoader,
)
from .enums import (
    DiscountValueTypeEnum,
    OrderDiscountTypeEnum,
    SaleType,
    VoucherTypeEnum,
)


class SaleChannelListing(ModelObjectType[models.SaleChannelListing]):
    id = graphene.GlobalID(required=True)
    channel = graphene.Field(Channel, required=True)
    discount_value = graphene.Float(required=True)
    currency = graphene.String(required=True)

    class Meta:
        description = "Represents sale channel listing."
        model = models.SaleChannelListing
        interfaces = [relay.Node]

    @staticmethod
    def resolve_channel(root: models.SaleChannelListing, info: ResolveInfo):
        return ChannelByIdLoader(info.context).load(root.channel_id)


class Sale(ChannelContextTypeWithMetadata, ModelObjectType[models.Sale]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    type = SaleType(required=True)
    start_date = graphene.DateTime(required=True)
    end_date = graphene.DateTime()
    created = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
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
        node = Sale


class VoucherChannelListing(ModelObjectType[models.VoucherChannelListing]):
    id = graphene.GlobalID(required=True)
    channel = graphene.Field(Channel, required=True)
    discount_value = graphene.Float(required=True)
    currency = graphene.String(required=True)
    min_spent = graphene.Field(Money)

    class Meta:
        description = "Represents voucher channel listing."
        model = models.VoucherChannelListing
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_channel(root: models.VoucherChannelListing, info: ResolveInfo):
        return ChannelByIdLoader(info.context).load(root.channel_id)


class Voucher(ChannelContextTypeWithMetadata[models.Voucher]):
    id = graphene.GlobalID(required=True)
    name = graphene.String()
    code = graphene.String(required=True)
    usage_limit = graphene.Int()
    used = graphene.Int(required=True)
    start_date = graphene.DateTime(required=True)
    end_date = graphene.DateTime()
    apply_once_per_order = graphene.Boolean(required=True)
    apply_once_per_customer = graphene.Boolean(required=True)
    only_for_staff = graphene.Boolean(required=True)
    min_checkout_items_quantity = graphene.Int()
    categories = ConnectionField(
        CategoryCountableConnection,
        description="List of categories this voucher applies to.",
    )
    collections = ConnectionField(
        CollectionCountableConnection,
        description="List of collections this voucher applies to.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
    )
    products = ConnectionField(
        ProductCountableConnection,
        description="List of products this voucher applies to.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
    )
    variants = ConnectionField(
        ProductVariantCountableConnection,
        description="List of product variants this voucher applies to." + ADDED_IN_31,
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
    )
    countries = NonNullList(
        types.CountryDisplay,
        description="List of countries available for the shipping voucher.",
    )
    translation = TranslationField(
        VoucherTranslation,
        type_name="voucher",
        resolver=ChannelContextType.resolve_translation,
    )
    discount_value_type = DiscountValueTypeEnum(
        description="Determines a type of discount for voucher - value or percentage",
        required=True,
    )
    discount_value = graphene.Float(description="Voucher value.")
    currency = graphene.String(description="Currency code for voucher.")
    min_spent = graphene.Field(
        Money, description="Minimum order value to apply voucher."
    )
    type = VoucherTypeEnum(description="Determines a type of voucher.", required=True)
    channel_listings = PermissionsField(
        NonNullList(VoucherChannelListing),
        description="List of availability in channels for the voucher.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Vouchers allow giving discounts to particular customers on categories, "
            "collections or specific products. They can be used during checkout by "
            "providing valid voucher codes."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Voucher

    @staticmethod
    def resolve_categories(
        root: ChannelContext[models.Voucher], info: ResolveInfo, **kwargs
    ):
        qs = root.node.categories.all()
        return create_connection_slice(qs, info, kwargs, CategoryCountableConnection)

    @staticmethod
    def resolve_collections(
        root: ChannelContext[models.Voucher], info: ResolveInfo, **kwargs
    ):
        qs = root.node.collections.all()
        qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)
        return create_connection_slice(qs, info, kwargs, CollectionCountableConnection)

    @staticmethod
    def resolve_products(
        root: ChannelContext[models.Voucher], info: ResolveInfo, **kwargs
    ):
        qs = root.node.products.all()
        qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)
        return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

    @staticmethod
    def resolve_variants(
        root: ChannelContext[models.Voucher], info: ResolveInfo, **kwargs
    ):
        qs = root.node.variants.all()
        qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)
        return create_connection_slice(
            qs, info, kwargs, ProductVariantCountableConnection
        )

    @staticmethod
    def resolve_countries(root: ChannelContext[models.Voucher], _info: ResolveInfo):
        return [
            types.CountryDisplay(code=country.code, country=country.name)
            for country in root.node.countries
        ]

    @staticmethod
    def resolve_discount_value(root: ChannelContext[models.Voucher], info: ResolveInfo):
        if not root.channel_slug:
            return None

        return (
            VoucherChannelListingByVoucherIdAndChanneSlugLoader(info.context)
            .load((root.node.id, root.channel_slug))
            .then(
                lambda channel_listing: channel_listing.discount_value
                if channel_listing
                else None
            )
        )

    @staticmethod
    def resolve_currency(root: ChannelContext[models.Voucher], info: ResolveInfo):
        if not root.channel_slug:
            return None

        return (
            VoucherChannelListingByVoucherIdAndChanneSlugLoader(info.context)
            .load((root.node.id, root.channel_slug))
            .then(
                lambda channel_listing: channel_listing.currency
                if channel_listing
                else None
            )
        )

    @staticmethod
    def resolve_min_spent(root: ChannelContext[models.Voucher], info: ResolveInfo):
        if not root.channel_slug:
            return None

        return (
            VoucherChannelListingByVoucherIdAndChanneSlugLoader(info.context)
            .load((root.node.id, root.channel_slug))
            .then(
                lambda channel_listing: channel_listing.min_spent
                if channel_listing
                else None
            )
        )

    @staticmethod
    def resolve_channel_listings(
        root: ChannelContext[models.Voucher], info: ResolveInfo
    ):
        return VoucherChannelListingByVoucherIdLoader(info.context).load(root.node.id)


class VoucherCountableConnection(CountableConnection):
    class Meta:
        node = Voucher


class OrderDiscount(ModelObjectType[models.OrderDiscount]):
    id = graphene.GlobalID(required=True)
    type = OrderDiscountTypeEnum(required=True)
    name = graphene.String()
    translated_name = graphene.String()
    value_type = graphene.Field(
        DiscountValueTypeEnum,
        required=True,
        description="Type of the discount: fixed or percent",
    )
    value = PositiveDecimal(
        required=True,
        description="Value of the discount. Can store fixed value or percent value",
    )
    reason = PermissionsField(
        graphene.String,
        required=False,
        description="Explanation for the applied discount.",
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    amount = graphene.Field(
        Money, description="Returns amount of discount.", required=True
    )

    class Meta:
        description = (
            "Contains all details related to the applied discount to the order."
        )
        interfaces = [relay.Node]
        model = models.OrderDiscount

    @staticmethod
    def resolve_reason(root: models.OrderDiscount, _info: ResolveInfo):
        return root.reason

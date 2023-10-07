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
from ...core import ResolveInfo, types
from ...core.connection import CountableConnection, create_connection_slice
from ...core.descriptions import ADDED_IN_31
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.fields import ConnectionField, PermissionsField
from ...core.types import ModelObjectType, Money, NonNullList
from ...meta.types import ObjectWithMetadata
from ...product.types import (
    CategoryCountableConnection,
    CollectionCountableConnection,
    ProductCountableConnection,
    ProductVariantCountableConnection,
)
from ...translations.fields import TranslationField
from ...translations.types import VoucherTranslation
from ..dataloaders import (
    VoucherChannelListingByVoucherIdAndChanneSlugLoader,
    VoucherChannelListingByVoucherIdLoader,
)
from ..enums import DiscountValueTypeEnum, VoucherTypeEnum


class VoucherChannelListing(ModelObjectType[models.VoucherChannelListing]):
    id = graphene.GlobalID(required=True, description="The ID of channel listing.")
    channel = graphene.Field(
        Channel,
        required=True,
        description="The channel in which voucher can be applied.",
    )
    discount_value = graphene.Float(
        required=True, description="The value of the discount on voucher in a channel."
    )
    currency = graphene.String(
        required=True, description="Currency code for voucher in a channel."
    )
    min_spent = graphene.Field(
        Money, description="Minimum order value for voucher to apply in channel."
    )

    class Meta:
        description = "Represents voucher channel listing."
        model = models.VoucherChannelListing
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_channel(root: models.VoucherChannelListing, info: ResolveInfo):
        return ChannelByIdLoader(info.context).load(root.channel_id)


class Voucher(ChannelContextTypeWithMetadata[models.Voucher]):
    id = graphene.GlobalID(required=True, description="The ID of the voucher.")
    name = graphene.String(description="The name of the voucher.")
    code = graphene.String(required=True, description="The code of the voucher.")
    usage_limit = graphene.Int(description="The number of times a voucher can be used.")
    used = graphene.Int(required=True, description="Usage count of the voucher.")
    start_date = graphene.DateTime(
        required=True, description="The start date and time of voucher."
    )
    end_date = graphene.DateTime(description="The end date and time of voucher.")
    apply_once_per_order = graphene.Boolean(
        required=True,
        description="Determine if the voucher should be applied once per order. If set "
        "to True, the voucher is applied to a single cheapest eligible product in "
        "checkout.",
    )
    apply_once_per_customer = graphene.Boolean(
        required=True,
        description="Determine if the voucher usage should be limited to one use per "
        "customer.",
    )
    only_for_staff = graphene.Boolean(
        required=True,
        description="Determine if the voucher is available only for staff members.",
    )
    min_checkout_items_quantity = graphene.Int(
        description="Determine minimum quantity of items for checkout."
    )
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
        doc_category = DOC_CATEGORY_DISCOUNTS
        node = Voucher

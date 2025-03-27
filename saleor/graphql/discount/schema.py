import graphene

from ...permission.enums import DiscountPermissions
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import (
    DEPRECATED_IN_3X_INPUT,
)
from ..core.doc_category import DOC_CATEGORY_DISCOUNTS
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.types import FilterInputObjectType
from ..core.utils import from_global_id_or_error
from ..translations.mutations import (
    PromotionRuleTranslate,
    PromotionTranslate,
    SaleTranslate,
    VoucherTranslate,
)
from .filters import PromotionWhereInput, SaleFilter, VoucherFilter
from .mutations import (
    PromotionBulkDelete,
    PromotionCreate,
    PromotionDelete,
    PromotionRuleCreate,
    PromotionRuleDelete,
    PromotionRuleUpdate,
    PromotionUpdate,
    SaleAddCatalogues,
    SaleChannelListingUpdate,
    SaleCreate,
    SaleDelete,
    SaleRemoveCatalogues,
    SaleUpdate,
    VoucherAddCatalogues,
    VoucherChannelListingUpdate,
    VoucherCodeBulkDelete,
    VoucherCreate,
    VoucherDelete,
    VoucherRemoveCatalogues,
    VoucherUpdate,
)
from .mutations.bulk_mutations import SaleBulkDelete, VoucherBulkDelete
from .resolvers import (
    resolve_promotion,
    resolve_promotions,
    resolve_sale,
    resolve_sales,
    resolve_voucher,
    resolve_vouchers,
)
from .sorters import PromotionSortingInput, SaleSortingInput, VoucherSortingInput
from .types import (
    Promotion,
    Sale,
    SaleCountableConnection,
    Voucher,
    VoucherCountableConnection,
)
from .types.promotions import PromotionCountableConnection


class VoucherFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        filterset_class = VoucherFilter


class SaleFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        filterset_class = SaleFilter


class DiscountQueries(graphene.ObjectType):
    sale = PermissionsField(
        Sale,
        id=graphene.Argument(graphene.ID, description="ID of the sale.", required=True),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a sale by ID.",
        deprecation_reason="Use the `promotion` query instead.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )
    sales = FilterConnectionField(
        SaleCountableConnection,
        filter=SaleFilterInput(description="Filtering options for sales."),
        sort_by=SaleSortingInput(description="Sort sales."),
        query=graphene.String(
            description=(
                "Search sales by name, value or type. "
                f"{DEPRECATED_IN_3X_INPUT} Use `filter.search` input instead."
            )
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of the shop's sales.",
        deprecation_reason="Use the `promotions` query instead.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )
    voucher = PermissionsField(
        Voucher,
        id=graphene.Argument(
            graphene.ID, description="ID of the voucher.", required=True
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a voucher by ID.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )
    vouchers = FilterConnectionField(
        VoucherCountableConnection,
        filter=VoucherFilterInput(description="Filtering options for vouchers."),
        sort_by=VoucherSortingInput(description="Sort voucher."),
        query=graphene.String(
            description=(
                "Search vouchers by name or code. "
                f"{DEPRECATED_IN_3X_INPUT} Use `filter.search` input instead."
            )
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of the shop's vouchers.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )
    promotion = PermissionsField(
        Promotion,
        id=graphene.Argument(
            graphene.ID, description="ID of the promotion.", required=True
        ),
        description="Look up a promotion by ID.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )
    promotions = FilterConnectionField(
        PromotionCountableConnection,
        where=PromotionWhereInput(description="Where filtering options."),
        sort_by=PromotionSortingInput(description="Sort promotions."),
        description="List of the promotions.",
        permissions=[DiscountPermissions.MANAGE_DISCOUNTS],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )

    @staticmethod
    def resolve_sale(_root, info, *, id, channel=None):
        _, id = from_global_id_or_error(id, Sale)
        return resolve_sale(info, id, channel)

    @staticmethod
    def resolve_sales(_root, info: ResolveInfo, *, channel=None, **kwargs):
        qs = resolve_sales(info, channel_slug=channel, **kwargs)
        kwargs["channel"] = channel
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, SaleCountableConnection)

    @staticmethod
    def resolve_voucher(_root, info: ResolveInfo, *, id, channel=None):
        _, id = from_global_id_or_error(id, Voucher)
        return resolve_voucher(info, id, channel)

    @staticmethod
    def resolve_vouchers(_root, info: ResolveInfo, *, channel=None, **kwargs):
        qs = resolve_vouchers(info, channel_slug=channel, **kwargs)
        kwargs["channel"] = channel
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, VoucherCountableConnection)

    @staticmethod
    def resolve_promotion(_root, info, *, id, channel=None):
        _, id = from_global_id_or_error(id, Promotion)
        return resolve_promotion(info, id)

    @staticmethod
    def resolve_promotions(_root, info: ResolveInfo, **kwargs):
        qs = resolve_promotions(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, PromotionCountableConnection)


class DiscountMutations(graphene.ObjectType):
    promotion_create = PromotionCreate.Field()
    promotion_update = PromotionUpdate.Field()
    promotion_delete = PromotionDelete.Field()
    promotion_rule_create = PromotionRuleCreate.Field()
    promotion_rule_update = PromotionRuleUpdate.Field()
    promotion_rule_delete = PromotionRuleDelete.Field()
    promotion_translate = PromotionTranslate.Field()
    promotion_rule_translate = PromotionRuleTranslate.Field()
    promotion_bulk_delete = PromotionBulkDelete.Field()

    sale_create = SaleCreate.Field(
        deprecation_reason="Use `promotionCreate` mutation instead."
    )
    sale_delete = SaleDelete.Field(
        deprecation_reason="Use `promotionDelete` mutation instead."
    )
    sale_bulk_delete = SaleBulkDelete.Field()
    sale_update = SaleUpdate.Field(
        deprecation_reason="Use `promotionUpdate` mutation instead."
    )
    sale_catalogues_add = SaleAddCatalogues.Field(
        deprecation_reason="Use `promotionRuleCreate` and `promotionRuleUpdate` mutations instead."
    )
    sale_catalogues_remove = SaleRemoveCatalogues.Field(
        deprecation_reason="Use `promotionRuleUpdate` and `promotionRuleDelete` mutations instead."
    )
    sale_translate = SaleTranslate.Field(
        deprecation_reason="Use `promotionTranslate` mutation instead."
    )
    sale_channel_listing_update = SaleChannelListingUpdate.Field(
        deprecation_reason="Use `promotionRuleUpdate` mutation instead."
    )

    voucher_create = VoucherCreate.Field()
    voucher_delete = VoucherDelete.Field()
    voucher_bulk_delete = VoucherBulkDelete.Field()
    voucher_update = VoucherUpdate.Field()
    voucher_catalogues_add = VoucherAddCatalogues.Field()
    voucher_catalogues_remove = VoucherRemoveCatalogues.Field()
    voucher_translate = VoucherTranslate.Field()
    voucher_channel_listing_update = VoucherChannelListingUpdate.Field()
    voucher_code_bulk_delete = VoucherCodeBulkDelete.Field()

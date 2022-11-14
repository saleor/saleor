import graphene

from ...core.permissions import DiscountPermissions
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import DEPRECATED_IN_3X_INPUT
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.types import FilterInputObjectType
from ..core.utils import from_global_id_or_error
from ..translations.mutations import SaleTranslate, VoucherTranslate
from .filters import SaleFilter, VoucherFilter
from .mutations.bulk_mutations import SaleBulkDelete, VoucherBulkDelete
from .mutations.sale_add_catalogues import SaleAddCatalogues
from .mutations.sale_channel_listing_update import SaleChannelListingUpdate
from .mutations.sale_create import SaleCreate
from .mutations.sale_delete import SaleDelete
from .mutations.sale_remove_catalogues import SaleRemoveCatalogues
from .mutations.sale_update import SaleUpdate
from .mutations.voucher_add_catalogues import VoucherAddCatalogues
from .mutations.voucher_channel_listing_update import VoucherChannelListingUpdate
from .mutations.voucher_create import VoucherCreate
from .mutations.voucher_delete import VoucherDelete
from .mutations.voucher_remove_catalogues import VoucherRemoveCatalogues
from .mutations.voucher_update import VoucherUpdate
from .resolvers import resolve_sale, resolve_sales, resolve_voucher, resolve_vouchers
from .sorters import SaleSortingInput, VoucherSortingInput
from .types import Sale, SaleCountableConnection, Voucher, VoucherCountableConnection


class VoucherFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = VoucherFilter


class SaleFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = SaleFilter


class DiscountQueries(graphene.ObjectType):
    sale = PermissionsField(
        Sale,
        id=graphene.Argument(graphene.ID, description="ID of the sale.", required=True),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a sale by ID.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
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
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
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
    )

    @staticmethod
    def resolve_sale(_root, _info, *, id, channel=None):
        _, id = from_global_id_or_error(id, Sale)
        return resolve_sale(id, channel)

    @staticmethod
    def resolve_sales(_root, info, *, channel=None, **kwargs):
        qs = resolve_sales(info, channel_slug=channel, **kwargs)
        kwargs["channel"] = channel
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, SaleCountableConnection)

    @staticmethod
    def resolve_voucher(_root, _info, *, id, channel=None):
        _, id = from_global_id_or_error(id, Voucher)
        return resolve_voucher(id, channel)

    @staticmethod
    def resolve_vouchers(_root, info, *, channel=None, **kwargs):
        qs = resolve_vouchers(info, channel_slug=channel, **kwargs)
        kwargs["channel"] = channel
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, VoucherCountableConnection)


class DiscountMutations(graphene.ObjectType):
    sale_create = SaleCreate.Field()
    sale_delete = SaleDelete.Field()
    sale_bulk_delete = SaleBulkDelete.Field()
    sale_update = SaleUpdate.Field()
    sale_catalogues_add = SaleAddCatalogues.Field()
    sale_catalogues_remove = SaleRemoveCatalogues.Field()
    sale_translate = SaleTranslate.Field()
    sale_channel_listing_update = SaleChannelListingUpdate.Field()

    voucher_create = VoucherCreate.Field()
    voucher_delete = VoucherDelete.Field()
    voucher_bulk_delete = VoucherBulkDelete.Field()
    voucher_update = VoucherUpdate.Field()
    voucher_catalogues_add = VoucherAddCatalogues.Field()
    voucher_catalogues_remove = VoucherRemoveCatalogues.Field()
    voucher_translate = VoucherTranslate.Field()
    voucher_channel_listing_update = VoucherChannelListingUpdate.Field()

import graphene

from ...core.permissions import DiscountPermissions
from ...discount import models
from ...discount.utils import fetch_catalogue_info
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types import DiscountError, NonNullList
from .mutations.utils import convert_catalogue_info_to_global_ids
from .types import Sale, Voucher


class SaleBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of sale IDs to delete."
        )

    class Meta:
        description = "Deletes sales."
        model = models.Sale
        object_type = Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def bulk_action(cls, info, queryset):
        sales_and_catalogues = [
            (sale, convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale)))
            for sale in list(queryset)
        ]
        queryset.delete()
        for sale, previous_catalogue in sales_and_catalogues:
            info.context.plugins.sale_deleted(sale, previous_catalogue)


class VoucherBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of voucher IDs to delete."
        )

    class Meta:
        description = "Deletes vouchers."
        model = models.Voucher
        object_type = Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def bulk_action(cls, info, queryset):
        vouchers = list(queryset)
        queryset.delete()
        for voucher in vouchers:
            info.context.plugins.voucher_deleted(voucher)

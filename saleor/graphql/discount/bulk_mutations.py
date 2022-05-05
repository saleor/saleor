import graphene

from ...core.permissions import DiscountPermissions
from ...discount import models
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types import DiscountError, NonNullList
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

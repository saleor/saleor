import graphene

from ...core.permissions import DiscountPermissions
from ...discount import models
from ..core.mutations import ModelBulkDeleteMutation


class SaleBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of sale IDs to delete."
        )

    class Meta:
        description = "Deletes sales."
        model = models.Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)


class VoucherBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of voucher IDs to delete."
        )

    class Meta:
        description = "Deletes vouchers."
        model = models.Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)

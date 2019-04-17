import graphene

from ...discount import models
from ..core.mutations import ModelBulkDeleteMutation


class SaleBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of sale IDs to delete.')

    class Meta:
        description = 'Deletes sales.'
        model = models.Sale
        permissions = ('discount.manage_discounts', )


class VoucherBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of voucher IDs to delete.')

    class Meta:
        description = 'Deletes vouchers.'
        model = models.Voucher
        permissions = ('discount.manage_discounts', )

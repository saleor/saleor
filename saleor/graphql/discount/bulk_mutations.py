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

    @classmethod
    def user_is_allowed(cls, user, ids):
        return user.has_perm('discount.manage_discounts')


class VoucherBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of voucher IDs to delete.')

    class Meta:
        description = 'Deletes vouchers.'
        model = models.Voucher

    @classmethod
    def user_is_allowed(cls, user, ids):
        return user.has_perm('discount.manage_discounts')

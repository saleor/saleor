import graphene

from ....order import models
from ...core.mutations import ModelBulkDeleteMutation


class DraftOrderBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of draft order IDs to delete.')

    class Meta:
        description = 'Deletes draft orders.'
        model = models.Order

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.manage_orders')

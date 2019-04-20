import graphene
from django.core.exceptions import ValidationError

from ....order import OrderStatus, models
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
        permissions = ('order.manage_orders', )

    @classmethod
    def clean_instance(cls, info, instance):
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError({'id': 'Cannot delete non-draft orders.'})


class DraftOrderLinesBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of order lines IDs to delete.')

    class Meta:
        description = 'Deletes order lines.'
        model = models.OrderLine
        permissions = ('order.manage_orders', )

    @classmethod
    def clean_instance(cls, _info, instance):
        if instance.order.status != OrderStatus.DRAFT:
            raise ValidationError(
                {'id': 'Cannot delete line for non-draft orders.'})

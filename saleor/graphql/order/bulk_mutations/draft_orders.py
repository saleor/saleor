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

    @classmethod
    def clean_instance(cls, info, instance):
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError({'id': 'Cannot delete non-draft orders.'})

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.manage_orders')


class DraftOrderLinesBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of order lines IDs to delete.')

    class Meta:
        description = 'Deletes order lines.'
        model = models.OrderLine

    @classmethod
    def clean_instance(cls, info, instance, errors):
        if instance.order.status != OrderStatus.DRAFT:
            cls.add_error(errors, 'id', 'Cannot delete line for non-draft orders.')

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.manage_orders')

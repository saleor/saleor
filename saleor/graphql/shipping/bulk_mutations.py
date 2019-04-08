import graphene

from ...shipping import models
from ..core.mutations import ModelBulkDeleteMutation


class ShippingZoneBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of shipping zone IDs to delete.')

    class Meta:
        description = 'Deletes shipping zones.'
        model = models.ShippingZone

    @classmethod
    def user_is_allowed(cls, user, _data):
        return user.has_perm('shipping.manage_shipping')


class ShippingPriceBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of shipping price IDs to delete.')

    class Meta:
        description = 'Deletes shipping prices.'
        model = models.ShippingMethod

    @classmethod
    def user_is_allowed(cls, user, _data):
        return user.has_perm('shipping.manage_shipping')

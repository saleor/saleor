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
        permissions = ('shipping.manage_shipping', )


class ShippingPriceBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of shipping price IDs to delete.')

    class Meta:
        description = 'Deletes shipping prices.'
        model = models.ShippingMethod
        permissions = ('shipping.manage_shipping', )

import graphene

from ...core.permissions import ShippingPermissions
from ...shipping import models
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types.common import ShippingError
from .types import ShippingMethod, ShippingZone


class ShippingZoneBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description="List of shipping zone IDs to delete.",
        )

    class Meta:
        description = "Deletes shipping zones."
        model = models.ShippingZone
        object_type = ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"


class ShippingPriceBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description="List of shipping price IDs to delete.",
        )

    class Meta:
        description = "Deletes shipping prices."
        model = models.ShippingMethod
        object_type = ShippingMethod
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def get_nodes_or_error(
        cls,
        ids,
        field,
        only_type=None,
        qs=None,
        schema=None,
    ):
        return super().get_nodes_or_error(
            ids,
            field,
            "ShippingMethodType",
            qs=models.ShippingMethod.objects,
            schema=schema,
        )

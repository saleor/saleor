import graphene

from ....permission.enums import ProductPermissions
from ....warehouse import models
from ...account.i18n import I18nMixin
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import NonNullList, WarehouseError
from ...shipping.types import ShippingZone
from ..types import Warehouse
from .warehouse_shipping_zone_assign import WarehouseShippingZoneAssign


class WarehouseShippingZoneUnassign(ModelMutation, I18nMixin):
    class Meta:
        model = models.Warehouse
        object_type = Warehouse
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        description = "Remove shipping zone from given warehouse."
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to update.", required=True)
        shipping_zone_ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of shipping zone IDs.",
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, shipping_zone_ids: list[str]
    ):
        warehouse = cls.get_node_or_error(info, id, only_type=Warehouse)
        shipping_zones = cls.get_nodes_or_error(
            shipping_zone_ids, "shipping_zone_id", only_type=ShippingZone
        )
        warehouse.shipping_zones.remove(*shipping_zones)
        return WarehouseShippingZoneAssign(warehouse=warehouse)

import graphene
import graphene_django_optimizer as gql_optimizer

from ...warehouse import models
from ..core.fields import FilterInputConnectionField
from ..decorators import permission_required
from .filters import WarehouseFilterInput
from .mutations import WarehouseCreate, WarehouseDelete, WarehouseUpdate
from .types import Warehouse


class WarehouseQueries(graphene.ObjectType):
    warehouse = graphene.Field(
        Warehouse,
        description="Look up an order by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of an warehouse", required=True
        ),
    )
    warehouses = FilterInputConnectionField(
        Warehouse,
        description="List of warehouses.",
        filter=WarehouseFilterInput(),
        query=graphene.String(),
    )

    @permission_required("warehouse.manage_warehouses")
    def resolve_warehouse(self, info, **data):
        warehouse_pk = data.get("id")
        warehouse = graphene.Node.get_node_from_global_id(info, warehouse_pk, Warehouse)
        return warehouse

    @permission_required("warehouse.manage_warehouses")
    def resolve_warehouses(self, info, **kwargs):
        qs = models.Warehouse.objects.all()
        return gql_optimizer.query(qs, info)


class WarehouseMutations(graphene.ObjectType):
    create_warehouse = WarehouseCreate.Field()
    update_warehouse = WarehouseUpdate.Field()
    delete_warehouse = WarehouseDelete.Field()

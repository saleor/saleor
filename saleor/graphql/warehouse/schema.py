import graphene
import graphene_django_optimizer as gql_optimizer
from graphql_jwt.decorators import login_required

from saleor.graphql.core.fields import PrefetchingConnectionField
from saleor.graphql.decorators import permission_required
from saleor.graphql.warehouse.mutations import (
    WarehouseCreate,
    WarehouseDelete,
    WarehouseUpdate,
)
from saleor.graphql.warehouse.types import Warehouse
from saleor.warehouse import models


class WarehouseQueries(graphene.ObjectType):
    warehouse = graphene.Field(
        Warehouse,
        description="Look up an order by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of an warehouse", required=True
        ),
    )
    warehouses = PrefetchingConnectionField(
        Warehouse, description="List of warehouses."
    )

    @login_required
    @permission_required("warehouse.manage_warehouses")
    def resolve_warehouse(self, _info, **data):
        warehouse_pk = data.get("id")
        warehouse = graphene.Node.get_node_from_global_id(
            _info, warehouse_pk, Warehouse
        )
        return warehouse

    @login_required
    @permission_required("warehouse.manage_warehouses")
    def resolve_warehouses(self, _info, **kwargs):
        qs = models.Warehouse.objects.all()
        return gql_optimizer.query(qs, _info)


class WarehouseMutations(graphene.ObjectType):
    create_warehouse = WarehouseCreate.Field()
    update_warehouse = WarehouseUpdate.Field()
    delete_warehouse = WarehouseDelete.Field()

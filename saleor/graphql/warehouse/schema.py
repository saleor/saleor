import graphene

from ...core.permissions import (
    OrderPermissions,
    ProductPermissions,
    ShippingPermissions,
)
from ..core.fields import FilterInputConnectionField
from ..core.utils import from_global_id_or_error
from ..decorators import one_of_permissions_required, permission_required
from .filters import StockFilterInput, WarehouseFilterInput
from .mutations import (
    WarehouseCreate,
    WarehouseDelete,
    WarehouseShippingZoneAssign,
    WarehouseShippingZoneUnassign,
    WarehouseUpdate,
)
from .resolvers import (
    resolve_stock,
    resolve_stocks,
    resolve_warehouse,
    resolve_warehouses,
)
from .sorters import WarehouseSortingInput
from .types import Stock, Warehouse


class WarehouseQueries(graphene.ObjectType):
    warehouse = graphene.Field(
        Warehouse,
        description="Look up a warehouse by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of an warehouse", required=True
        ),
    )
    warehouses = FilterInputConnectionField(
        Warehouse,
        description="List of warehouses.",
        filter=WarehouseFilterInput(),
        sort_by=WarehouseSortingInput(),
    )

    @one_of_permissions_required(
        [
            ProductPermissions.MANAGE_PRODUCTS,
            OrderPermissions.MANAGE_ORDERS,
            ShippingPermissions.MANAGE_SHIPPING,
        ]
    )
    def resolve_warehouse(self, info, **data):
        warehouse_pk = data.get("id")
        _, id = from_global_id_or_error(warehouse_pk, Warehouse)
        return resolve_warehouse(id)

    @one_of_permissions_required(
        [
            ProductPermissions.MANAGE_PRODUCTS,
            OrderPermissions.MANAGE_ORDERS,
            ShippingPermissions.MANAGE_SHIPPING,
        ]
    )
    def resolve_warehouses(self, info, **_kwargs):
        return resolve_warehouses()


class WarehouseMutations(graphene.ObjectType):
    create_warehouse = WarehouseCreate.Field()
    update_warehouse = WarehouseUpdate.Field()
    delete_warehouse = WarehouseDelete.Field()
    assign_warehouse_shipping_zone = WarehouseShippingZoneAssign.Field()
    unassign_warehouse_shipping_zone = WarehouseShippingZoneUnassign.Field()


class StockQueries(graphene.ObjectType):
    stock = graphene.Field(
        Stock,
        description="Look up a stock by ID",
        id=graphene.ID(required=True, description="ID of an warehouse"),
    )
    stocks = FilterInputConnectionField(
        Stock, description="List of stocks.", filter=StockFilterInput()
    )

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_stock(self, info, **kwargs):
        stock_id = kwargs.get("id")
        _, id = from_global_id_or_error(stock_id, Stock)
        return resolve_stock(id)

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_stocks(self, info, **_kwargs):
        return resolve_stocks()

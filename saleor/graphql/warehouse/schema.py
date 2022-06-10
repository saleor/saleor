import graphene

from ...core.permissions import (
    OrderPermissions,
    ProductPermissions,
    ShippingPermissions,
)
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.utils import from_global_id_or_error
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
from .types import (
    Stock,
    StockCountableConnection,
    Warehouse,
    WarehouseCountableConnection,
)


class WarehouseQueries(graphene.ObjectType):
    warehouse = PermissionsField(
        Warehouse,
        description="Look up a warehouse by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of an warehouse", required=True
        ),
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
            OrderPermissions.MANAGE_ORDERS,
            ShippingPermissions.MANAGE_SHIPPING,
        ],
    )
    warehouses = FilterConnectionField(
        WarehouseCountableConnection,
        description="List of warehouses.",
        filter=WarehouseFilterInput(),
        sort_by=WarehouseSortingInput(),
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
            OrderPermissions.MANAGE_ORDERS,
            ShippingPermissions.MANAGE_SHIPPING,
        ],
    )

    @staticmethod
    def resolve_warehouse(_root, _info, **data):
        warehouse_pk = data.get("id")
        _, id = from_global_id_or_error(warehouse_pk, Warehouse)
        return resolve_warehouse(id)

    @staticmethod
    def resolve_warehouses(_root, info, **kwargs):
        qs = resolve_warehouses()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, WarehouseCountableConnection)


class WarehouseMutations(graphene.ObjectType):
    create_warehouse = WarehouseCreate.Field()
    update_warehouse = WarehouseUpdate.Field()
    delete_warehouse = WarehouseDelete.Field()
    assign_warehouse_shipping_zone = WarehouseShippingZoneAssign.Field()
    unassign_warehouse_shipping_zone = WarehouseShippingZoneUnassign.Field()


class StockQueries(graphene.ObjectType):
    stock = PermissionsField(
        Stock,
        description="Look up a stock by ID",
        id=graphene.ID(required=True, description="ID of an warehouse"),
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    stocks = FilterConnectionField(
        StockCountableConnection,
        description="List of stocks.",
        filter=StockFilterInput(),
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )

    @staticmethod
    def resolve_stock(_root, _info, **kwargs):
        stock_id = kwargs.get("id")
        _, id = from_global_id_or_error(stock_id, Stock)
        return resolve_stock(id)

    @staticmethod
    def resolve_stocks(_root, info, **kwargs):
        qs = resolve_stocks()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, StockCountableConnection)

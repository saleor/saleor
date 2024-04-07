import graphene

from ...permission.enums import (
    OrderPermissions,
    ProductPermissions,
    ShippingPermissions,
)
from ...warehouse import models
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_310
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.utils import from_global_id_or_error
from ..core.utils.resolvers import resolve_by_global_id_or_ext_ref
from .bulk_mutations import StockBulkUpdate
from .filters import StockFilterInput, WarehouseFilterInput
from .mutations import (
    WarehouseCreate,
    WarehouseDelete,
    WarehouseShippingZoneAssign,
    WarehouseShippingZoneUnassign,
    WarehouseUpdate,
)
from .resolvers import resolve_stock, resolve_stocks, resolve_warehouses
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
        id=graphene.Argument(graphene.ID, description="ID of a warehouse."),
        external_reference=graphene.Argument(
            graphene.String, description=f"External ID of a warehouse. {ADDED_IN_310}"
        ),
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
            OrderPermissions.MANAGE_ORDERS,
            ShippingPermissions.MANAGE_SHIPPING,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
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
        doc_category=DOC_CATEGORY_PRODUCTS,
    )

    @staticmethod
    def resolve_warehouse(
        _root, info: ResolveInfo, /, *, id=None, external_reference=None
    ):
        return resolve_by_global_id_or_ext_ref(
            info, models.Warehouse, id, external_reference
        )

    @staticmethod
    def resolve_warehouses(_root, info: ResolveInfo, **kwargs):
        qs = resolve_warehouses(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
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
        id=graphene.ID(required=True, description="ID of a stock"),
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    stocks = FilterConnectionField(
        StockCountableConnection,
        description="List of stocks.",
        filter=StockFilterInput(),
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )

    @staticmethod
    def resolve_stock(_root, info: ResolveInfo, /, *, id: str):
        _, id = from_global_id_or_error(id, Stock)
        return resolve_stock(info, id)

    @staticmethod
    def resolve_stocks(_root, info: ResolveInfo, **kwargs):
        qs = resolve_stocks(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, StockCountableConnection)


class StockMutations(graphene.ObjectType):
    stock_bulk_update = StockBulkUpdate.Field()

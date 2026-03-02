import graphene

from ...permission.enums import WarehousePermissions
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.utils import from_global_id_or_error
from .mutations import (
    AddOrderToPurchaseOrder,
    AddPurchaseOrderItem,
    PurchaseOrderConfirm,
    PurchaseOrderCreate,
    PurchaseOrderDelete,
    PurchaseOrderUpdate,
    ReceiptComplete,
    ReceiptDelete,
    ReceiptLineDelete,
    ReceiptReceiveItem,
    ReceiptStart,
    RemoveOrderFromPurchaseOrder,
    RemovePurchaseOrderItem,
    ResolveProductDiscrepancy,
    UpdatePurchaseOrderItem,
)
from .resolvers import (
    resolve_purchase_order,
    resolve_purchase_orders,
    resolve_receipt,
    resolve_receipts,
)
from .types import (
    ProductDiscrepancy,
    PurchaseOrder,
    PurchaseOrderCountableConnection,
    PurchaseOrderItemAdjustment,
    PurchaseOrderItemAdjustmentCountableConnection,
    Receipt,
    ReceiptCountableConnection,
)


class InventoryQueries(graphene.ObjectType):
    purchase_order = PermissionsField(
        PurchaseOrder,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the purchase order.",
            required=True,
        ),
        description="Look up a purchase order by ID.",
        permissions=[
            WarehousePermissions.MANAGE_PURCHASE_ORDERS,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    purchase_orders = FilterConnectionField(
        PurchaseOrderCountableConnection,
        description="List of purchase orders.",
        permissions=[
            WarehousePermissions.MANAGE_PURCHASE_ORDERS,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    receipt = PermissionsField(
        Receipt,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the receipt.",
            required=True,
        ),
        description="Look up a receipt by ID.",
        permissions=[
            WarehousePermissions.MANAGE_STOCK,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    receipts = FilterConnectionField(
        ReceiptCountableConnection,
        description="List of goods receipts.",
        permissions=[
            WarehousePermissions.MANAGE_STOCK,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    purchase_order_item_adjustments = FilterConnectionField(
        PurchaseOrderItemAdjustmentCountableConnection,
        processed=graphene.Argument(
            graphene.Boolean,
            description="Filter by processed status. True=processed, False=pending, null=all.",
        ),
        description="List purchase order item adjustments with optional filtering.",
        permissions=[
            WarehousePermissions.MANAGE_STOCK,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    purchase_order_item_adjustment = PermissionsField(
        PurchaseOrderItemAdjustment,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the adjustment.",
            required=True,
        ),
        description="Look up a purchase order item adjustment by ID.",
        permissions=[
            WarehousePermissions.MANAGE_STOCK,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    product_discrepancies = PermissionsField(
        graphene.List(graphene.NonNull(ProductDiscrepancy)),
        receipt_id=graphene.Argument(
            graphene.ID,
            description="ID of the completed receipt.",
            required=True,
        ),
        description=(
            "Product-level discrepancy view for a completed receipt. "
            "Returns per-variant breakdown and affected orders for each "
            "product with unresolved POIAs."
        ),
        permissions=[
            WarehousePermissions.MANAGE_STOCK,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )

    @staticmethod
    def resolve_purchase_order(root, info: ResolveInfo, *, id):
        _, pk = from_global_id_or_error(id, "PurchaseOrder")
        return resolve_purchase_order(info, pk)

    @staticmethod
    def resolve_purchase_orders(root, info: ResolveInfo, **kwargs):
        qs = resolve_purchase_orders(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(
            qs, info, kwargs, PurchaseOrderCountableConnection
        )

    @staticmethod
    def resolve_receipt(root, info: ResolveInfo, *, id):
        _, pk = from_global_id_or_error(id, "Receipt")
        return resolve_receipt(info, pk)

    @staticmethod
    def resolve_receipts(root, info: ResolveInfo, **kwargs):
        qs = resolve_receipts(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, ReceiptCountableConnection)

    @staticmethod
    def resolve_purchase_order_item_adjustments(root, info: ResolveInfo, **kwargs):
        from ...inventory.models import PurchaseOrderItemAdjustment

        processed = kwargs.pop("processed", None)
        qs = PurchaseOrderItemAdjustment.objects.all()

        if processed is True:
            qs = qs.filter(processed_at__isnull=False)
        elif processed is False:
            qs = qs.filter(processed_at__isnull=True)

        qs = qs.order_by("-created_at")
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(
            qs, info, kwargs, PurchaseOrderItemAdjustmentCountableConnection
        )

    @staticmethod
    def resolve_purchase_order_item_adjustment(root, info: ResolveInfo, *, id):
        from ...inventory.models import PurchaseOrderItemAdjustment

        _, pk = from_global_id_or_error(id, PurchaseOrderItemAdjustment)
        return PurchaseOrderItemAdjustment.objects.filter(pk=pk).first()

    @staticmethod
    def resolve_product_discrepancies(root, info: ResolveInfo, *, receipt_id):
        from ...inventory.models import Receipt as ReceiptModel
        from ...inventory.receipt_workflow import get_product_discrepancies

        _, pk = from_global_id_or_error(receipt_id, "Receipt")
        receipt = ReceiptModel.objects.filter(pk=pk).first()
        if not receipt:
            return []
        return get_product_discrepancies(receipt)


class InventoryMutations(graphene.ObjectType):
    create_purchase_order = PurchaseOrderCreate.Field()
    update_purchase_order = PurchaseOrderUpdate.Field()
    confirm_purchase_order = PurchaseOrderConfirm.Field()
    delete_purchase_order = PurchaseOrderDelete.Field()
    add_order_to_purchase_order = AddOrderToPurchaseOrder.Field()
    remove_order_from_purchase_order = RemoveOrderFromPurchaseOrder.Field()
    add_purchase_order_item = AddPurchaseOrderItem.Field()
    update_purchase_order_item = UpdatePurchaseOrderItem.Field()
    remove_purchase_order_item = RemovePurchaseOrderItem.Field()

    # Receipt workflow mutations
    start_receipt = ReceiptStart.Field()
    receive_item = ReceiptReceiveItem.Field()
    complete_receipt = ReceiptComplete.Field()
    delete_receipt = ReceiptDelete.Field()
    delete_receipt_line = ReceiptLineDelete.Field()

    # POIA resolution
    resolve_product_discrepancy = ResolveProductDiscrepancy.Field()

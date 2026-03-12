import graphene

from ...inventory import models
from ..channel.dataloaders.by_self import ChannelByIdLoader
from ..core import ResolveInfo
from ..core.connection import CountableConnection
from ..core.context import ChannelContext
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.enums import PurchaseOrderErrorCode, ReceiptErrorCode
from ..core.scalars import DateTime, PositiveDecimal
from ..core.types import BaseInputObjectType, Error, ModelObjectType, Money, NonNullList
from ..meta.inputs import MetadataInput
from ..product.dataloaders import ProductVariantByIdLoader
from ..warehouse.dataloaders import WarehouseByIdLoader
from .dataloaders import PurchaseOrderByIdLoader
from .enums import (
    PurchaseOrderItemAdjustmentReasonEnum,
    PurchaseOrderItemAdjustmentStatusEnum,
    PurchaseOrderItemStatusEnum,
    PurchaseOrderStatusEnum,
)


class PurchaseOrder(ModelObjectType[models.PurchaseOrder]):
    id = graphene.GlobalID(required=True, description="The ID of the purchase order.")
    name = graphene.String(
        required=True,
        description="Name of the purchase order.",
    )
    supplier_warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse",
        required=True,
        description="Supplier warehouse (non-owned).",
    )
    destination_warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse",
        required=True,
        description="Destination warehouse (owned).",
    )

    channel = graphene.Field(
        "saleor.graphql.channel.types.Channel",
        required=False,
        description="Channel this purchase order is associated with.",
    )

    status = PurchaseOrderStatusEnum(
        required=True, description="Current status of the purchase order."
    )

    items = graphene.List(
        lambda: PurchaseOrderItem,
        required=True,
        description="Items in this purchase order.",
    )

    currency = graphene.String(
        required=True,
        description="Default currency for this purchase order.",
    )

    auto_reallocate_variants = graphene.Boolean(
        required=True,
        description="Whether variants are automatically reallocated on receipt.",
    )

    has_linked_orders = graphene.Boolean(
        required=True,
        description="Whether any orders are linked to this PO via requested allocations.",
    )

    linked_orders = graphene.List(
        graphene.NonNull("saleor.graphql.order.types.Order"),
        required=True,
        description="Orders linked to this PO via requested allocations.",
    )

    created_at = DateTime(
        required=True,
        description="When the purchase order was created.",
    )

    class Meta:
        description = "Represents a purchase order from a supplier."
        model = models.PurchaseOrder
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_supplier_warehouse(root, info: ResolveInfo):
        return WarehouseByIdLoader(info.context).load(root.source_warehouse_id)

    @staticmethod
    def resolve_destination_warehouse(root, info: ResolveInfo):
        return WarehouseByIdLoader(info.context).load(root.destination_warehouse_id)

    @staticmethod
    def resolve_channel(root, info: ResolveInfo):
        if root.channel_id is None:
            return None
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    def resolve_has_linked_orders(root, info: ResolveInfo):
        return root.requested_allocations.exists()

    @staticmethod
    def resolve_linked_orders(root, info: ResolveInfo):
        from ...order.models import Order
        from ..core.context import SyncWebhookControlContext

        orders = Order.objects.filter(
            lines__allocations__purchase_order_requested_allocations__purchase_order=root,
        ).distinct()
        return [
            SyncWebhookControlContext(node=order, allow_sync_webhooks=False)
            for order in orders
        ]

    @staticmethod
    def resolve_items(root, info: ResolveInfo):
        return root.items.all()


class PurchaseOrderItem(ModelObjectType[models.PurchaseOrderItem]):
    id = graphene.GlobalID(
        required=True, description="The ID of the purchase order item."
    )
    purchase_order = graphene.Field(
        PurchaseOrder, required=True, description="Parent purchase order."
    )
    product_variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant",
        required=True,
        description="Product variant ordered.",
    )
    quantity_ordered = graphene.Int(required=True, description="Quantity ordered.")
    quantity_received = graphene.Int(
        required=True, description="Total quantity received across all receipt lines."
    )

    unit_price = graphene.Field(
        Money,
        description="Unit cost (buy price). Null for items added from orders before pricing.",
    )
    country_of_origin = graphene.String(
        description="Country of origin (ISO 2-letter code)."
    )
    status = PurchaseOrderItemStatusEnum(
        required=True, description="Status of this purchase order item."
    )

    class Meta:
        description = "Represents a line item in a purchase order."
        model = models.PurchaseOrderItem
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_purchase_order(root, info: ResolveInfo):
        return PurchaseOrderByIdLoader(info.context).load(root.order_id)

    @staticmethod
    def resolve_product_variant(root, info: ResolveInfo):
        return (
            ProductVariantByIdLoader(info.context)
            .load(root.product_variant_id)
            .then(lambda variant: ChannelContext(node=variant, channel_slug=None))
        )

    @staticmethod
    def resolve_country_of_origin(root: models.PurchaseOrderItem, info: ResolveInfo):
        if root.country_of_origin:
            return str(root.country_of_origin)
        return None

    @staticmethod
    def resolve_unit_price(root: models.PurchaseOrderItem, info: ResolveInfo):
        if root.currency is None or root.total_price_amount is None:
            return None
        return root.unit_price


class PurchaseOrderCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        node = PurchaseOrder


# Error types
class PurchaseOrderError(Error):
    code = PurchaseOrderErrorCode(description="The error code.", required=True)
    warehouses = NonNullList(
        graphene.ID,
        description="List of warehouse IDs which cause the error.",
        required=False,
    )
    variants = NonNullList(
        graphene.ID,
        description="List of variant IDs which cause the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ReceiptError(Error):
    code = ReceiptErrorCode(description="The error code.", required=True)
    warehouses = NonNullList(
        graphene.ID,
        description="List of warehouse IDs which cause the error.",
        required=False,
    )
    variants = NonNullList(
        graphene.ID,
        description="List of variant IDs which cause the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


# Input types
class PurchaseOrderItemInput(BaseInputObjectType):
    variant_id = graphene.ID(required=True, description="Product variant to order.")
    quantity_ordered = graphene.Int(
        required=True, description="Quantity to order from supplier."
    )
    unit_price_amount = PositiveDecimal(
        description="Unit cost (buy price). Optional for draft creation."
    )
    currency = graphene.String(
        description="Currency code (e.g., GBP, USD). Optional for draft creation."
    )
    country_of_origin = graphene.String(
        description="ISO 2-letter country code for customs/duties.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class PurchaseOrderCreateInput(BaseInputObjectType):
    source_warehouse_id = graphene.ID(
        required=True,
        description="Supplier warehouse (must be non-owned warehouse).",
    )
    destination_warehouse_id = graphene.ID(
        required=True,
        description="Destination warehouse (must be owned warehouse).",
    )
    channel_id = graphene.ID(
        required=False,
        description="Channel this purchase order is associated with.",
    )
    name = graphene.String(
        description="Optional name for the purchase order.",
    )
    items = NonNullList(
        PurchaseOrderItemInput,
        description="Line items to order. Can be empty for draft creation.",
    )
    auto_reallocate_variants = graphene.Boolean(
        description="Whether variants are automatically reallocated on receipt. Defaults to True.",
    )
    metadata = NonNullList(
        MetadataInput,
        description="Public metadata (e.g., supplier PO number).",
    )
    private_metadata = NonNullList(
        MetadataInput,
        description="Private metadata (e.g., invoice parsing data for future automation).",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class PurchaseOrderItemAdjustment(ModelObjectType[models.PurchaseOrderItemAdjustment]):
    id = graphene.GlobalID(required=True, description="The ID of the adjustment.")
    purchase_order_item = graphene.Field(
        PurchaseOrderItem,
        required=True,
        description="Purchase order item being adjusted.",
    )
    quantity_change = graphene.Int(
        required=True,
        description="Change in quantity (negative for losses, positive for gains).",
    )
    reason = PurchaseOrderItemAdjustmentReasonEnum(
        required=True,
        description="Reason for the adjustment.",
    )
    affects_payable = graphene.Boolean(
        required=True,
        description=(
            "Whether supplier credits us for this adjustment. "
            "True for invoice variance or delivery shortages. "
            "False for losses we absorb (shrinkage, damage)."
        ),
    )
    financial_impact = graphene.Field(
        Money,
        required=True,
        description=(
            "Financial impact of this adjustment. "
            "Negative for losses, positive for gains. "
            "Calculated as quantity_change × original_unit_price."
        ),
    )
    status = PurchaseOrderItemAdjustmentStatusEnum(
        required=True,
        description="Processing status: PENDING or PROCESSED.",
    )
    purchase_order_number = graphene.String(
        description="Purchase order reference number for context.",
    )
    notes = graphene.String(description="Additional notes about the adjustment.")
    processed_at = DateTime(
        description="When the adjustment was processed (null if pending)."
    )
    created_at = DateTime(
        required=True,
        description="When the adjustment was created.",
    )
    created_by = graphene.Field(
        "saleor.graphql.account.types.User",
        description="User who created the adjustment.",
    )

    class Meta:
        description = "Represents an inventory adjustment to a purchase order item."
        model = models.PurchaseOrderItemAdjustment
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_purchase_order_item(root, info: ResolveInfo):
        return root.purchase_order_item

    @staticmethod
    def resolve_financial_impact(root, info: ResolveInfo):
        from prices import Money

        poi = root.purchase_order_item
        return Money(root.financial_impact, poi.currency)

    @staticmethod
    def resolve_status(root, info: ResolveInfo):
        return "processed" if root.processed_at else "pending"

    @staticmethod
    def resolve_purchase_order_number(root, info: ResolveInfo):
        return str(root.purchase_order_item.order.id)


class PurchaseOrderItemAdjustmentCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        node = PurchaseOrderItemAdjustment


# Receipt types


class ReceiptStatusEnum(graphene.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReceiptLine(ModelObjectType[models.ReceiptLine]):
    purchase_order_item = graphene.Field(
        PurchaseOrderItem,
        description="The purchase order item being received.",
        required=True,
    )
    quantity_received = graphene.Int(
        description="Quantity received in this line.",
        required=True,
    )
    received_at = DateTime(
        description="When this item was scanned/received.",
        required=True,
    )
    received_by = graphene.Field(
        "saleor.graphql.account.types.User",
        description="Warehouse staff who scanned this item.",
    )
    notes = graphene.String(
        description="Notes about this specific receipt line.",
    )

    class Meta:
        description = "Represents a line item in a goods receipt."
        interfaces = [graphene.relay.Node]
        model = models.ReceiptLine
        doc_category = DOC_CATEGORY_PRODUCTS


class ReceiptLineCountableConnection(CountableConnection):
    class Meta:
        node = ReceiptLine


class Receipt(ModelObjectType[models.Receipt]):
    shipment = graphene.Field(
        "saleor.graphql.shipping.types.Shipment",
        description="The shipment being received.",
        required=True,
    )
    status = ReceiptStatusEnum(
        description="Current status of the receipt.",
        required=True,
    )
    lines = graphene.List(
        graphene.NonNull(ReceiptLine),
        description="Items received in this receipt.",
        required=True,
    )
    created_at = DateTime(
        description="When the receipt was started.",
        required=True,
    )
    completed_at = DateTime(
        description="When the receipt was completed.",
    )
    created_by = graphene.Field(
        "saleor.graphql.account.types.User",
        description="User who started the receipt.",
    )
    completed_by = graphene.Field(
        "saleor.graphql.account.types.User",
        description="User who completed the receipt.",
    )
    notes = graphene.String(
        description="Notes about this receipt.",
    )

    class Meta:
        description = "Represents a goods receipt for an inbound shipment."
        interfaces = [graphene.relay.Node]
        model = models.Receipt
        doc_category = DOC_CATEGORY_PRODUCTS

    @staticmethod
    def resolve_lines(root: models.Receipt, info: ResolveInfo):
        return root.lines.all()


class ReceiptCountableConnection(CountableConnection):
    class Meta:
        node = Receipt


# Product discrepancy types (for POIA resolution UI)


class VariantDiscrepancy(graphene.ObjectType):
    variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant",
        required=True,
        description="The product variant.",
    )
    quantity_ordered = graphene.Int(
        required=True, description="Quantity originally ordered."
    )
    quantity_received = graphene.Int(
        required=True, description="Quantity actually received."
    )
    delta = graphene.Int(
        required=True,
        description="Difference (received - ordered). Negative means shortage.",
    )

    @staticmethod
    def resolve_variant(root, info):
        from ..core.context import ChannelContext

        return ChannelContext(node=root["variant"], channel_slug=None)


class OrderAllocationInfo(graphene.ObjectType):
    variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant",
        required=True,
        description="Product variant allocated.",
    )
    quantity = graphene.Int(required=True, description="Quantity allocated.")

    @staticmethod
    def resolve_variant(root, info):
        from ..core.context import ChannelContext

        return ChannelContext(node=root["variant"], channel_slug=None)


class AffectedOrderInfo(graphene.ObjectType):
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        required=True,
        description="The affected order.",
    )
    allocations = graphene.List(
        graphene.NonNull(OrderAllocationInfo),
        required=True,
        description="Current allocations for this order.",
    )

    @staticmethod
    def resolve_order(root, info):
        from ..core.context import SyncWebhookControlContext

        return SyncWebhookControlContext(node=root["order"], allow_sync_webhooks=False)


class ProductDiscrepancy(graphene.ObjectType):
    product = graphene.Field(
        "saleor.graphql.product.types.Product",
        required=True,
        description="The product with discrepancies.",
    )

    @staticmethod
    def resolve_product(root, info):
        from ..core.context import ChannelContext

        return ChannelContext(node=root["product"], channel_slug=None)

    variants = graphene.List(
        graphene.NonNull(VariantDiscrepancy),
        required=True,
        description="Per-variant breakdown of ordered vs received.",
    )
    affected_orders = graphene.List(
        graphene.NonNull(AffectedOrderInfo),
        required=True,
        description="Orders currently allocated from these POIs.",
    )
    total_shortage = graphene.Int(
        required=True,
        description="Total units short across all variants (absolute value).",
    )

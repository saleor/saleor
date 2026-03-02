"""Stock management utilities for purchase orders and inventory tracking."""

from django.db import transaction
from django.utils import timezone

from ..core.exceptions import InsufficientStock, InsufficientStockData
from ..warehouse.models import Allocation, AllocationSource, Stock
from . import PurchaseOrderItemStatus
from .events import (
    adjustment_processed_event,
    purchase_order_item_confirmed_event,
)
from .exceptions import (
    AdjustmentAffectsFulfilledOrders,
    AdjustmentAffectsPaidOrders,
    AdjustmentAlreadyProcessed,
    InvalidPurchaseOrderItemStatus,
)
from .models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderItemAdjustment,
    PurchaseOrderRequestedAllocation,
)


@transaction.atomic
def add_allocation_to_draft_purchase_order_item(
    a: Allocation, poi: PurchaseOrderItem
) -> PurchaseOrderRequestedAllocation:
    """Link an allocation to a draft PO as a requested allocation (PORA).

    Records intent to fulfill this allocation when the PO is confirmed. On confirmation,
    PORAs are consumed FIFO by order line creation time to create AllocationSources.
    """
    from ..order import OrderStatus
    from . import PurchaseOrderStatus

    po = poi.order

    if po.status != PurchaseOrderStatus.DRAFT:
        raise InvalidPurchaseOrderItemStatus(poi, PurchaseOrderStatus.DRAFT)
    if a.stock.warehouse_id != po.source_warehouse_id:
        raise ValueError(
            f"Allocation stock warehouse {a.stock.warehouse_id} does not match "
            f"PO source warehouse {po.source_warehouse_id}"
        )
    if a.stock.product_variant_id != poi.product_variant_id:
        raise ValueError(
            f"Allocation variant {a.stock.product_variant_id} does not match "
            f"POI variant {poi.product_variant_id}"
        )
    if a.order_line.order.status != OrderStatus.UNCONFIRMED:
        raise ValueError(
            f"Order {a.order_line.order.pk} must be UNCONFIRMED, "
            f"got {a.order_line.order.status}"
        )
    if PurchaseOrderRequestedAllocation.objects.filter(
        purchase_order=po, allocation=a
    ).exists():
        raise ValueError(f"Allocation {a.pk} is already a PORA on PO {po.pk}")

    if PurchaseOrderRequestedAllocation.objects.filter(allocation=a).exists():
        import warnings

        warnings.warn(
            f"Allocation {a.pk} is already requested by another purchase order.",
            stacklevel=2,
        )

    return PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=po,
        allocation=a,
    )


@transaction.atomic
def add_order_to_purchase_order(
    order, po: PurchaseOrder
) -> list[PurchaseOrderRequestedAllocation]:
    """Add all allocations from an order to a draft PO as PORAs where PO.source_warehouse = allocations warehouse, creating POIs where necessary."""
    from ..order import OrderStatus
    from . import PurchaseOrderStatus

    if po.status != PurchaseOrderStatus.DRAFT:
        raise ValueError(f"PurchaseOrder {po.pk} must be DRAFT, got {po.status}")
    if order.status != OrderStatus.UNCONFIRMED:
        raise ValueError(f"Order {order.pk} must be UNCONFIRMED, got {order.status}")

    allocations = list(
        Allocation.objects.filter(
            order_line__order=order,
            stock__warehouse=po.source_warehouse,
        ).select_related("order_line", "stock")
    )

    if not allocations:
        raise ValueError(
            f"Order {order.pk} has no allocations at warehouse {po.source_warehouse_id}"
        )

    poras = []
    for allocation in allocations:
        poi = PurchaseOrderItem.objects.filter(
            order=po,
            product_variant=allocation.stock.product_variant,
        ).first()
        if poi is None:
            poi = PurchaseOrderItem.objects.create(
                order=po,
                product_variant=allocation.stock.product_variant,
                quantity_ordered=0,
                status=PurchaseOrderItemStatus.DRAFT,
            )
        poi.quantity_ordered += allocation.quantity_allocated
        poi.save(update_fields=["quantity_ordered"])
        poras.append(add_allocation_to_draft_purchase_order_item(allocation, poi))

    return poras


@transaction.atomic
def remove_order_from_purchase_order(order, po: PurchaseOrder) -> None:
    """Remove an order's linkage from a draft PO, reversing add_order_to_purchase_order."""
    from . import PurchaseOrderStatus

    if po.status != PurchaseOrderStatus.DRAFT:
        raise ValueError(f"PO {po.pk} must be DRAFT, got {po.status}")

    poras = PurchaseOrderRequestedAllocation.objects.filter(
        purchase_order=po,
        allocation__order_line__order=order,
    ).select_related("allocation__stock")

    for pora in poras:
        qty = pora.allocation.quantity_allocated
        poi = PurchaseOrderItem.objects.filter(
            order=po,
            product_variant_id=pora.allocation.stock.product_variant_id,
        ).first()
        if poi:
            poi.quantity_ordered = max(0, poi.quantity_ordered - qty)
            if poi.quantity_ordered == 0:
                poi.delete()
            else:
                poi.save(update_fields=["quantity_ordered"])

    poras.delete()


@transaction.atomic
def confirm_purchase_order_item(poi: PurchaseOrderItem, user=None, app=None):
    """Confirm purchase order item and move stock from supplier to owned warehouse.

    This is THE ONLY WAY stock enters owned warehouses. When a POI is confirmed,
    we move stock from the supplier (non-owned) warehouse to our owned warehouse.

    The function:
    1. Moves physical stock from source to destination
    2. Moves existing order allocations via FIFO on PORAs on the POI.
    3. Creates AllocationSources to link allocations to this POI (batch tracking)
    4. The rest becomes unallocated stock.
    5. Logs the confirmation event for audit trail

    See `saleor/warehouse/tests/test_stock_invariants.py` for description of how Stock
    conservation works
    """

    from ..warehouse.management import _allocate_sources_incremental

    if poi.status != PurchaseOrderItemStatus.DRAFT:
        raise InvalidPurchaseOrderItemStatus(poi, PurchaseOrderItemStatus.DRAFT)

    if not (poi.currency and poi.total_price_amount is not None):
        raise ValueError(
            f"POI {poi.pk} must have currency and total_price_amount set before confirmation"
        )

    # Get source and destination (locked via select_for_update)
    source = (
        Stock.objects.select_for_update()
        .select_related("warehouse")
        .get(
            warehouse=poi.order.source_warehouse,
            product_variant=poi.product_variant,
        )
    )

    destination, created = (
        Stock.objects.select_for_update()
        .select_related("warehouse")
        .get_or_create(
            warehouse=poi.order.destination_warehouse,
            product_variant=poi.product_variant,
            defaults={"quantity": 0, "quantity_allocated": 0},
        )
    )

    if poi.quantity_allocated != 0:
        raise ValueError(
            f"POI {poi.pk} has quantity_allocated={poi.quantity_allocated}, expected 0"
        )
    if poi.quantity_fulfilled != 0:
        raise ValueError(
            f"POI {poi.pk} has quantity_fulfilled={poi.quantity_fulfilled}, expected 0"
        )

    quantity = poi.quantity_ordered

    if source.warehouse.is_owned:
        raise ValueError(f"Source warehouse {source.warehouse.pk} must not be owned")
    if not destination.warehouse.is_owned:
        raise ValueError(
            f"Destination warehouse {destination.warehouse.pk} must be owned"
        )
    if quantity > source.quantity + source.quantity_allocated:
        raise ValueError(
            f"Insufficient stock at source: need {quantity}, "
            f"have {source.quantity + source.quantity_allocated} "
            f"(quantity={source.quantity}, allocated={source.quantity_allocated})"
        )

    poras = (
        PurchaseOrderRequestedAllocation.objects.select_for_update()
        .select_related("allocation__order_line__order", "allocation__stock")
        .filter(
            purchase_order=poi.order,
            allocation__stock__product_variant=poi.product_variant,
        )
        .order_by("allocation__order_line__created_at")
    )

    from ..order import OrderStatus
    from ..warehouse.management import can_confirm_order

    orders_to_check = set()

    # Move physical stock from source to destination
    # Note: Stock locks ensure these moves are isolated
    # Physical stock moves based on POI quantity; allocation tracking happens in loop below
    if quantity <= source.quantity:
        # Sufficient unallocated stock
        source.quantity -= quantity
    else:
        # Taking more than unallocated - remainder comes from allocated pool
        # Don't update quantity_allocated here; that happens when allocations move in loop
        source.quantity = 0

    destination.quantity += quantity

    # Confirm POI status before moving allocations
    # allocate_sources() needs POI to be CONFIRMED to find it
    poi.status = PurchaseOrderItemStatus.CONFIRMED
    poi.confirmed_at = timezone.now()
    poi.save(update_fields=["status", "confirmed_at"])

    # Move PORA-scoped allocations from source to destination and create AllocationSources.
    # Delete each PORA after its allocation is processed - they are consumed on confirmation.
    for pora in poras:
        allocation = pora.allocation
        available = destination.quantity - destination.quantity_allocated
        if available >= allocation.quantity_allocated:
            # Move entire allocation to owned warehouse
            allocation.stock = destination
            allocation.save(update_fields=["stock"])

            try:
                _allocate_sources_incremental(
                    allocation, allocation.quantity_allocated, poi=poi
                )
            except InsufficientStock:
                raise

            destination.quantity_allocated += allocation.quantity_allocated
            source.quantity_allocated -= allocation.quantity_allocated
            orders_to_check.add(allocation.order_line.order)
        else:
            # POI exhausted - split: move what fits, rest stays at source
            move_quantity = available

            moved_allocation = Allocation.objects.create(
                order_line=allocation.order_line,
                stock=destination,
                quantity_allocated=move_quantity,
            )

            try:
                _allocate_sources_incremental(moved_allocation, move_quantity, poi=poi)
            except InsufficientStock:
                raise

            destination.quantity_allocated += move_quantity
            source.quantity_allocated -= move_quantity

            allocation.quantity_allocated -= move_quantity
            if allocation.quantity_allocated == 0:
                allocation.delete()
            else:
                allocation.save(update_fields=["quantity_allocated"])

            orders_to_check.add(allocation.order_line.order)

        pora.delete()

    source.save(update_fields=["quantity", "quantity_allocated"])
    destination.save(update_fields=["quantity", "quantity_allocated"])

    # Auto-confirm orders that now have all allocations with sources
    for order in orders_to_check:
        if can_confirm_order(order):
            order.status = OrderStatus.UNFULFILLED
            order.save(update_fields=["status", "updated_at"])

            from ..order.actions import order_confirmed
            from ..plugins.manager import get_plugins_manager

            confirm_manager = get_plugins_manager(allow_replica=False)

            # Send order confirmed email
            # Use lambda with default args to capture loop variables by value
            transaction.on_commit(
                lambda o=order, u=user, a=app, m=confirm_manager: order_confirmed(  # type: ignore[misc]
                    o, u, a, m, send_confirmation_email=True
                )
            )

    # Log event for audit trail
    purchase_order_item_confirmed_event(
        purchase_order_item=poi,
        user=user,
        app=app,
    )

    return source


# TODO: this needs work on refunding orders
@transaction.atomic
def process_adjustment(
    adjustment: PurchaseOrderItemAdjustment,
    user=None,
    app=None,
    manager=None,
):
    """Process a PurchaseOrderItemAdjustment and update stock.

    Handles inventory discrepancies by adjusting stock and POI quantities.
    For negative adjustments, deallocates from unpaid orders if stock is allocated.

    Args:
        adjustment: PurchaseOrderItemAdjustment instance to process
        user: User processing the adjustment (optional)
        app: App processing the adjustment (optional)
        manager: PluginsManager for webhooks (optional)

    For positive adjustments (gains):
        - Increases stock.quantity
        - Increases POI.quantity_received
        - Makes stock available for new allocations

    For negative adjustments (losses):
        - Decreases stock.quantity
        - Decreases POI.quantity_received
        - Deallocates from affected unpaid orders
        - Unconfirms orders that lose all their sources

    Raises:
        AdjustmentAlreadyProcessed: If adjustment already processed
        AdjustmentAffectsFulfilledOrders: If affects UNFULFILLED orders (locked, not editable)
        AdjustmentAffectsPaidOrders: If negative adjustment affects fully paid orders
        InsufficientStock: If loss exceeds total physical stock in warehouse

    UNFULFILLED orders require manual resolution (cannot be edited via standard flow) -
    we will kick this back for now

    """
    from ..order import OrderStatus
    from ..warehouse.management import can_confirm_order, deallocate_sources

    if adjustment.processed_at is not None:
        raise AdjustmentAlreadyProcessed(adjustment)

    poi = adjustment.purchase_order_item
    quantity_change = adjustment.quantity_change

    # Get stock with lock
    stock = Stock.objects.select_for_update().get(
        warehouse=poi.order.destination_warehouse,
        product_variant=poi.product_variant,
    )

    # Handle positive adjustment (gain)
    if quantity_change > 0:
        stock.quantity += quantity_change
        stock.save(update_fields=["quantity"])

        # Note: quantity_received is not modified - it represents what was physically received
        # Adjustments affect available_quantity which includes processed adjustments

    # Handle negative adjustment (loss)
    elif quantity_change < 0:
        loss = abs(quantity_change)

        # stock.quantity is live stock so if we don't have enough live stock how the
        # hell did we lose more than we ever had?
        if stock.quantity < loss:
            raise InsufficientStock(
                [
                    InsufficientStockData(
                        available_quantity=stock.quantity,
                        variant=stock.product_variant,
                        warehouse_pk=stock.warehouse.pk,
                    )
                ]
            )

        # Find allocations sourced from this POI batch
        affected_sources = (
            AllocationSource.objects.select_for_update()
            .select_related("allocation__order_line__order")
            .filter(purchase_order_item=poi)
        )

        # Check order statuses and payment
        unfulfilled_orders_affected = []
        paid_orders_affected = []
        unconfirmed_sources = []

        for source in affected_sources:
            order = source.allocation.order_line.order

            # Check if UNFULFILLED (locked, can't edit)
            if order.status == OrderStatus.UNFULFILLED:
                unfulfilled_orders_affected.append(order.number)

            # Check if fully paid
            elif order.is_fully_paid():
                paid_orders_affected.append(order.number)

            # UNCONFIRMED and not fully paid - we can handle this
            else:
                unconfirmed_sources.append(source)

        # Reject if UNFULFILLED orders are affected
        # These are locked and cannot be edited automatically
        if unfulfilled_orders_affected:
            raise AdjustmentAffectsFulfilledOrders(
                adjustment, unfulfilled_orders_affected
            )

        # Reject if fully paid orders are affected
        # TODO: Implement refund workflow
        if paid_orders_affected:
            raise AdjustmentAffectsPaidOrders(adjustment, paid_orders_affected)

        # Deallocate from UNCONFIRMED, unpaid orders
        # Track remaining loss to distribute across affected allocations
        remaining_loss = loss
        orders_to_check = set()
        for source in unconfirmed_sources:
            if remaining_loss <= 0:
                break

            allocation = source.allocation
            order = allocation.order_line.order
            quantity_to_deallocate = min(source.quantity, remaining_loss)

            # Deallocate sources (removes AllocationSource, restores POI.quantity_allocated)
            deallocate_sources(allocation, quantity_to_deallocate)

            # Track unconfirmed orders for status check
            if order.status == OrderStatus.UNCONFIRMED:
                orders_to_check.add(order)

            # Reduce allocation quantity
            allocation.quantity_allocated -= quantity_to_deallocate
            if allocation.quantity_allocated == 0:
                allocation.delete()
            else:
                allocation.save(update_fields=["quantity_allocated"])

            # Update stock quantity_allocated
            stock.quantity_allocated -= quantity_to_deallocate

            # Track remaining loss to distribute
            remaining_loss -= quantity_to_deallocate

        # Decrease physical stock
        stock.quantity -= loss
        stock.save(update_fields=["quantity", "quantity_allocated"])

        # Note: quantity_received is not modified - it represents what was physically received
        # The adjustment is tracked separately and affects available_quantity

        # Transition UNCONFIRMED orders back to DRAFT if they lost all their sources
        # UNCONFIRMED is a transient state waiting for all allocations to have sources
        # If stock adjustment removes sources, order must go back to DRAFT
        for order in orders_to_check:
            if not can_confirm_order(order):
                order.status = OrderStatus.DRAFT
                order.save(update_fields=["status", "updated_at"])

    # Mark adjustment as processed
    adjustment.processed_at = timezone.now()
    adjustment.save(update_fields=["processed_at"])

    # Log event for audit trail
    adjustment_processed_event(
        adjustment=adjustment,
        user=user,
        app=app,
    )

    return adjustment

"""Receipt workflow: receiving, reallocation, and POIA resolution."""

import logging
from collections import defaultdict

from django.db import transaction
from django.utils import timezone

from saleor.order.models import Order, OrderLine
from saleor.product.models import ProductVariant

from ..warehouse.models import Allocation, AllocationSource, Stock, Warehouse
from . import PurchaseOrderItemStatus
from .events import adjustment_created_event, adjustment_processed_event
from .exceptions import (
    CannotReallocateVariants,
    ReceiptLineNotInProgress,
    ReceiptNotInProgress,
)
from .models import (
    PurchaseOrderItem,
    PurchaseOrderItemAdjustment,
    ReceiptLine,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def start_receipt(shipment, user=None):
    """Create a new Receipt for receiving an inbound shipment.

    Args:
        shipment: Shipment being received
        user: User starting the receipt (warehouse staff)

    Returns:
        Receipt instance

    Raises:
        ValueError: If shipment already has a receipt or is already received

    """
    from ..shipping import ShipmentType
    from .models import Receipt

    if shipment.shipment_type != ShipmentType.INBOUND:
        raise ValueError(
            f"Cannot start receipt for {shipment.shipment_type} shipment. "
            "Only inbound shipments can be received."
        )

    if shipment.arrived_at is not None:
        raise ValueError(f"Shipment {shipment.id} already marked as received")

    if hasattr(shipment, "receipt"):
        existing = shipment.receipt
        if existing.status == "in_progress":
            return existing
        raise ValueError(f"Shipment {shipment.id} already has a receipt")

    receipt = Receipt.objects.create(
        shipment=shipment,
        created_by=user,
    )

    return receipt


@transaction.atomic
def receive_item(receipt, product_variant, quantity, user=None, notes=""):
    from . import ReceiptStatus
    from .models import ReceiptLine

    if receipt.status != ReceiptStatus.IN_PROGRESS:
        raise ReceiptNotInProgress(receipt)

    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")

    pois = list(
        PurchaseOrderItem.objects.filter(
            shipment=receipt.shipment,
            product_variant=product_variant,
        )
        .prefetch_related("receipt_lines")
        .order_by("pk")
    )
    if not pois:
        raise ValueError(
            f"Product variant {product_variant.sku} not found in "
            f"shipment {receipt.shipment.id}"
        )

    # FIFO: fill POIs in order, picking the first with remaining capacity
    poi = pois[0]
    for candidate in pois:
        if candidate.quantity_received < candidate.quantity_ordered:
            poi = candidate
            break

    receipt_line = ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi,
        quantity_received=quantity,
        received_by=user,
        notes=notes,
    )

    return receipt_line


@transaction.atomic
def update_receipt_lines(receipt, lines_data, user=None):
    """Upsert receipt lines by purchase order item.

    Each entry in lines_data is a dict with:
      - purchase_order_item_id: ID of the PurchaseOrderItem
      - quantity: absolute quantity received (0 = delete the line)

    Creates, updates, or deletes ReceiptLines as needed.
    """
    from . import ReceiptStatus

    if receipt.status != ReceiptStatus.IN_PROGRESS:
        raise ReceiptNotInProgress(receipt)

    for line_data in lines_data:
        poi_id = line_data["purchase_order_item_id"]
        quantity = line_data["quantity"]

        existing = ReceiptLine.objects.filter(
            receipt=receipt,
            purchase_order_item_id=poi_id,
        ).first()

        if quantity <= 0:
            if existing:
                existing.delete()
        elif existing:
            existing.quantity_received = quantity
            existing.received_by = user
            existing.save(update_fields=["quantity_received", "received_by"])
        else:
            ReceiptLine.objects.create(
                receipt=receipt,
                purchase_order_item_id=poi_id,
                quantity_received=quantity,
                received_by=user,
            )

    return receipt


def _remove_allocation_source(
    ass: AllocationSource,
    *,
    allocation: "Allocation | None" = None,
    stock: Stock | None = None,
    poi: "PurchaseOrderItem | None" = None,
) -> None:
    """Delete an AllocationSource and update all dependent quantities.

    Updates: AllocationSource (deleted), Allocation (deleted if qty hits 0),
    Stock.quantity_allocated, POI.quantity_allocated.

    OrderLine quantities are NOT touched here — callers that need OrderLine
    sync should use the net-change approach after all removes/adds are done.

    Pass pre-locked ``allocation``, ``stock``, and ``poi`` when calling inside
    a batch that touches multiple AllocationSources sharing the same row.
    Without this, FK cache objects are stale and concurrent saves overwrite
    each other's decrements.
    """
    qty = ass.quantity
    allocation = allocation or ass.allocation
    stock = stock or allocation.stock
    poi = poi or ass.purchase_order_item

    logger.debug(
        "remove_alloc_source: AS %s qty=%d | alloc %s (%d -> %d) | "
        "stock %s variant=%s (%d -> %d) | poi %s (%d -> %d)",
        ass.pk,
        qty,
        allocation.pk,
        allocation.quantity_allocated,
        allocation.quantity_allocated - qty,
        stock.pk,
        stock.product_variant_id,
        stock.quantity_allocated,
        stock.quantity_allocated - qty,
        poi.pk,
        poi.quantity_allocated,
        poi.quantity_allocated - qty,
    )

    ass.delete()

    allocation.quantity_allocated -= qty
    if allocation.quantity_allocated == 0:
        logger.debug("remove_alloc_source: deleting empty allocation %s", allocation.pk)
        allocation.delete()
    else:
        allocation.save(update_fields=["quantity_allocated"])

    stock.quantity_allocated -= qty
    stock.save(update_fields=["quantity_allocated"])

    poi.quantity_allocated -= qty
    poi.save(update_fields=["quantity_allocated"])


def _add_allocation_source(
    poi: PurchaseOrderItem,
    order_line: "OrderLine",
    stock: Stock,
    quantity: int,
) -> AllocationSource:
    """Create an AllocationSource and update all dependent quantities.

    Updates: Allocation (created or incremented), Stock.quantity_allocated,
    POI.quantity_allocated, AllocationSource (created).

    OrderLine quantities are NOT touched here — callers that need OrderLine
    sync should use the net-change approach after all removes/adds are done.
    """
    allocation, created = Allocation.objects.get_or_create(
        order_line=order_line,
        stock=stock,
        defaults={"quantity_allocated": 0},
    )

    logger.debug(
        "add_alloc_source: poi %s order_line %s (order %s) variant=%s qty=%d | "
        "alloc %s %s (%d -> %d) | stock %s (%d -> %d) | poi (%d -> %d)",
        poi.pk,
        order_line.pk,
        order_line.order_id,
        stock.product_variant_id,
        quantity,
        allocation.pk,
        "NEW" if created else "EXISTING",
        allocation.quantity_allocated,
        allocation.quantity_allocated + quantity,
        stock.pk,
        stock.quantity_allocated,
        stock.quantity_allocated + quantity,
        poi.quantity_allocated,
        poi.quantity_allocated + quantity,
    )

    allocation.quantity_allocated += quantity
    allocation.save(update_fields=["quantity_allocated"])

    stock.quantity_allocated += quantity
    stock.save(update_fields=["quantity_allocated"])

    poi.quantity_allocated += quantity
    poi.save(update_fields=["quantity_allocated"])

    ass = AllocationSource.objects.create(
        purchase_order_item=poi,
        allocation=allocation,
        quantity=quantity,
    )
    logger.debug("add_alloc_source: created AS %s", ass.pk)
    return ass


def _apply_reallocation(
    removals: list[AllocationSource],
    distribution: dict[tuple, int],
    poi_by_variant: dict[ProductVariant, list[PurchaseOrderItem]],
    received_by_poi: dict[PurchaseOrderItem, int],
    warehouse: Warehouse,
):
    """Atomically tear down old AllocationSources and rebuild from a new distribution.

    This is the shared primitive for both automated variant reallocation and
    manual POIA substitute resolution. The caller computes what the new
    distribution should be; this function applies it.

    Args:
        removals: AllocationSources to delete (the "old world").
        distribution: {(order, variant): qty} — the desired end state.
        poi_by_variant: {variant: [POIs]} for linking new AllocationSources.
        received_by_poi: {POI: qty} weights for splitting across multiple POIs
            per variant (Hamilton). For manual resolution with a single POI
            per variant, pass {poi: 1} or similar.
        warehouse: The owned warehouse where stock lives.

    """
    from ..core.utils.apportionment import hamilton
    from ..order.models import Order

    if not removals and not distribution:
        logger.debug(
            "apply_reallocation: nothing to do (empty removals + distribution)"
        )
        return

    logger.debug(
        "apply_reallocation: warehouse=%s removals=%d distribution_entries=%d",
        warehouse.pk,
        len(removals),
        len(distribution),
    )
    for a in removals:
        logger.debug(
            "  removal: AS %s qty=%d order=%s variant=%s (poi %s)",
            a.pk,
            a.quantity,
            a.allocation.order_line.order_id,
            a.purchase_order_item.product_variant_id,
            a.purchase_order_item_id,
        )
    for (order, variant), qty in distribution.items():
        logger.debug(
            "  target:  order=%s variant=%s (pk=%s) qty=%d",
            order.pk,
            variant.sku,
            variant.pk,
            qty,
        )

    # --- Acquire row-level locks on all rows we'll modify ---
    # Without these locks, concurrent transactions can read stale
    # quantity_allocated values and overwrite each other's decrements.
    # Additionally, when AllocationSources are loaded with select_related,
    # multiple removals sharing the same Stock/POI get separate Python
    # objects with stale caches — the locked maps below are the single
    # source of truth.

    variant_ids = set()
    order_ids = set()
    poi_ids = set()
    alloc_ids = set()

    for a in removals:
        variant_ids.add(a.purchase_order_item.product_variant_id)
        order_ids.add(a.allocation.order_line.order_id)
        poi_ids.add(a.purchase_order_item_id)
        alloc_ids.add(a.allocation_id)
    for order, variant in distribution:
        variant_ids.add(variant.pk)
        order_ids.add(order.pk)
    for pois in poi_by_variant.values():
        for p in pois:
            poi_ids.add(p.pk)

    # Lock Stock rows
    stock_map = {
        s.product_variant_id: s
        for s in Stock.objects.select_for_update().filter(
            warehouse=warehouse,
            product_variant_id__in=variant_ids,
        )
    }
    # Create Stock for new variants (substitution targets)
    for _order, variant in distribution:
        if variant.pk not in stock_map:
            stock_map[variant.pk], _ = Stock.objects.get_or_create(
                warehouse=warehouse,
                product_variant=variant,
                defaults={"quantity": 0, "quantity_allocated": 0},
            )

    # Lock Orders whose OrderLines we'll modify
    if order_ids:
        list(Order.objects.select_for_update().filter(pk__in=order_ids))

    # Lock Allocations — multiple ASes can share the same Allocation row
    # and their FK cache objects hold stale quantity_allocated values
    alloc_map = {
        a.pk: a for a in Allocation.objects.select_for_update().filter(pk__in=alloc_ids)
    }

    # Lock POIs — fresh instances avoid stale FK cache from select_related
    poi_map = {
        p.pk: p
        for p in PurchaseOrderItem.objects.select_for_update().filter(pk__in=poi_ids)
    }

    # Replace POI references with locked versions
    locked_poi_by_variant = {}
    for variant, pois in poi_by_variant.items():
        locked_poi_by_variant[variant] = [poi_map.get(p.pk, p) for p in pois]

    locked_received_by_poi = {}
    for poi, qty in received_by_poi.items():
        locked_received_by_poi[poi_map.get(poi.pk, poi)] = qty

    # Derive current state from removals so callers don't have to pass it
    order_line_by_order_variant: dict[tuple, OrderLine] = {}
    price_template: dict = {}
    for a in removals:
        order = a.allocation.order_line.order
        variant = a.purchase_order_item.product_variant
        order_line_by_order_variant[(order, variant)] = a.allocation.order_line
        price_template[order] = a.allocation.order_line

    # --- delete old world ---
    logger.debug(
        "apply_reallocation: tearing down %d allocation sources", len(removals)
    )
    for a in removals:
        _remove_allocation_source(
            a,
            allocation=alloc_map.get(a.allocation_id),
            stock=stock_map.get(a.purchase_order_item.product_variant_id),
            poi=poi_map.get(a.purchase_order_item_id),
        )

    for (order, variant), line in order_line_by_order_variant.items():
        new_qty = distribution.get((order, variant), 0)
        if new_qty == 0:
            logger.debug(
                "apply_reallocation: deleting order_line %s (order %s, variant %s)",
                line.pk,
                order.pk,
                variant.sku,
            )
            line.delete()
        else:
            logger.debug(
                "apply_reallocation: updating order_line %s qty %d -> %d "
                "(order %s, variant %s)",
                line.pk,
                line.quantity,
                new_qty,
                order.pk,
                variant.sku,
            )
            line.quantity = new_qty
            line.total_price_net_amount = line.unit_price_net_amount * new_qty
            line.total_price_gross_amount = line.unit_price_gross_amount * new_qty
            line.save(
                update_fields=[
                    "quantity",
                    "total_price_net_amount",
                    "total_price_gross_amount",
                ]
            )

    # --- rebuild new world from distribution ---
    logger.debug(
        "apply_reallocation: rebuilding %d distribution entries", len(distribution)
    )
    order_line_map: dict[tuple, OrderLine] = {}
    for (order, variant), line in order_line_by_order_variant.items():
        if distribution.get((order, variant), 0) > 0:
            order_line_map[(order, variant)] = line

    for (order, variant), qty in distribution.items():
        if (order, variant) not in order_line_map:
            template = price_template[order]
            order_line_map[(order, variant)] = OrderLine.objects.create(
                order=order,
                variant=variant,
                product_name=variant.product.name,
                variant_name=variant.name or "",
                product_sku=variant.sku,
                product_variant_id=str(variant.pk),
                quantity=qty,
                unit_price_net_amount=template.unit_price_net_amount,
                unit_price_gross_amount=template.unit_price_gross_amount,
                total_price_net_amount=template.unit_price_net_amount * qty,
                total_price_gross_amount=template.unit_price_gross_amount * qty,
                undiscounted_unit_price_net_amount=template.undiscounted_unit_price_net_amount,
                undiscounted_unit_price_gross_amount=template.undiscounted_unit_price_gross_amount,
                base_unit_price_amount=template.base_unit_price_amount,
                currency=template.currency,
                is_shipping_required=template.is_shipping_required,
                is_gift_card=template.is_gift_card,
            )

    for (order, variant), qty in distribution.items():
        order_line = order_line_map[(order, variant)]
        stock = stock_map[variant.pk]
        pois = locked_poi_by_variant[variant]
        if len(pois) == 1:
            _add_allocation_source(pois[0], order_line, stock, qty)
        else:
            poi_weights = {poi: locked_received_by_poi[poi] for poi in pois}
            poi_dist = hamilton(poi_weights, qty)
            for poi, poi_qty in poi_dist.items():
                if poi_qty > 0:
                    _add_allocation_source(poi, order_line, stock, poi_qty)

    # --- adjust Stock.quantity to reflect actual received quantities ---
    # When variants are swapped (e.g. ordered 6×S+4×M, received 4×S+6×M),
    # the physical stock must move with the allocation.
    old_qty_by_variant: dict[int, int] = defaultdict(int)
    for a in removals:
        old_qty_by_variant[a.purchase_order_item.product_variant_id] += a.quantity

    new_qty_by_variant: dict[int, int] = defaultdict(int)
    for (_order, variant), qty in distribution.items():
        new_qty_by_variant[variant.pk] += qty

    all_variant_ids = set(old_qty_by_variant) | set(new_qty_by_variant)
    for variant_id in all_variant_ids:
        delta = new_qty_by_variant.get(variant_id, 0) - old_qty_by_variant.get(
            variant_id, 0
        )
        if delta != 0:
            stock = stock_map[variant_id]
            logger.debug(
                "apply_reallocation: adjusting stock %s variant=%s quantity %d -> %d "
                "(delta=%+d)",
                stock.pk,
                variant_id,
                stock.quantity,
                stock.quantity + delta,
                delta,
            )
            stock.quantity += delta
            stock.save(update_fields=["quantity"])


@transaction.atomic
def _variant_reallocate(
    rs: list[ReceiptLine],
    ass: list[AllocationSource],
) -> bool:
    """Reallocate variants of some product across unfulfilled order lines using Hamilton's method.

    Computes a new distribution and delegates to _apply_reallocation.

    Returns True if reallocation was performed, False if skipped (no-op).

    Raises:
        CannotReallocateVariants: if received < order entitlement at product level

    """
    from ..core.utils.apportionment import hamilton

    if not ass:
        logger.debug("variant_reallocate: no allocation sources, nothing to do")
        return False

    logger.debug(
        "variant_reallocate: %d receipt lines, %d allocation sources",
        len(rs),
        len(ass),
    )

    received: dict[ProductVariant, int] = {}
    received_by_poi: dict[PurchaseOrderItem, int] = {}
    poi_by_variant: dict[ProductVariant, list[PurchaseOrderItem]] = defaultdict(list)
    product = None
    for rl in rs:
        v = rl.purchase_order_item.product_variant
        poi = rl.purchase_order_item
        product = product or v.product
        if product != v.product:
            raise ValueError(
                f"All receipt lines must belong to the same product, "
                f"got {product.pk} and {v.product.pk}"
            )

        received[v] = received.get(v, 0) + rl.quantity_received
        received_by_poi[poi] = received_by_poi.get(poi, 0) + rl.quantity_received
        if poi not in poi_by_variant[v]:
            poi_by_variant[v].append(poi)

    expected: dict[ProductVariant, int] = {}
    for a in ass:
        v = a.purchase_order_item.product_variant
        expected[v] = expected.get(v, 0) + a.quantity

    all_variants = set(received) | set(expected)
    mismatched = {v for v in all_variants if received.get(v, 0) != expected.get(v, 0)}

    logger.debug(
        "variant_reallocate: product=%s received=%s expected=%s mismatched=%s",
        product,
        {v.sku: q for v, q in received.items()},
        {v.sku: q for v, q in expected.items()},
        {v.sku for v in mismatched},
    )

    if not mismatched:
        logger.debug("variant_reallocate: no mismatches, nothing to do")
        return False

    mismatched_ass = [
        a for a in ass if a.purchase_order_item.product_variant in mismatched
    ]

    order_entitlement: dict[Order, int] = {}
    for a in mismatched_ass:
        order = a.allocation.order_line.order
        order_entitlement[order] = order_entitlement.get(order, 0) + a.quantity

    logger.debug(
        "variant_reallocate: order_entitlement=%s",
        {o.pk: q for o, q in order_entitlement.items()},
    )

    total_received_mismatched = sum(received.get(v, 0) for v in mismatched)
    total_order_entitlement = sum(order_entitlement.values())

    logger.debug(
        "variant_reallocate: total_received_mismatched=%d total_order_entitlement=%d",
        total_received_mismatched,
        total_order_entitlement,
    )

    if total_order_entitlement > total_received_mismatched:
        raise CannotReallocateVariants(
            f"Cannot reallocate: received {total_received_mismatched} of "
            f"Product {product} but orders require {total_order_entitlement}",
        )

    # --- compute new distribution ---
    remaining_quota = dict(order_entitlement)
    distribution: dict[tuple, int] = {}
    for variant in sorted(mismatched, key=lambda v: v.pk):
        recv_qty = received.get(variant, 0)
        if recv_qty == 0:
            logger.debug("variant_reallocate: skipping %s (0 received)", variant.sku)
            continue
        eligible = {o: q for o, q in remaining_quota.items() if q > 0}
        allocatable = min(recv_qty, sum(eligible.values()))
        variant_alloc = hamilton(eligible, allocatable)
        logger.debug(
            "variant_reallocate: variant %s recv=%d allocatable=%d "
            "eligible=%s hamilton=%s",
            variant.sku,
            recv_qty,
            allocatable,
            {o.pk: q for o, q in eligible.items()},
            {o.pk: q for o, q in variant_alloc.items()},
        )
        for order, qty in variant_alloc.items():
            if qty > 0:
                distribution[(order, variant)] = qty
                remaining_quota[order] -= qty

    warehouse = ass[0].allocation.stock.warehouse

    logger.debug(
        "variant_reallocate: final distribution=%s remaining_quota=%s",
        {(o.pk, v.sku): q for (o, v), q in distribution.items()},
        {o.pk: q for o, q in remaining_quota.items()},
    )

    _apply_reallocation(
        removals=mismatched_ass,
        distribution=distribution,
        poi_by_variant=poi_by_variant,
        received_by_poi=received_by_poi,
        warehouse=warehouse,
    )

    total_distributed = sum(distribution.values())
    if total_order_entitlement != total_distributed:
        raise CannotReallocateVariants(
            f"Invariant violation: entitlement {total_order_entitlement} "
            f"!= distributed {total_distributed}"
        )
    order_distributed: dict = {}
    for (order, _), qty in distribution.items():
        order_distributed[order] = order_distributed.get(order, 0) + qty
    for order, expected_total in order_entitlement.items():
        if order_distributed.get(order, 0) != expected_total:
            raise CannotReallocateVariants(
                f"Invariant violation: order {order.pk} expected "
                f"{expected_total}, got {order_distributed.get(order, 0)}"
            )

    return True


@transaction.atomic
def complete_receipt(receipt, user=None, manager=None):
    """Complete a receipt and process any discrepancies.

    Tries variant reallocation first for each product group with discrepancies.
    Falls back to creating POIAs when reallocation fails (shortage, reallocation
    not allowed, etc).

    Returns:
        dict with summary: {
            'receipt': Receipt,
            'adjustments_pending': [PurchaseOrderItemAdjustment, ...],
            'items_received': int,
            'discrepancies': int,
        }

    Raises:
        ReceiptNotInProgress: If receipt is not in progress

    """
    from ..core.notify import AdminNotifyEvent, NotifyHandler
    from . import (
        PurchaseOrderItemAdjustmentReason,
        PurchaseOrderStatus,
        ReceiptStatus,
    )
    from .models import PurchaseOrder, PurchaseOrderItemAdjustment

    receipt = type(receipt).objects.select_for_update().get(pk=receipt.pk)
    if receipt.status != ReceiptStatus.IN_PROGRESS:
        raise ReceiptNotInProgress(receipt)

    shipment = receipt.shipment
    logger.debug(
        "complete_receipt: receipt=%s shipment=%s",
        receipt.pk,
        shipment.pk,
    )

    all_pois = (
        PurchaseOrderItem.objects.select_for_update()
        .filter(shipment=shipment)
        .select_related("product_variant__product")
        .prefetch_related("receipt_lines")
    )

    adjustments_pending = []

    pois_with_discrepancies = []
    for poi in all_pois:
        if poi.quantity_received != poi.quantity_ordered:
            pois_with_discrepancies.append(poi)
            logger.debug(
                "complete_receipt: poi %s variant=%s DISCREPANCY "
                "ordered=%d received=%d (delta=%+d)",
                poi.pk,
                poi.product_variant.sku,
                poi.quantity_ordered,
                poi.quantity_received,
                poi.quantity_received - poi.quantity_ordered,
            )
        else:
            logger.debug(
                "complete_receipt: poi %s variant=%s OK "
                "ordered=%d received=%d -> RECEIVED",
                poi.pk,
                poi.product_variant.sku,
                poi.quantity_ordered,
                poi.quantity_received,
            )
            poi.status = PurchaseOrderItemStatus.RECEIVED
            poi.save(update_fields=["status", "updated_at"])

    pois_by_product = defaultdict(list)
    for poi in pois_with_discrepancies:
        pois_by_product[poi.product_variant.product].append(poi)

    logger.debug(
        "complete_receipt: %d products with discrepancies, %d POIs total",
        len(pois_by_product),
        len(pois_with_discrepancies),
    )

    for product, product_pois in pois_by_product.items():
        rs = [rl for poi in product_pois for rl in poi.receipt_lines.all()]
        ass = list(
            AllocationSource.objects.filter(
                purchase_order_item__in=product_pois,
                allocation__order_line__order__allow_variant_reallocation=True,
            ).select_related(
                "allocation__order_line__order",
                "allocation__stock",
                "purchase_order_item__product_variant",
            )
        )

        logger.debug(
            "complete_receipt: product %s (%s) — %d POIs, %d receipt lines, "
            "%d reallocation-eligible allocation sources",
            product.pk,
            product.name,
            len(product_pois),
            len(rs),
            len(ass),
        )

        reallocation_succeeded = False
        try:
            reallocation_succeeded = _variant_reallocate(rs, ass)
            logger.debug(
                "complete_receipt: product %s reallocation succeeded",
                product.pk,
            )
        except CannotReallocateVariants as e:
            logger.debug(
                "complete_receipt: product %s reallocation failed: %s",
                product.pk,
                e,
            )

        if reallocation_succeeded:
            total_ordered = sum(p.quantity_ordered for p in product_pois)
            total_received = sum(p.quantity_received for p in product_pois)
            if total_received == total_ordered:
                for poi in product_pois:
                    poi.refresh_from_db()
                    received = poi.quantity_received
                    if received != poi.quantity_ordered:
                        logger.debug(
                            "complete_receipt: poi %s variant=%s adjusting "
                            "quantity_ordered %d -> %d (reallocation)",
                            poi.pk,
                            poi.product_variant.sku,
                            poi.quantity_ordered,
                            received,
                        )
                        poi.quantity_ordered = received
                        poi.save(update_fields=["quantity_ordered", "updated_at"])

        for poi in product_pois:
            poi.refresh_from_db()
            discrepancy = poi.quantity_received - poi.quantity_ordered
            if discrepancy == 0:
                logger.debug(
                    "complete_receipt: poi %s variant=%s resolved by "
                    "reallocation -> RECEIVED",
                    poi.pk,
                    poi.product_variant.sku,
                )
                poi.status = PurchaseOrderItemStatus.RECEIVED
                poi.save(update_fields=["status", "updated_at"])
            else:
                reason = (
                    PurchaseOrderItemAdjustmentReason.DELIVERY_SHORT
                    if discrepancy < 0
                    else PurchaseOrderItemAdjustmentReason.CYCLE_COUNT_POSITIVE
                )
                adjustment = PurchaseOrderItemAdjustment.objects.create(
                    purchase_order_item=poi,
                    quantity_change=discrepancy,
                    reason=reason,
                    affects_payable=True,
                    notes=(
                        f"Auto-created during receipt completion "
                        f"(Receipt #{receipt.id})"
                    ),
                    created_by=user,
                )
                logger.debug(
                    "complete_receipt: poi %s variant=%s unresolved "
                    "discrepancy=%+d -> POIA %s (%s) -> REQUIRES_ATTENTION",
                    poi.pk,
                    poi.product_variant.sku,
                    discrepancy,
                    adjustment.pk,
                    reason,
                )
                adjustment_created_event(adjustment=adjustment, user=user)
                poi.status = PurchaseOrderItemStatus.REQUIRES_ATTENTION
                poi.save(update_fields=["status", "updated_at"])
                adjustments_pending.append(adjustment)

    # Mark shipment as arrived
    if shipment.arrived_at is None:
        shipment.arrived_at = timezone.now()
        shipment.save(update_fields=["arrived_at"])
        logger.debug(
            "complete_receipt: shipment %s marked arrived",
            shipment.pk,
        )

    # Complete the receipt
    receipt.status = ReceiptStatus.COMPLETED
    receipt.completed_at = timezone.now()
    receipt.completed_by = user
    receipt.save(update_fields=["status", "completed_at", "completed_by"])

    # Transition PO status based on how many items are now received.
    po_ids = list({poi.order_id for poi in all_pois})
    for po in PurchaseOrder.objects.filter(pk__in=po_ids).select_for_update():
        unreceived = po.items.exclude(
            status__in=[
                PurchaseOrderItemStatus.RECEIVED,
                PurchaseOrderItemStatus.CANCELLED,
            ]
        )
        if not unreceived.exists():
            new_status = PurchaseOrderStatus.RECEIVED
        else:
            new_status = PurchaseOrderStatus.PARTIALLY_RECEIVED
        if po.status != new_status:
            logger.debug(
                "complete_receipt: PO %s status %s -> %s",
                po.pk,
                po.status,
                new_status,
            )
            po.status = new_status
            po.save(update_fields=["status", "updated_at"])

    # Create fulfillments only if no pending adjustments
    if not adjustments_pending:
        logger.debug("complete_receipt: no pending adjustments, creating fulfillments")
        _create_fulfillments_for_shipment(shipment=shipment, user=user, manager=manager)
    else:
        logger.debug(
            "complete_receipt: %d pending adjustments, skipping fulfillments",
            len(adjustments_pending),
        )

    # If there are pending adjustments, notify staff
    if adjustments_pending and manager:

        def generate_payload():
            return {
                "receipt_id": receipt.id,
                "shipment_id": shipment.id,
                "count": len(adjustments_pending),
                "adjustments": [
                    {
                        "id": adj.id,
                        "poi_id": adj.purchase_order_item.id,
                        "variant_sku": adj.purchase_order_item.product_variant.sku,
                        "quantity_change": adj.quantity_change,
                        "reason": adj.get_reason_display(),
                    }
                    for adj in adjustments_pending
                ],
            }

        handler = NotifyHandler(generate_payload)
        manager.notify(
            AdminNotifyEvent.PENDING_ADJUSTMENTS,
            payload_func=handler.payload,
        )

    return {
        "receipt": receipt,
        "adjustments_pending": adjustments_pending,
        "items_received": len(all_pois),
        "discrepancies": len(pois_with_discrepancies),
    }


def _create_fulfillments_for_shipment(shipment, user, manager):
    from django.contrib.sites.models import Site

    from ..order import OrderStatus
    from ..order.actions import OrderFulfillmentLineInfo, create_fulfillments
    from ..order.models import Order
    from ..plugins.manager import get_plugins_manager
    from ..warehouse.models import Allocation

    fulfill_manager = manager or get_plugins_manager(allow_replica=False)
    site_settings = Site.objects.get_current().settings

    orders_to_fulfill = Order.objects.filter(
        lines__allocations__allocation_sources__purchase_order_item__shipment=shipment,
        status=OrderStatus.UNFULFILLED,
    ).distinct()

    for order in orders_to_fulfill:
        allocations = Allocation.objects.filter(order_line__order=order).select_related(
            "stock__warehouse", "order_line"
        )

        warehouse_groups: dict = defaultdict(list)
        for allocation in allocations:
            warehouse_groups[allocation.stock.warehouse_id].append(allocation)

        fulfillment_lines_for_warehouses = {
            warehouse_pk: [
                OrderFulfillmentLineInfo(
                    order_line=alloc.order_line,
                    quantity=alloc.quantity_allocated,
                )
                for alloc in alloc_list
            ]
            for warehouse_pk, alloc_list in warehouse_groups.items()
        }

        create_fulfillments(
            user=user,
            app=None,
            order=order,
            fulfillment_lines_for_warehouses=fulfillment_lines_for_warehouses,
            manager=fulfill_manager,
            site_settings=site_settings,
            notify_customer=False,
            auto_approved=False,
            tracking_url="",
        )


@transaction.atomic
def delete_receipt(receipt):
    """Delete a draft receipt and revert any quantity updates.

    Only allows deleting receipts that are still IN_PROGRESS.
    Reverts POI.quantity_received for all items in the receipt.

    Args:
        receipt: Receipt to delete

    Raises:
        ReceiptNotInProgress: If receipt is already completed

    """
    from . import ReceiptStatus

    # Only allow deleting in-progress receipts
    if receipt.status != ReceiptStatus.IN_PROGRESS:
        raise ReceiptNotInProgress(receipt)

    # Delete the receipt (cascade will delete lines, quantity_received auto-recalculates)
    receipt.delete()


@transaction.atomic
def delete_receipt_line(receipt_line):
    """Delete a receipt line and revert quantity update.

    Use when an item was scanned by mistake during receiving.
    Only works if receipt is still IN_PROGRESS.

    Args:
        receipt_line: ReceiptLine to delete

    Raises:
        ReceiptLineNotInProgress: If receipt is not in progress

    """
    from . import ReceiptStatus

    # Only allow deleting lines from in-progress receipts
    if receipt_line.receipt.status != ReceiptStatus.IN_PROGRESS:
        raise ReceiptLineNotInProgress(receipt_line)

    # Delete the line (quantity_received auto-recalculates from remaining lines)
    receipt_line.delete()


# ---------------------------------------------------------------------------
# POIA resolution
# ---------------------------------------------------------------------------


def get_product_discrepancies(receipt):
    """Return product-level discrepancy view for a completed receipt.

    For each product with pending (unprocessed) POIAs, returns:
    - Per-variant breakdown: ordered, received, delta
    - Affected orders with their current allocations
    """

    pois = PurchaseOrderItem.objects.filter(
        shipment=receipt.shipment,
        status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
    ).select_related("product_variant__product")

    pois_by_product = defaultdict(list)
    for poi in pois:
        pois_by_product[poi.product_variant.product].append(poi)

    results = []
    for product, product_pois in pois_by_product.items():
        variants = []
        for poi in product_pois:
            variants.append(
                {
                    "variant": poi.product_variant,
                    "quantity_ordered": poi.quantity_ordered,
                    "quantity_received": poi.quantity_received,
                    "delta": poi.quantity_received - poi.quantity_ordered,
                }
            )

        ass = AllocationSource.objects.filter(
            purchase_order_item__in=product_pois,
        ).select_related(
            "allocation__order_line__order",
            "purchase_order_item__product_variant",
        )

        orders_allocs: dict[Order, dict[ProductVariant, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for a in ass:
            order = a.allocation.order_line.order
            variant = a.purchase_order_item.product_variant
            orders_allocs[order][variant] += a.quantity

        affected_orders = []
        for order, variant_map in orders_allocs.items():
            affected_orders.append(
                {
                    "order": order,
                    "allocations": [
                        {"variant": v, "quantity": q} for v, q in variant_map.items()
                    ],
                }
            )

        total_shortage = sum(v["delta"] for v in variants if v["delta"] < 0)

        results.append(
            {
                "product": product,
                "variants": variants,
                "affected_orders": affected_orders,
                "total_shortage": abs(total_shortage),
            }
        )

    return results


@transaction.atomic
def resolve_product_discrepancy(
    receipt,
    product,
    resolutions,
    affects_payable,
    user=None,
    manager=None,
):
    """Resolve all pending POIAs for a product by applying user-specified allocations.

    Args:
        receipt: The completed Receipt these POIAs came from.
        product: The Product being resolved.
        resolutions: list of dicts {order, variant, quantity} — the desired
            end state for each (order, variant) pair. Omitted pairs are removed.
        affects_payable: Whether the supplier owes credit for this discrepancy.
        user: User performing the resolution.
        manager: Plugin manager for event dispatching.

    Returns:
        list of resolved PurchaseOrderItemAdjustments.

    Raises:
        ValueError: If no pending POIAs, or resolution over-allocates.

    """

    pois = list(
        PurchaseOrderItem.objects.select_for_update()
        .filter(
            shipment=receipt.shipment,
            product_variant__product=product,
            status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
        )
        .select_related("product_variant")
    )

    if not pois:
        raise ValueError(
            f"No pending POIAs for product {product} on receipt {receipt.id}"
        )

    # Build poi_by_variant for _apply_reallocation
    poi_by_variant: dict[ProductVariant, list[PurchaseOrderItem]] = defaultdict(list)
    for poi in pois:
        if poi not in poi_by_variant[poi.product_variant]:
            poi_by_variant[poi.product_variant].append(poi)

    # Gather all current AllocationSources for these POIs
    current_ass = list(
        AllocationSource.objects.select_for_update()
        .filter(
            purchase_order_item__in=pois,
        )
        .select_related(
            "allocation__order_line__order",
            "allocation__stock",
            "purchase_order_item__product_variant",
        )
    )

    # Determine the warehouse from existing allocations or POI destination
    if current_ass:
        warehouse = current_ass[0].allocation.stock.warehouse
    else:
        warehouse = pois[0].order.destination_warehouse

    # Build the desired distribution from resolutions
    distribution: dict[tuple[Order, ProductVariant], int] = {}
    for r in resolutions:
        key = (r["order"], r["variant"])
        distribution[key] = distribution.get(key, 0) + r["quantity"]

    # Validate: can't allocate more of a variant than was received
    received_by_variant: dict[ProductVariant, int] = defaultdict(int)
    for poi in pois:
        received_by_variant[poi.product_variant] += poi.quantity_received

    variant_totals: dict[ProductVariant, int] = defaultdict(int)
    for (_order, variant), qty in distribution.items():
        variant_totals[variant] += qty
    for variant, total in variant_totals.items():
        received = received_by_variant.get(variant, 0)
        if total > received:
            raise ValueError(
                f"Cannot allocate {total} of {variant.sku}: only {received} received"
            )

    # Apply the reallocation
    received_by_poi = {poi: poi.quantity_received for poi in pois}

    _apply_reallocation(
        removals=current_ass,
        distribution=distribution,
        poi_by_variant=dict(poi_by_variant),
        received_by_poi=received_by_poi,
        warehouse=warehouse,
    )

    # Mark all pending POIAs for these POIs as processed
    adjustments = list(
        PurchaseOrderItemAdjustment.objects.filter(
            purchase_order_item__in=pois,
            processed_at__isnull=True,
        )
    )

    now = timezone.now()
    for adj in adjustments:
        adj.affects_payable = affects_payable
        adj.processed_at = now
        adj.save(update_fields=["affects_payable", "processed_at"])
        adjustment_processed_event(adjustment=adj, user=user)

    # Transition POIs to RECEIVED
    for poi in pois:
        poi.status = PurchaseOrderItemStatus.RECEIVED
        poi.save(update_fields=["status", "updated_at"])

    # If all POIs on this shipment are now RECEIVED, create fulfillments
    shipment = receipt.shipment
    remaining = (
        PurchaseOrderItem.objects.filter(
            shipment=shipment,
        )
        .exclude(
            status=PurchaseOrderItemStatus.RECEIVED,
        )
        .exists()
    )

    if not remaining:
        _create_fulfillments_for_shipment(
            shipment=shipment,
            user=user,
            manager=manager,
        )

    return adjustments

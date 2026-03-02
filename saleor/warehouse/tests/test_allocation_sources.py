"""Tests for AllocationSource tracking in owned warehouses.

AllocationSource records track which PurchaseOrderItem batches fulfill which
customer order allocations. This is required for:
- COGS (Cost of Goods Sold) calculation
- Batch traceability (recalls, expiry tracking)
- FIFO inventory management

Key invariant: Allocations in owned warehouses MUST have AllocationSources.
Allocations in non-owned warehouses do NOT need AllocationSources.
"""

from decimal import Decimal

import pytest
from django.db.models import Sum
from django.utils import timezone

from ...core.exceptions import InsufficientStock
from ...order.fetch import OrderLineInfo
from ...plugins.manager import get_plugins_manager
from ...shipping import ShipmentType
from ..management import (
    allocate_stocks,
    deallocate_stock,
    increase_stock,
)
from ..models import Allocation, AllocationSource, Stock

COUNTRY_CODE = "US"


def test_allocate_sources_creates_allocation_source_for_owned_warehouse(
    order_line, owned_warehouse, purchase_order_item, channel_USD
):
    """When allocating in owned warehouse, AllocationSource is created."""
    # given
    variant = order_line.variant
    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100},
    )
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    # when
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
        COUNTRY_CODE,
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50

    # Check AllocationSource was created
    assert allocation.allocation_sources.count() == 1
    source = allocation.allocation_sources.first()
    assert source.purchase_order_item == purchase_order_item
    assert source.quantity == 50

    # Check POI.quantity_allocated was updated
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_allocated == 50


def test_allocate_sources_not_created_for_nonowned_warehouse(
    order_line, nonowned_warehouse, channel_USD
):
    """Non-owned warehouses don't create AllocationSources."""
    # given
    variant = order_line.variant
    stock = Stock.objects.create(
        warehouse=nonowned_warehouse, product_variant=variant, quantity=100
    )

    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    # when
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
        COUNTRY_CODE,
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50

    # Check NO AllocationSource was created for non-owned warehouse
    assert allocation.allocation_sources.count() == 0


def test_deallocate_sources_restores_poi_quantity_allocated(
    order_line, owned_warehouse, purchase_order_item, channel_USD
):
    """Deallocating removes AllocationSource and restores POI.quantity_allocated."""
    # given - create allocation with source
    variant = order_line.variant
    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100},
    )
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
        COUNTRY_CODE,
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.allocation_sources.count() == 1

    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_allocated == 50

    # when - deallocate
    deallocate_stock(
        [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - AllocationSource removed and POI.quantity_allocated restored
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 0
    assert allocation.allocation_sources.count() == 0

    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_allocated == 0


def test_partial_deallocate_updates_poi_correctly(
    order_line, owned_warehouse, purchase_order_item, channel_USD
):
    """Partial deallocation reduces POI.quantity_allocated correctly."""
    # given - allocate 50
    variant = order_line.variant
    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100},
    )
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
        COUNTRY_CODE,
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_allocated == 50

    # when - deallocate 20
    deallocate_stock(
        [OrderLineInfo(line=order_line, variant=variant, quantity=20)],
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - POI.quantity_allocated reduced to 30
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_allocated == 30

    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 30


def test_allocation_uses_fifo_across_multiple_pois(
    order_line,
    order,
    owned_warehouse,
    multiple_purchase_order_items,
    channel_USD,
):
    """Allocations consume POIs in FIFO order (oldest first)."""
    # given - 3 POIs confirmed at different times, each with 100 units
    poi_oldest, poi_middle, poi_newest = multiple_purchase_order_items
    variant = order_line.variant

    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 300},
    )
    stock.quantity = 300
    stock.save(update_fields=["quantity"])

    # Create 3 order lines to allocate 250 units total
    order_line_2 = order.lines.create(
        product_name=order_line.product_name,
        variant_name=order_line.variant_name,
        product_sku=order_line.product_sku,
        variant=variant,
        quantity=1,
        unit_price_gross_amount=10,
        unit_price_net_amount=10,
        total_price_gross_amount=10,
        total_price_net_amount=10,
        currency="USD",
        is_shipping_required=False,
        is_gift_card=False,
    )

    order_line_3 = order.lines.create(
        product_name=order_line.product_name,
        variant_name=order_line.variant_name,
        product_sku=order_line.product_sku,
        variant=variant,
        quantity=1,
        unit_price_gross_amount=10,
        unit_price_net_amount=10,
        total_price_gross_amount=10,
        total_price_net_amount=10,
        currency="USD",
        is_shipping_required=False,
        is_gift_card=False,
    )

    order_line.quantity = 100
    order_line.save(update_fields=["quantity"])
    order_line_2.quantity = 100
    order_line_2.save(update_fields=["quantity"])
    order_line_3.quantity = 50
    order_line_3.save(update_fields=["quantity"])

    # when - allocate 250 units (100 + 100 + 50)
    allocate_stocks(
        [
            OrderLineInfo(line=order_line, variant=variant, quantity=100),
            OrderLineInfo(line=order_line_2, variant=variant, quantity=100),
            OrderLineInfo(line=order_line_3, variant=variant, quantity=50),
        ],
        COUNTRY_CODE,
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - should consume oldest first (FIFO)
    poi_oldest.refresh_from_db()
    poi_middle.refresh_from_db()
    poi_newest.refresh_from_db()

    assert poi_oldest.quantity_allocated == 100  # Fully consumed
    assert poi_middle.quantity_allocated == 100  # Fully consumed
    assert poi_newest.quantity_allocated == 50  # Partially consumed
    # Total: 250 allocated across 3 POIs in FIFO order


def test_insufficient_poi_quantity_raises_error(
    order_line, owned_warehouse, purchase_order_item, channel_USD
):
    """Allocating more than POI capacity raises InsufficientStock."""
    # given - POI with 100 capacity, 80 already allocated
    variant = order_line.variant
    purchase_order_item.quantity_allocated = 80
    purchase_order_item.save()

    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100},
    )
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    order_line.quantity = 30
    order_line.save(update_fields=["quantity"])

    # when/then - trying to allocate 30 more (total 110 > 100 capacity) fails
    with pytest.raises(InsufficientStock):
        allocate_stocks(
            [OrderLineInfo(line=order_line, variant=variant, quantity=30)],
            COUNTRY_CODE,
            channel_USD,
            manager=get_plugins_manager(allow_replica=False),
        )


def test_poi_quantity_allocated_invariant(
    order,
    owned_warehouse,
    variant,
    purchase_order_item,
    channel_USD,
):
    """POI.quantity_allocated equals sum of AllocationSource.quantity."""
    # given - create 3 order lines
    lines = []
    for i in range(3):
        line = order.lines.create(
            product_name=f"Product {i}",
            variant_name=variant.name,
            product_sku=variant.sku,
            variant=variant,
            quantity=1,
            unit_price_gross_amount=10,
            unit_price_net_amount=10,
            total_price_gross_amount=10,
            total_price_net_amount=10,
            currency="USD",
            is_shipping_required=False,
            is_gift_card=False,
        )
        lines.append(line)

    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100},
    )
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    lines[0].quantity = 10
    lines[0].save(update_fields=["quantity"])
    lines[1].quantity = 20
    lines[1].save(update_fields=["quantity"])
    lines[2].quantity = 15
    lines[2].save(update_fields=["quantity"])

    # when - allocate different amounts to each line (10 + 20 + 15 = 45)
    allocate_stocks(
        [
            OrderLineInfo(line=lines[0], variant=variant, quantity=10),
            OrderLineInfo(line=lines[1], variant=variant, quantity=20),
            OrderLineInfo(line=lines[2], variant=variant, quantity=15),
        ],
        COUNTRY_CODE,
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - POI.quantity_allocated should equal sum of all AllocationSource quantities
    total_from_sources = (
        AllocationSource.objects.filter(
            purchase_order_item=purchase_order_item
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )

    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_allocated == 45
    assert purchase_order_item.quantity_allocated == total_from_sources


def test_increase_stock_with_allocate_creates_sources(
    order_line, owned_warehouse, purchase_order_item
):
    """increase_stock with allocate=True creates AllocationSources."""
    # given
    variant = order_line.variant
    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 50},
    )
    stock.quantity = 50
    stock.save(update_fields=["quantity"])

    # when
    increase_stock(order_line, owned_warehouse, quantity=30, allocate=True)

    # then
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 30
    assert allocation.allocation_sources.count() == 1

    source = allocation.allocation_sources.first()
    assert source.purchase_order_item == purchase_order_item
    assert source.quantity == 30

    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_allocated == 30


def test_increase_existing_allocation_creates_incremental_sources(
    order_line, owned_warehouse, purchase_order_item, channel_USD
):
    """Increasing existing allocation creates additional AllocationSources."""
    # given - initial allocation of 20
    variant = order_line.variant
    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100},
    )
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    order_line.quantity = 35
    order_line.save(update_fields=["quantity"])

    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=20)],
        COUNTRY_CODE,
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 20
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_allocated == 20

    # when - increase by 15 more
    increase_stock(order_line, owned_warehouse, quantity=15, allocate=True)

    # then - total allocation is 35, POI.quantity_allocated is 35
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 35

    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_allocated == 35

    # AllocationSource quantity should sum to 35
    total_sources = (
        allocation.allocation_sources.aggregate(total=Sum("quantity"))["total"] or 0
    )
    assert total_sources == 35


def test_order_auto_confirms_when_all_allocations_sourced(
    order_line, owned_warehouse, purchase_order_item, channel_USD
):
    """Order automatically confirms when all AllocationSources are assigned."""
    from ...order import OrderStatus

    # given - UNCONFIRMED order
    order = order_line.order
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    variant = order_line.variant
    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100},
    )
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    # when - allocate (which creates AllocationSources)
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
        COUNTRY_CODE,
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - order should auto-confirm
    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED


def test_allocate_sources_ignores_draft_and_cancelled_pois(
    order_line, owned_warehouse, purchase_order, channel_USD
):
    """AllocationSource only uses CONFIRMED or RECEIVED POIs, not DRAFT or CANCELLED."""
    from ...inventory import PurchaseOrderItemStatus
    from ...inventory.models import PurchaseOrderItem
    from ...shipping.models import Shipment

    # given - stock in owned warehouse
    variant = order_line.variant
    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100},
    )
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    # Create DRAFT POI (should be ignored)
    from ...shipping import IncoTerm

    shipment = Shipment.objects.create(
        source=purchase_order.source_warehouse.address,
        destination=purchase_order.destination_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="DRAFT-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )
    PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,  # DRAFT - should be ignored
    )

    # when - try to allocate (should fail - no active POIs)
    with pytest.raises(InsufficientStock):
        allocate_stocks(
            [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
            COUNTRY_CODE,
            channel_USD,
            manager=get_plugins_manager(allow_replica=False),
        )

    # then - no AllocationSource created (allocation itself may exist but failed)
    assert AllocationSource.objects.count() == 0


def test_allocate_sources_prefers_received_poi_over_confirmed(
    order_line,
    owned_warehouse,
    purchase_order_item,
    purchase_order,
    channel_USD,
):
    """RECEIVED POIs are sourced before CONFIRMED POIs regardless of FIFO date.

    Regression test: when stock has physically arrived (RECEIVED POI) alongside
    in-transit stock (CONFIRMED POI), allocation must source from the received
    batch so the order line reports received quantity > 0 (not 'Out of Stock').
    """
    from datetime import timedelta

    from ...inventory import PurchaseOrderItemStatus
    from ...inventory.models import PurchaseOrderItem
    from ...inventory.receipt_workflow import (
        complete_receipt,
        receive_item,
        start_receipt,
    )
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment
    from ..stock_utils import get_received_quantity_for_order_line

    variant = order_line.variant

    # purchase_order_item fixture is already a CONFIRMED (in-transit) POI
    poi_confirmed = purchase_order_item

    # Create a second shipment and POI that will be fully received
    shipment_received = Shipment.objects.create(
        source=purchase_order.source_warehouse.address,
        destination=purchase_order.destination_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="SHIPMENT-RECEIVED-TEST",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
    )
    poi_received = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=10,
        total_price_amount=100.00,
        currency="USD",
        shipment=shipment_received,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi_received)

    # Make poi_confirmed older so pure FIFO would pick it first (the buggy behaviour)
    now = timezone.now()
    poi_confirmed.confirmed_at = now - timedelta(days=2)
    poi_confirmed.save(update_fields=["confirmed_at"])
    poi_received.confirmed_at = now - timedelta(days=1)
    poi_received.save(update_fields=["confirmed_at"])

    # Receive poi_received through the receipt workflow
    receipt = start_receipt(shipment_received)
    receive_item(receipt, variant, 10)
    complete_receipt(receipt)

    poi_received.refresh_from_db()
    assert poi_received.status == PurchaseOrderItemStatus.RECEIVED

    order_line.quantity = 1
    order_line.save(update_fields=["quantity"])
    stock = Stock.objects.get(warehouse=owned_warehouse, product_variant=variant)

    # when
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=1)],
        COUNTRY_CODE,
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - source must come from the RECEIVED POI, not the older CONFIRMED one
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.allocation_sources.count() == 1
    source = allocation.allocation_sources.first()
    assert source.purchase_order_item == poi_received

    # And received quantity must be > 0 so the line is not shown as 'Out of Stock'
    received_qty = get_received_quantity_for_order_line(order_line)
    assert received_qty > 0

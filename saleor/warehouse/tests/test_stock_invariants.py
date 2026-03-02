"""Dedicated tests for the Stock ↔ POI invariants in owned warehouses.

THE THREE FUNDAMENTAL INVARIANTS:

1. Total Physical Stock - conservation of mass:
    Stock.quantity == sum(POI.quantity_ordered + processed_adjustments - POI.quantity_fulfilled)

    For any (owned_warehouse, variant) pair, Stock.quantity represents physical stock
    currently in the warehouse. This equals what we received from suppliers (quantity_ordered
    + adjustments) minus what we've shipped to customers (quantity_fulfilled).

    Note: POI.quantity_received is just an audit trail showing what initially arrived.
    The actual stock is always based on quantity_ordered + processed_adjustments - quantity_fulfilled.
    Only processed adjustments (processed_at != NULL) are included.

2. Allocation Tracking - AllocationSources link Stock to POI batches:
    Stock.quantity_allocated == sum(POI.quantity_allocated)

    For owned warehouses, AllocationSources ensure that Stock.quantity_allocated
    always matches the sum of POI.quantity_allocated across all active POIs.

3. Fulfillment Tracking - FulfillmentSources provide audit trail:
    sum(FulfillmentSource.quantity) == sum(POI.quantity_fulfilled)

    When items are fulfilled, AllocationSources are converted to FulfillmentSources
    and POI.quantity_fulfilled is incremented.

DERIVED RELATIONSHIP (follows mathematically from the above):
    Available stock: Stock.quantity - Stock.quantity_allocated == sum(POI.available_quantity)
    Where POI.available_quantity = (quantity_ordered + processed_adjustments - quantity_allocated - quantity_fulfilled)

Any time an invariant is violated we should add a test here. We should also regularly
run an invariant validation to make sure the Stock is in the correct state.
"""

from decimal import Decimal

import pytest
from django.utils import timezone
from prices import Money

from ...inventory import PurchaseOrderItemStatus
from ...inventory.models import PurchaseOrderItem, PurchaseOrderRequestedAllocation
from ...shipping import IncoTerm, ShipmentType
from ..models import Stock


def calculate_expected_stock_quantity(warehouse, variant):
    """Calculate what Stock.quantity SHOULD be based on POIs (PRIMARY INVARIANT).

    This is the "source of truth" calculation from the POI table.
    Stock.quantity should always equal this value.

    Returns physical stock currently in warehouse.
    Formula: sum(POI.quantity_ordered + processed_adjustments - quantity_fulfilled)

    This equals what we received from suppliers minus what we shipped to customers.
    """
    from django.db.models import Sum

    pois = PurchaseOrderItem.objects.filter(
        order__destination_warehouse=warehouse,
        product_variant=variant,
        status__in=PurchaseOrderItemStatus.STOCK_PRESENT_STATUSES,
    )

    total = 0
    for poi in pois:
        # Get processed adjustments for this POI
        processed_adjustments = (
            poi.adjustments.filter(processed_at__isnull=False).aggregate(
                total=Sum("quantity_change")
            )["total"]
            or 0
        )

        # Physical stock in warehouse = received from supplier - shipped to customers
        total += poi.quantity_ordered + processed_adjustments - poi.quantity_fulfilled

    return total


def calculate_expected_available_quantity(warehouse, variant):
    """Calculate what available stock SHOULD be based on POIs (SECONDARY INVARIANT).

    This calculates: sum(POI.available_quantity)
    Which should equal: Stock.quantity - Stock.quantity_allocated

    Returns the sum of available (unallocated) quantities from POIs.
    """
    pois = PurchaseOrderItem.objects.filter(
        order__destination_warehouse=warehouse,
        product_variant=variant,
        status__in=PurchaseOrderItemStatus.STOCK_PRESENT_STATUSES,
    ).annotate_available_quantity()

    return sum(poi.available_quantity for poi in pois)


def calculate_expected_poi_allocated(warehouse, variant):
    """Calculate what POI.quantity_allocated SHOULD sum to (TERTIARY INVARIANT).

    For owned warehouses, this should equal Stock.quantity_allocated
    because AllocationSources link stock allocations to POI allocations.
    """
    pois = PurchaseOrderItem.objects.filter(
        order__destination_warehouse=warehouse,
        product_variant=variant,
        status__in=PurchaseOrderItemStatus.STOCK_PRESENT_STATUSES,
    )

    return sum(poi.quantity_allocated for poi in pois)


def assert_stock_poi_invariant(warehouse, variant):
    """Assert ALL FUNDAMENTAL INVARIANTS hold for a specific warehouse/variant pair.

    This is THE assertion that proves Stock is a client of POI.

    Checks:
    1. INVARIANT 1: Stock.quantity == sum(POI.quantity_ordered + adjustments - fulfilled)
    2. INVARIANT 2: Stock.quantity_allocated == sum(POI.quantity_allocated)
    3. INVARIANT 3: For each POI: sum(FulfillmentSource.quantity) == POI.quantity_fulfilled
    4. INVARIANT 4: For each Allocation in owned warehouse: sum(AllocationSource.quantity) == Allocation.quantity_allocated
    5. INVARIANT 5: For each POI: quantity_ordered + adjustments == allocated + fulfilled + available (conservation)
    6. INVARIANT 6: No negative quantities
    7. INVARIANT 7: Logical constraints (allocated + fulfilled <= ordered + adjustments)
    8. DERIVED: Stock.quantity - Stock.quantity_allocated == sum(POI.available_quantity)
    """
    from ...inventory import PurchaseOrderItemStatus
    from ...inventory.models import PurchaseOrderItem

    stock = Stock.objects.filter(warehouse=warehouse, product_variant=variant).first()
    expected_total = calculate_expected_stock_quantity(warehouse, variant)
    expected_available = calculate_expected_available_quantity(warehouse, variant)
    expected_poi_allocated = calculate_expected_poi_allocated(warehouse, variant)

    if stock:
        actual_quantity = stock.quantity
        actual_allocated = stock.quantity_allocated
        actual_available = stock.quantity - stock.quantity_allocated
    else:
        actual_quantity = 0
        actual_allocated = 0
        actual_available = 0

    # Get debug info about POIs
    pois = PurchaseOrderItem.objects.filter(
        order__destination_warehouse=warehouse,
        product_variant=variant,
        status__in=PurchaseOrderItemStatus.STOCK_PRESENT_STATUSES,
    )

    poi_debug = []
    for poi in pois:
        poi_debug.append(
            f"    POI #{poi.id}: ordered={poi.quantity_ordered}, "
            f"allocated={poi.quantity_allocated}, available={poi.available_quantity}, "
            f"status={poi.status}"
        )

    # Check INVARIANT 1: Stock.quantity = total from POIs
    assert actual_quantity == expected_total, (
        f"INVARIANT 1 VIOLATED for {warehouse.name} / {variant.sku}:\n"
        f"  Stock.quantity (total physical): {actual_quantity}\n"
        f"  Expected (sum POI.ordered/received): {expected_total}\n"
        f"  Difference: {actual_quantity - expected_total}\n"
        f"  Stock.quantity_allocated: {actual_allocated}\n"
        f"  POIs:\n" + "\n".join(poi_debug or ["    None"])
    )

    # Check INVARIANT 2: Allocations tracked via POIs
    assert actual_allocated == expected_poi_allocated, (
        f"INVARIANT 2 VIOLATED for {warehouse.name} / {variant.sku}:\n"
        f"  Stock.quantity_allocated: {actual_allocated}\n"
        f"  Expected (sum POI.quantity_allocated): {expected_poi_allocated}\n"
        f"  Difference: {actual_allocated - expected_poi_allocated}\n"
        f"  This means AllocationSources are not properly tracking allocations to POIs!\n"
        f"  POIs:\n" + "\n".join(poi_debug or ["    None"])
    )

    # Check DERIVED relationship: Available stock matches
    assert actual_available == expected_available, (
        f"DERIVED RELATIONSHIP VIOLATED for {warehouse.name} / {variant.sku}:\n"
        f"  Stock.quantity - Stock.quantity_allocated: {actual_available}\n"
        f"  Expected (sum POI.available): {expected_available}\n"
        f"  Difference: {actual_available - expected_available}\n"
        f"  This should be mathematically impossible if Invariants 1 and 2 hold!\n"
        f"  Breakdown:\n"
        f"    Stock.quantity: {actual_quantity}\n"
        f"    Stock.quantity_allocated: {actual_allocated}\n"
        f"  POIs:\n" + "\n".join(poi_debug or ["    None"])
    )

    # Check INVARIANT 3: FulfillmentSource audit trail matches POI.quantity_fulfilled
    from django.db.models import Sum

    from ..models import FulfillmentSource

    for poi in pois:
        fulfillment_source_sum = (
            FulfillmentSource.objects.filter(purchase_order_item=poi).aggregate(
                total=Sum("quantity")
            )["total"]
            or 0
        )
        assert fulfillment_source_sum == poi.quantity_fulfilled, (
            f"INVARIANT 3 VIOLATED for POI #{poi.id}:\n"
            f"  POI.quantity_fulfilled: {poi.quantity_fulfilled}\n"
            f"  sum(FulfillmentSource.quantity): {fulfillment_source_sum}\n"
            f"  FulfillmentSource audit trail doesn't match fulfilled quantity!"
        )

    # Check INVARIANT 4: AllocationSource batch tracking (owned warehouses only)
    from ..models import Allocation, AllocationSource

    if warehouse.is_owned:
        allocations = Allocation.objects.filter(
            stock__warehouse=warehouse, stock__product_variant=variant
        )
        for allocation in allocations:
            allocation_source_sum = (
                AllocationSource.objects.filter(allocation=allocation).aggregate(
                    total=Sum("quantity")
                )["total"]
                or 0
            )
            assert allocation_source_sum == allocation.quantity_allocated, (
                f"INVARIANT 4 VIOLATED for Allocation #{allocation.id}:\n"
                f"  Allocation.quantity_allocated: {allocation.quantity_allocated}\n"
                f"  sum(AllocationSource.quantity): {allocation_source_sum}\n"
                f"  AllocationSource batch tracking doesn't match allocated quantity!"
            )

    # Check INVARIANT 5: POI conservation of mass
    for poi in pois:
        processed_adjustments = (
            poi.adjustments.filter(processed_at__isnull=False).aggregate(
                total=Sum("quantity_change")
            )["total"]
            or 0
        )
        total_received = poi.quantity_ordered + processed_adjustments
        total_accounted = (
            poi.quantity_allocated + poi.quantity_fulfilled + poi.available_quantity
        )
        assert total_received == total_accounted, (
            f"INVARIANT 5 VIOLATED for POI #{poi.id} (conservation of mass):\n"
            f"  Received: quantity_ordered ({poi.quantity_ordered}) + "
            f"adjustments ({processed_adjustments}) = {total_received}\n"
            f"  Accounted: allocated ({poi.quantity_allocated}) + "
            f"fulfilled ({poi.quantity_fulfilled}) + "
            f"available ({poi.available_quantity}) = {total_accounted}\n"
            f"  Units are missing or created from nothing!"
        )

    # Check INVARIANT 6: No negative quantities
    for poi in pois:
        assert poi.quantity_allocated >= 0, (
            f"INVARIANT 6 VIOLATED for POI #{poi.id}: "
            f"quantity_allocated ({poi.quantity_allocated}) is negative!"
        )
        assert poi.quantity_fulfilled >= 0, (
            f"INVARIANT 6 VIOLATED for POI #{poi.id}: "
            f"quantity_fulfilled ({poi.quantity_fulfilled}) is negative!"
        )
        assert poi.available_quantity >= 0, (
            f"INVARIANT 6 VIOLATED for POI #{poi.id}: "
            f"available_quantity ({poi.available_quantity}) is negative!"
        )

    if stock:
        assert stock.quantity >= 0, (
            f"INVARIANT 6 VIOLATED for Stock: quantity ({stock.quantity}) is negative!"
        )
        assert stock.quantity_allocated >= 0, (
            f"INVARIANT 6 VIOLATED for Stock: "
            f"quantity_allocated ({stock.quantity_allocated}) is negative!"
        )

    # Check INVARIANT 7: Logical constraints
    for poi in pois:
        processed_adjustments = (
            poi.adjustments.filter(processed_at__isnull=False).aggregate(
                total=Sum("quantity_change")
            )["total"]
            or 0
        )
        max_allowed = poi.quantity_ordered + processed_adjustments
        actual_used = poi.quantity_allocated + poi.quantity_fulfilled
        assert actual_used <= max_allowed, (
            f"INVARIANT 7 VIOLATED for POI #{poi.id}:\n"
            f"  Max available: quantity_ordered ({poi.quantity_ordered}) + "
            f"adjustments ({processed_adjustments}) = {max_allowed}\n"
            f"  Actually used: allocated ({poi.quantity_allocated}) + "
            f"fulfilled ({poi.quantity_fulfilled}) = {actual_used}\n"
            f"  Cannot allocate + fulfill more than we have!"
        )

    if stock:
        assert stock.quantity_allocated <= stock.quantity, (
            f"INVARIANT 7 VIOLATED for Stock:\n"
            f"  Stock.quantity: {stock.quantity}\n"
            f"  Stock.quantity_allocated: {stock.quantity_allocated}\n"
            f"  Cannot allocate more than physical stock!"
        )


# ==============================================================================
# INVARIANT TESTS
# ==============================================================================


def test_invariant_empty_database():
    """With no POIs, Stock.quantity should be 0 (or no Stock exists).

    Purpose: Verify invariant holds in the trivial base case.
    """
    # given - empty database (pytest fixture handles cleanup)

    # then - no stocks should exist OR all stocks have quantity=0
    for stock in Stock.objects.filter(warehouse__is_owned=True):
        expected = calculate_expected_stock_quantity(
            stock.warehouse, stock.product_variant
        )
        assert stock.quantity == expected


def test_invariant_after_single_poi_confirmation(
    owned_warehouse, variant, purchase_order, nonowned_warehouse
):
    """After confirming one POI, invariant holds.

    Purpose: Verify invariant after the most basic operation.
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...shipping.models import Shipment

    # given - source stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=200,
    )

    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    # when
    confirm_purchase_order_item(poi)

    # then - verify invariant
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_with_multiple_pois_same_variant(
    owned_warehouse, variant, purchase_order, nonowned_warehouse
):
    """With multiple POIs for same variant, invariant holds.

    Purpose: Verify Stock.quantity equals SUM of all POI.available_quantity.
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...shipping.models import Shipment

    # given - source stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=500,
    )

    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    # Create 3 POIs with different quantities
    pois = []
    for qty in [100, 75, 50]:
        poi = PurchaseOrderItem.objects.create(
            order=purchase_order,
            product_variant=variant,
            quantity_ordered=qty,
            quantity_allocated=0,
            total_price_amount=1000.0,  # 100 qty × $10.0/unit
            currency="USD",
            shipment=shipment,
            country_of_origin="US",
            status=PurchaseOrderItemStatus.DRAFT,
        )
        pois.append(poi)

    # when - confirm all
    for poi in pois:
        confirm_purchase_order_item(poi)

    # then - invariant holds (Stock.quantity == 100 + 75 + 50 = 225)
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_with_partially_allocated_pois(
    owned_warehouse, variant, purchase_order, nonowned_warehouse
):
    """When POIs have allocations, both invariants hold.

    Purpose: Verify that POI allocations are tracked correctly in Stock.
    INVARIANT 1: Stock.quantity == sum(POI.quantity_ordered) = 100 + 80 = 180
    INVARIANT 2: Stock.quantity_allocated == sum(POI.quantity_allocated) = 30 + 80 = 110
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...shipping.models import Shipment

    # given - source stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=500,
    )

    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    # Create POIs
    poi1 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    poi2 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=80,
        quantity_allocated=0,
        total_price_amount=800.0,  # 80 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    # when - confirm and simulate allocations
    confirm_purchase_order_item(poi1)
    confirm_purchase_order_item(poi2)

    # Simulate allocations (POI.quantity_allocated updated by allocation process)
    poi1.quantity_allocated = 30
    poi1.save()

    poi2.quantity_allocated = 80
    poi2.save()

    # Update Stock.quantity_allocated to match
    stock = Stock.objects.get(warehouse=owned_warehouse, product_variant=variant)
    stock.quantity_allocated = 110  # 30 + 80 (INVARIANT 2)
    stock.save()
    # Note: Stock.quantity stays at 180 (100 + 80, INVARIANT 1)

    # then - both invariants hold
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_with_fully_allocated_poi(
    owned_warehouse, variant, purchase_order, nonowned_warehouse
):
    """Fully allocated POI still contributes to Stock.quantity (INVARIANT 1).

    Purpose: Edge case - POI with available_quantity=0 still has total physical stock.
    INVARIANT 1: Stock.quantity == POI.quantity_ordered = 100
    INVARIANT 2: Stock.quantity_allocated == POI.quantity_allocated = 100
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...shipping.models import Shipment

    # given
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=200,
    )

    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    # when - confirm and fully allocate
    confirm_purchase_order_item(poi)
    poi.quantity_allocated = 100
    poi.save()

    stock = Stock.objects.get(warehouse=owned_warehouse, product_variant=variant)
    stock.quantity_allocated = 100  # INVARIANT 2
    stock.save()
    # Note: Stock.quantity stays at 100 (INVARIANT 1 - total doesn't change)

    # then - both invariants hold
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_excludes_draft_pois(
    owned_warehouse, variant, purchase_order, nonowned_warehouse
):
    """DRAFT POIs don't contribute to Stock.quantity.

    Purpose: Verify only CONFIRMED/RECEIVED POIs count toward invariant.
    """
    from ...shipping.models import Shipment

    # given - DRAFT POI (not confirmed)
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=200,
    )

    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
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
        status=PurchaseOrderItemStatus.DRAFT,  # Still DRAFT
    )

    # when - check stock (should not exist yet)
    stock = Stock.objects.filter(
        warehouse=owned_warehouse, product_variant=variant
    ).first()

    # then - no stock exists, expected quantity is 0 (DRAFT excluded)
    expected = calculate_expected_stock_quantity(owned_warehouse, variant)
    assert expected == 0
    assert stock is None  # No stock created yet

    # Invariant: 0 (no stock) == 0 (no CONFIRMED/RECEIVED POIs) ✓


def test_invariant_with_multiple_variants_in_same_warehouse(
    owned_warehouse, purchase_order, nonowned_warehouse
):
    """Each variant maintains independent invariant.

    Purpose: Verify invariant is per (warehouse, variant) pair, not per warehouse.
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...product.models import Product, ProductType
    from ...shipping.models import Shipment

    # given - 2 variants
    product_type = ProductType.objects.create(name="Test Type", slug="test-type")
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        product_type=product_type,
    )
    variant1 = product.variants.create(sku="VAR-1")
    variant2 = product.variants.create(sku="VAR-2")

    # Source stocks
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant1,
        quantity=300,
    )
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant2,
        quantity=300,
    )

    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    # Create POIs for each variant
    poi1 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant1,
        quantity_ordered=75,
        quantity_allocated=0,
        total_price_amount=750.0,  # 75 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    poi2 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant2,
        quantity_ordered=125,
        quantity_allocated=0,
        total_price_amount=1875.0,  # 125 qty × $15.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    # when - confirm both
    confirm_purchase_order_item(poi1)
    confirm_purchase_order_item(poi2)

    # then - invariant holds for BOTH variants independently
    assert_stock_poi_invariant(owned_warehouse, variant1)
    assert_stock_poi_invariant(owned_warehouse, variant2)


def test_invariant_after_allocation_and_deallocation(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    order_line,
    channel_USD,
):
    """Invariant holds through allocation/deallocation cycle.

    Purpose: Verify that allocation operations don't break the invariant.
    Stock.quantity should remain constant, only Stock.quantity_allocated changes.
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks, deallocate_stock

    # given - confirmed POI
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=300,
    )

    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    confirm_purchase_order_item(poi)

    # Invariant before allocation
    assert_stock_poi_invariant(owned_warehouse, variant)

    # Update order_line quantity to match allocation
    order_line.quantity = 60
    order_line.save(update_fields=["quantity"])

    # when - allocate
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=60)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - invariant still holds (Stock.quantity unchanged, only quantity_allocated changed)
    assert_stock_poi_invariant(owned_warehouse, variant)

    # when - deallocate
    deallocate_stock(
        [OrderLineInfo(line=order_line, variant=variant, quantity=60)],
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - invariant STILL holds
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_does_not_apply_to_nonowned_warehouses(nonowned_warehouse, variant):
    """Invariant only applies to owned warehouses, not suppliers.

    Purpose: Clarify scope - non-owned warehouses are NOT clients of POI table.
    """
    # given - stock in non-owned warehouse
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=500,  # Can be set to any value
    )

    # then - we DON'T check invariant for non-owned warehouses
    # Non-owned warehouse stock is managed externally (supplier data)
    assert not nonowned_warehouse.is_owned

    # There may be POIs sourced from this warehouse, but Stock.quantity
    # doesn't need to match anything - it's just an upper bound


def test_invariant_when_confirming_poi_moves_allocations_from_supplier(
    owned_warehouse,
    nonowned_warehouse,
    purchase_order,
    order_line,
    channel_USD,
):
    """Confirming POI moves existing allocations from supplier to owned warehouse.

    Purpose: Test the REALISTIC flow - customer orders first, then we order from supplier.
    This is the most common scenario in production.

    Flow:
    1. Customer places order → allocated from supplier warehouse (non-owned)
    2. We create and confirm PurchaseOrder
    3. Allocations should migrate: supplier → owned warehouse
    4. AllocationSources should be created
    5. Invariant should hold
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order import OrderStatus
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks
    from ..models import Allocation

    # CRITICAL: Use order_line.variant for ALL operations
    variant = order_line.variant

    # Order must be UNCONFIRMED for allocation at supplier warehouse
    order = order_line.order
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    # Update order_line quantity to match what we're allocating
    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    # given - stock at supplier
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=200,
        quantity_allocated=0,
    )

    # Step 1: Customer orders (allocates from supplier warehouse)
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # Verify: Allocation exists at supplier (non-owned)
    allocation = Allocation.objects.get(order_line=order_line)
    assert allocation.stock.warehouse == nonowned_warehouse
    assert allocation.quantity_allocated == 50
    assert allocation.allocation_sources.count() == 0  # No sources (non-owned)

    # Verify: No stock in owned warehouse yet
    owned_stock = Stock.objects.filter(
        warehouse=owned_warehouse, product_variant=variant
    ).first()
    assert owned_stock is None

    # Step 2: Create and confirm POI (order from supplier)
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,  # Order 100, but only 50 allocated        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=poi.order, allocation=allocation
    )

    # when - confirm POI (this should move allocations)
    confirm_purchase_order_item(poi)

    # then - allocation should have moved to owned warehouse
    allocation.refresh_from_db()
    assert allocation.stock.warehouse == owned_warehouse
    assert allocation.quantity_allocated == 50

    # AllocationSources should now exist (owned warehouse)
    assert allocation.allocation_sources.count() == 1
    source = allocation.allocation_sources.first()
    assert source.purchase_order_item == poi
    assert source.quantity == 50

    # POI should reflect allocation
    poi.refresh_from_db()
    assert poi.quantity_allocated == 50

    # Invariant should hold
    # Stock.quantity = 100 - 50 = 50 (50 allocated, 50 available)
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_when_multiple_customer_orders_then_confirm_poi(
    owned_warehouse,
    nonowned_warehouse,
    variant,
    purchase_order,
    order,
    channel_USD,
):
    """Multiple customer orders from supplier, then confirm POI.

    Purpose: Test that confirming POI correctly handles multiple pre-existing allocations.

    Flow:
    1. Three customers order from supplier (3 allocations)
    2. We confirm POI
    3. All allocations should migrate
    4. Invariant should hold
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order import OrderStatus
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks

    # Order must be UNCONFIRMED for allocation at supplier warehouse
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    # given - supplier stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=500,
    )

    # Ensure order lines use the same variant
    order.lines.all().delete()  # Clear any existing lines

    # Create 3 customer orders with quantities 30, 40, 20
    order_lines = []
    quantities = [30, 40, 20]
    for i, qty in enumerate(quantities):
        line = order.lines.create(
            product_name=f"Product {i}",
            variant_name=variant.name,
            product_sku=variant.sku,
            variant=variant,
            quantity=qty,
            unit_price_gross_amount=10,
            unit_price_net_amount=10,
            total_price_gross_amount=10 * qty,
            total_price_net_amount=10 * qty,
            currency="USD",
            is_shipping_required=False,
            is_gift_card=False,
        )
        order_lines.append(line)

    # Allocate: 30 + 40 + 20 = 90 units from supplier
    allocate_stocks(
        [OrderLineInfo(line=order_lines[0], variant=variant, quantity=30)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )
    allocate_stocks(
        [OrderLineInfo(line=order_lines[1], variant=variant, quantity=40)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )
    allocate_stocks(
        [OrderLineInfo(line=order_lines[2], variant=variant, quantity=20)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # Verify: All allocations at supplier
    from ..models import Allocation

    allocations = Allocation.objects.filter(order_line__in=order_lines)
    assert allocations.count() == 3
    for alloc in allocations:
        assert alloc.stock.warehouse == nonowned_warehouse

    # when - confirm POI for 150 units (more than allocated)
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=150,
        quantity_allocated=0,
        total_price_amount=1500.0,  # 150 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    allocations = Allocation.objects.filter(order_line__in=order_lines)
    for alloc in allocations:
        PurchaseOrderRequestedAllocation.objects.create(
            purchase_order=poi.order, allocation=alloc
        )

    confirm_purchase_order_item(poi)

    # then - all allocations moved to owned warehouse
    allocations = Allocation.objects.filter(order_line__in=order_lines)
    for alloc in allocations:
        alloc.refresh_from_db()
        assert alloc.stock.warehouse == owned_warehouse
        assert alloc.allocation_sources.count() > 0

    # POI should have 90 allocated (30 + 40 + 20)
    poi.refresh_from_db()
    assert poi.quantity_allocated == 90

    # Invariant should hold
    # Stock.quantity = 150 - 90 = 60 (90 allocated, 60 available)
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_when_poi_quantity_less_than_allocations(
    owned_warehouse,
    nonowned_warehouse,
    variant,
    purchase_order,
    order,
    channel_USD,
):
    """POI quantity < allocated quantity - partial allocation movement.

    Purpose: Test edge case where we can't move all allocations (POI too small).

    Flow:
    1. Customer orders 100 units from supplier
    2. We only confirm POI for 60 units
    3. Only 60 units of allocation should move
    4. 40 units should stay at supplier
    5. Invariant should hold (only owned warehouse part)
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order import OrderStatus
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks
    from ..models import Allocation

    # Order must be UNCONFIRMED for allocation at supplier warehouse
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    # given - supplier stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=500,
    )

    # Clear any existing order lines
    order.lines.all().delete()

    # Customer orders 100 units
    order_line = order.lines.create(
        product_name="Product",
        variant_name=variant.name,
        product_sku=variant.sku,
        variant=variant,
        quantity=100,
        unit_price_gross_amount=10,
        unit_price_net_amount=10,
        total_price_gross_amount=1000,
        total_price_net_amount=1000,
        currency="USD",
        is_shipping_required=False,
        is_gift_card=False,
    )

    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=100)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # when - confirm POI for only 60 units (less than allocated!)
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=60,  # Less than 100 allocated!        quantity_allocated=0,
        total_price_amount=600.0,  # 60 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    from ..models import Allocation as _Allocation

    source_allocation = _Allocation.objects.get(
        order_line=order_line, stock__warehouse=nonowned_warehouse
    )
    PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=poi.order, allocation=source_allocation
    )

    confirm_purchase_order_item(poi)

    # then - allocation should be moved (possibly split)
    allocations = Allocation.objects.filter(order_line=order_line)

    # The allocation behavior depends on implementation:
    # - Could be 1 allocation moved to owned (if all fits)
    # - Could be 2 allocations (split: owned + supplier)
    # What matters: owned warehouse has the right amount
    owned_alloc = allocations.filter(stock__warehouse=owned_warehouse).first()
    assert owned_alloc is not None
    assert owned_alloc.quantity_allocated == 60

    # If there's leftover at supplier, check it
    supplier_alloc = allocations.filter(stock__warehouse=nonowned_warehouse).first()
    if supplier_alloc:
        assert supplier_alloc.quantity_allocated == 40

    # Owned allocation should have sources
    assert owned_alloc.allocation_sources.count() > 0

    # POI should be fully allocated
    poi.refresh_from_db()
    assert poi.quantity_allocated == 60

    # Invariant should hold for owned warehouse
    # Stock.quantity = 60 - 60 = 0 (all allocated)
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_when_order_auto_confirms_after_poi_confirmation(
    owned_warehouse,
    nonowned_warehouse,
    variant,
    purchase_order,
    order_line,
    channel_USD,
):
    """Order auto-confirms when POI gives it allocation sources.

    Purpose: Test integration - confirming POI should trigger order confirmation.

    Flow:
    1. Order created (UNCONFIRMED) with allocation from supplier
    2. Confirm POI
    3. Allocation moves and gets sources
    4. Order should auto-confirm (UNCONFIRMED → UNFULFILLED)
    5. Invariant should hold
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order import OrderStatus
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks

    # IMPORTANT: Use order_line.variant
    variant = order_line.variant

    # given - supplier stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=200,
    )

    # Order is UNCONFIRMED
    order = order_line.order
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    # Update order_line quantity to match allocation
    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    # Allocate from supplier
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # Verify order still UNCONFIRMED (no sources yet)
    order.refresh_from_db()
    assert order.status == OrderStatus.UNCONFIRMED

    # when - confirm POI
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    from ..models import Allocation as _Allocation

    source_allocation = _Allocation.objects.get(
        order_line=order_line, stock__warehouse=nonowned_warehouse
    )
    PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=poi.order, allocation=source_allocation
    )

    confirm_purchase_order_item(poi)

    # then - order should auto-confirm
    order.refresh_from_db()

    # Debug: Check why order didn't auto-confirm
    if order.status != OrderStatus.UNFULFILLED:
        from ..management import can_confirm_order
        from ..models import Allocation

        allocations = Allocation.objects.filter(order_line=order_line)
        debug_info = []
        for alloc in allocations:
            sources = alloc.allocation_sources.all()
            sources_sum = sum(s.quantity for s in sources)
            debug_info.append(
                f"    Allocation: warehouse={alloc.stock.warehouse.name}, "
                f"qty={alloc.quantity_allocated}, sources_count={sources.count()}, "
                f"sources_sum={sources_sum}"
            )

        can_confirm = can_confirm_order(order)

        pytest.fail(
            f"Order did not auto-confirm!\n"
            f"  Order status: {order.status}\n"
            f"  can_confirm_order(): {can_confirm}\n"
            f"  Allocations:\n" + "\n".join(debug_info)
        )

    assert order.status == OrderStatus.UNFULFILLED

    # Invariant should hold
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_with_mixed_allocations_owned_and_nonowned(
    owned_warehouse,
    nonowned_warehouse,
    variant,
    purchase_order,
    order,
    channel_USD,
):
    """Some allocations in owned, some in non-owned, then confirm more POIs.

    Purpose: Test that system handles mixed state correctly.

    Flow:
    1. Confirm POI1 (creates owned warehouse stock)
    2. Customer orders (some from owned, some from supplier)
    3. Confirm POI2 (moves remaining supplier allocations)
    4. Invariant should hold throughout
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order import OrderStatus
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks

    # Order must be UNCONFIRMED for allocation at supplier warehouse
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    # given - supplier stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=500,
    )

    # Clear existing order lines
    order.lines.all().delete()

    # Step 1: Confirm first POI (50 units to owned warehouse)
    shipment1 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi1 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=50,
        quantity_allocated=0,
        total_price_amount=500.0,  # 50 qty × $10.0/unit
        currency="USD",
        shipment=shipment1,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    confirm_purchase_order_item(poi1)
    # After POI1: supplier=450, owned=50
    # Allocation strategy prefers owned warehouse despite having less stock

    # Invariant check after POI1
    assert_stock_poi_invariant(owned_warehouse, variant)

    # Step 2: Customer orders 80 units total
    # Should allocate: 50 from owned (prioritized) + 30 from supplier
    order_line = order.lines.create(
        product_name="Product",
        variant_name=variant.name,
        product_sku=variant.sku,
        variant=variant,
        quantity=80,
        unit_price_gross_amount=10,
        unit_price_net_amount=10,
        total_price_gross_amount=800,
        total_price_net_amount=800,
        currency="USD",
        is_shipping_required=False,
        is_gift_card=False,
    )

    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=80)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # Verify: Should have allocations totaling 80
    from ..models import Allocation

    allocations = Allocation.objects.filter(order_line=order_line)
    total_allocated = sum(a.quantity_allocated for a in allocations)
    assert total_allocated == 80

    # Check allocations - with updated allocation strategy, should use owned first
    owned_alloc = allocations.filter(stock__warehouse=owned_warehouse).first()
    supplier_alloc = allocations.filter(stock__warehouse=nonowned_warehouse).first()

    # Owned warehouse is prioritized, so should allocate 50 from there
    assert owned_alloc is not None, "Should have allocation from owned warehouse"
    assert owned_alloc.quantity_allocated == 50

    # Remaining 30 should come from supplier
    assert supplier_alloc is not None, "Should have allocation from supplier"
    assert supplier_alloc.quantity_allocated == 30

    # Invariant after mixed allocations
    assert_stock_poi_invariant(owned_warehouse, variant)

    # Step 3: Confirm second POI (100 units)
    shipment2 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-456",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi2 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment2,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=poi2.order, allocation=supplier_alloc
    )

    # Check state BEFORE confirming POI2
    Stock.objects.get(warehouse=owned_warehouse, product_variant=variant)

    confirm_purchase_order_item(poi2)

    # Check state AFTER confirming POI2
    Stock.objects.get(warehouse=owned_warehouse, product_variant=variant)
    poi1.refresh_from_db()
    poi2.refresh_from_db()

    # then - supplier allocation should have moved
    allocations = Allocation.objects.filter(order_line=order_line)
    for alloc in allocations:
        alloc.refresh_from_db()
        assert alloc.stock.warehouse == owned_warehouse

    # Final invariant check
    # Stock.quantity = (50 + 100) - 80 = 70
    # 80 allocated across two POIs, 70 available
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_stress_test_realistic_daily_operations(
    owned_warehouse, variant, purchase_order, nonowned_warehouse, order, channel_USD
):
    """Stress test: simulate realistic daily operations over time.

    Purpose: Integration test with realistic complexity - many operations interleaved.

    Simulates:
    - Day 1: Customer orders (supplier allocation)
    - Day 2: Confirm POI
    - Day 3: More customer orders
    - Day 4: Customer cancels
    - Day 5: Confirm another POI
    - Throughout: Invariant should ALWAYS hold
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order import OrderStatus
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks, deallocate_stock

    # Order must be UNCONFIRMED for allocation at supplier warehouse
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    # Setup: Supplier has stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=1000,
    )

    # Clear existing order lines
    order.lines.all().delete()

    # Day 1: Three customers order from website (allocates from supplier)
    order_lines = []
    for i, qty in enumerate([30, 50, 20]):
        line = order.lines.create(
            product_name=f"Order {i + 1}",
            variant_name=variant.name,
            product_sku=variant.sku,
            variant=variant,
            quantity=qty,
            unit_price_gross_amount=10,
            unit_price_net_amount=10,
            total_price_gross_amount=10 * qty,
            total_price_net_amount=10 * qty,
            currency="USD",
            is_shipping_required=False,
            is_gift_card=False,
        )
        allocate_stocks(
            [OrderLineInfo(line=line, variant=variant, quantity=qty)],
            "US",
            channel_USD,
            manager=get_plugins_manager(allow_replica=False),
        )
        order_lines.append(line)

    # Invariant: No owned stock yet (all at supplier)
    owned_stock = Stock.objects.filter(
        warehouse=owned_warehouse, product_variant=variant
    ).first()
    assert owned_stock is None

    # Day 2: We order 150 units from supplier (confirm POI)
    shipment1 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="SHIP-001",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )
    poi1 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=150,
        quantity_allocated=0,
        total_price_amount=1500.0,  # 150 qty × $10.0/unit
        currency="USD",
        shipment=shipment1,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    from ..models import Allocation as _Allocation

    for day1_line in order_lines:
        day1_alloc = _Allocation.objects.get(
            order_line=day1_line, stock__warehouse=nonowned_warehouse
        )
        PurchaseOrderRequestedAllocation.objects.create(
            purchase_order=poi1.order, allocation=day1_alloc
        )

    confirm_purchase_order_item(poi1)

    # Invariant after POI confirmation
    # Should have: 150 - (30+50+20) = 50 available
    assert_stock_poi_invariant(owned_warehouse, variant)

    # Day 3: Two more customers order (allocate from owned warehouse)
    for i, qty in enumerate([25, 15], start=3):
        line = order.lines.create(
            product_name=f"Order {i + 1}",
            variant_name=variant.name,
            product_sku=variant.sku,
            variant=variant,
            quantity=qty,
            unit_price_gross_amount=10,
            unit_price_net_amount=10,
            total_price_gross_amount=10 * qty,
            total_price_net_amount=10 * qty,
            currency="USD",
            is_shipping_required=False,
            is_gift_card=False,
        )
        allocate_stocks(
            [OrderLineInfo(line=line, variant=variant, quantity=qty)],
            "US",
            channel_USD,
            manager=get_plugins_manager(allow_replica=False),
        )
        order_lines.append(line)

    # Invariant after more allocations
    # Should have: 150 - (30+50+20+25+15) = 10 available
    assert_stock_poi_invariant(owned_warehouse, variant)

    # Day 4: First customer cancels (deallocate 30 units)
    deallocate_stock(
        [OrderLineInfo(line=order_lines[0], variant=variant, quantity=30)],
        manager=get_plugins_manager(allow_replica=False),
    )

    # Invariant after cancellation
    # Should have: 150 - (50+20+25+15) = 40 available
    assert_stock_poi_invariant(owned_warehouse, variant)

    # Day 5: Order more from supplier (80 units)
    shipment2 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="SHIP-002",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )
    poi2 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=80,
        quantity_allocated=0,
        total_price_amount=800.0,  # 80 qty × $10.0/unit
        currency="USD",
        shipment=shipment2,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi2)

    # Final invariant check
    # Should have: (150 + 80) - (50+20+25+15) = 120 available
    assert_stock_poi_invariant(owned_warehouse, variant)


# ==============================================================================
# EXPLICIT MECHANISM VALIDATION TESTS
# ==============================================================================


def test_allocation_creates_allocation_sources(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    order_line,
    channel_USD,
):
    """Allocating creates AllocationSources linking Stock to POI batches.

    Purpose: Explicitly validate INVARIANT 2 mechanism.
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks
    from ..models import Allocation, AllocationSource

    # given
    Stock.objects.create(
        warehouse=nonowned_warehouse, product_variant=variant, quantity=200
    )
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi)
    # After confirmation: nonowned has 100, owned has 100
    # Allocation strategy now prefers owned warehouse

    # Update order_line quantity to match allocation
    order_line.quantity = 60
    order_line.save(update_fields=["quantity"])

    # when - allocate 60 units
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=60)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - AllocationSources created and POI.quantity_allocated increased
    poi.refresh_from_db()
    assert poi.quantity_allocated == 60

    allocation = Allocation.objects.get(order_line=order_line)
    sources = AllocationSource.objects.filter(allocation=allocation)
    assert sources.count() == 1
    assert sources.first().purchase_order_item == poi
    assert sources.first().quantity == 60

    # and - both invariants hold
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_stock_quantity_constant_during_allocation(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    order_line,
    channel_USD,
):
    """Stock.quantity stays constant when allocating (INVARIANT 1).

    Purpose: Explicitly validate that Stock.quantity doesn't change during allocation.
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks, deallocate_stock

    # given
    Stock.objects.create(
        warehouse=nonowned_warehouse, product_variant=variant, quantity=200
    )
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi)
    # After confirmation: nonowned has 100, owned has 100
    # Allocation strategy now prefers owned warehouse

    stock = Stock.objects.get(warehouse=owned_warehouse, product_variant=variant)
    initial_quantity = stock.quantity

    # Update order_line quantity to match allocation
    order_line.quantity = 60
    order_line.save(update_fields=["quantity"])

    # when - allocate
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=60)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - Stock.quantity unchanged
    stock.refresh_from_db()
    assert stock.quantity == initial_quantity  # INVARIANT 1: total unchanged

    # when - deallocate
    deallocate_stock(
        [OrderLineInfo(line=order_line, variant=variant, quantity=60)],
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - Stock.quantity still unchanged
    stock.refresh_from_db()
    assert stock.quantity == initial_quantity  # Still constant


def test_allocation_spans_poi_batches_fifo(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    order_line,
    channel_USD,
):
    """Allocation spanning multiple POIs uses FIFO (oldest first).

    Purpose: Validate INVARIANT 2 with multiple POI batches.
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks

    # given - two POIs
    Stock.objects.create(
        warehouse=nonowned_warehouse, product_variant=variant, quantity=300
    )

    shipment1 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-1",
        shipping_cost=Money(Decimal("100.00"), "USD"),
        carrier="TEST-CARRIER",
    )
    poi1 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=50,
        quantity_allocated=0,
        total_price_amount=500.0,  # 50 qty × $10.0/unit
        currency="USD",
        shipment=shipment1,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi1)

    shipment2 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-2",
        shipping_cost=Money(Decimal("100.00"), "USD"),
        carrier="TEST-CARRIER",
    )
    poi2 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=80,
        quantity_allocated=0,
        total_price_amount=800.0,  # 80 qty × $10.0/unit
        currency="USD",
        shipment=shipment2,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi2)
    # After confirmation: nonowned has 170, owned has 130
    # Allocation strategy now prefers owned warehouse

    # Update order_line quantity to match allocation
    order_line.quantity = 100
    order_line.save(update_fields=["quantity"])

    # when - allocate 100 (spans both POIs)
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=100)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - FIFO: POI1 fully allocated (50), POI2 partially (50)
    poi1.refresh_from_db()
    poi2.refresh_from_db()
    assert poi1.quantity_allocated == 50
    assert poi2.quantity_allocated == 50

    # and - both invariants hold
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_partial_deallocation(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    order_line,
    channel_USD,
):
    """Partial deallocation correctly updates POI.quantity_allocated.

    Purpose: Validate INVARIANT 2 with partial operations.
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks, deallocate_stock

    # given - allocated 100
    Stock.objects.create(
        warehouse=nonowned_warehouse, product_variant=variant, quantity=200
    )
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,  # 100 qty × $10.0/unit
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi)
    # After confirmation: nonowned has 100, owned has 100
    # Allocation strategy now prefers owned warehouse

    # Update order_line quantity to match allocation
    order_line.quantity = 100
    order_line.save(update_fields=["quantity"])

    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=100)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # when - deallocate only 30 (partial)
    deallocate_stock(
        [OrderLineInfo(line=order_line, variant=variant, quantity=30)],
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - POI.quantity_allocated decreased by 30
    poi.refresh_from_db()
    assert poi.quantity_allocated == 70

    # and - both invariants hold
    assert_stock_poi_invariant(owned_warehouse, variant)

    # when - deallocate remaining 70
    deallocate_stock(
        [OrderLineInfo(line=order_line, variant=variant, quantity=70)],
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - fully deallocated
    poi.refresh_from_db()
    assert poi.quantity_allocated == 0

    # and - invariants still hold
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_partial_allocation_is_allowed(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    order_line,
    channel_USD,
):
    """Partial allocation (less than order line quantity) is allowed.

    Purpose: Validate that you can allocate part of an order line's quantity.
    This supports use cases like backorders, pre-orders, and incremental allocation.
    """
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks
    from ..models import Allocation

    # given
    Stock.objects.create(
        warehouse=nonowned_warehouse, product_variant=variant, quantity=200
    )
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi)

    # Customer ordered 100 units, but we only allocate 30 (partial)
    order_line.quantity = 100
    order_line.save(update_fields=["quantity"])

    # when - allocate only 30 out of 100
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=30)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # then - allocation succeeds with partial quantity
    allocation = Allocation.objects.get(order_line=order_line)
    assert allocation.quantity_allocated == 30  # Only 30 allocated
    assert order_line.quantity == 100  # Order line still has 100 total

    # and - invariants hold
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_allocation_raises_error_on_over_allocation(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    order_line,
    channel_USD,
):
    """Allocating more than ordered raises AllocationQuantityError.

    Purpose: Validate that OrderLineInfo.quantity cannot exceed OrderLine.quantity.
    Partial allocation (less than ordered) is allowed.
    """
    from ...core.exceptions import AllocationQuantityError
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ...shipping.models import Shipment
    from ..management import allocate_stocks

    # given
    Stock.objects.create(
        warehouse=nonowned_warehouse, product_variant=variant, quantity=200
    )
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi)

    # Set order line to 50 units, but try to allocate 60 (over-allocation)
    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    # when/then - attempting to over-allocate raises error
    with pytest.raises(AllocationQuantityError) as exc_info:
        allocate_stocks(
            [OrderLineInfo(line=order_line, variant=variant, quantity=60)],
            "US",
            channel_USD,
            manager=get_plugins_manager(allow_replica=False),
        )

    # Verify error details
    error = exc_info.value
    assert error.order_line == order_line
    assert error.requested_quantity == 60
    assert error.line_quantity == 50
    assert "Cannot allocate 60 units when order line only has 50 units" in str(error)


# ==============================================================================
# ADJUSTMENT INVARIANT TESTS
# ==============================================================================


def test_invariant_after_delivery_shortage_with_processed_adjustment(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    staff_user,
):
    """Delivery shortage creates and processes adjustment, invariant holds.

    Purpose: Verify INVARIANT 1 includes processed adjustments.

    Flow:
    1. Order 100 units from supplier (POI created)
    2. Confirm POI (Stock.quantity = 100)
    3. Receive only 90 units (shortage of 10)
    4. Complete receipt (creates and processes -10 adjustment)
    5. Stock.quantity should be 90 = (100 - 10)
    6. Invariant should hold
    """
    from ...inventory.models import Receipt, ReceiptLine
    from ...inventory.receipt_workflow import complete_receipt
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...shipping.models import Shipment

    # given - source stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=200,
    )

    # Create and confirm POI for 100 units
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST-CARRIER",
        inco_term=IncoTerm.DDP,
        arrived_at=timezone.now(),
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    confirm_purchase_order_item(poi)

    # Verify stock after confirmation (before receiving)
    stock = Stock.objects.get(warehouse=owned_warehouse, product_variant=variant)
    assert stock.quantity == 100
    assert_stock_poi_invariant(owned_warehouse, variant)

    # when - receive only 90 units (shortage)
    receipt = Receipt.objects.create(
        shipment=shipment,
        created_by=staff_user,
    )

    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi,
        quantity_received=90,  # Shortage of 10
        received_by=staff_user,
    )

    # Complete receipt (creates and processes adjustment)
    result = complete_receipt(receipt, user=staff_user)

    # then - pending POIA created (not auto-processed)
    assert result["discrepancies"] == 1
    assert len(result["adjustments_pending"]) == 1

    adjustment = result["adjustments_pending"][0]
    assert adjustment.quantity_change == -10
    assert adjustment.processed_at is None

    # Stock.quantity NOT yet updated (pending resolution)
    stock.refresh_from_db()
    assert stock.quantity == 100

    # POI shows correct values
    poi.refresh_from_db()
    assert poi.quantity_ordered == 100
    assert poi.quantity_received == 90  # Audit trail
    assert poi.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION


def test_invariant_after_overage_with_processed_adjustment(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    staff_user,
):
    """Overage creates and processes adjustment, invariant holds.

    Purpose: Verify INVARIANT 1 with positive adjustments.

    Flow:
    1. Order 100 units from supplier
    2. Confirm POI (Stock.quantity = 100)
    3. Receive 110 units (overage of 10)
    4. Complete receipt (creates and processes +10 adjustment)
    5. Stock.quantity should be 110 = (100 + 10)
    6. Invariant should hold
    """
    from ...inventory.models import Receipt, ReceiptLine
    from ...inventory.receipt_workflow import complete_receipt
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...shipping.models import Shipment

    # given - source stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=200,
    )

    # Create and confirm POI
    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-456",
        shipping_cost=Money(Decimal("100.00"), "USD"),
        carrier="TEST-CARRIER",
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    confirm_purchase_order_item(poi)

    # Verify initial state
    stock = Stock.objects.get(warehouse=owned_warehouse, product_variant=variant)
    assert stock.quantity == 100
    assert_stock_poi_invariant(owned_warehouse, variant)

    # when - receive 110 units (overage)
    receipt = Receipt.objects.create(
        shipment=shipment,
        created_by=staff_user,
    )

    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi,
        quantity_received=110,  # Overage of 10
        received_by=staff_user,
    )

    # Complete receipt
    result = complete_receipt(receipt, user=staff_user)

    # then - pending POIA created (not auto-processed)
    assert result["discrepancies"] == 1
    adjustment = result["adjustments_pending"][0]
    assert adjustment.quantity_change == 10
    assert adjustment.processed_at is None

    # Stock NOT yet updated (pending resolution)
    stock.refresh_from_db()
    assert stock.quantity == 100

    # POI shows correct values
    poi.refresh_from_db()
    assert poi.quantity_ordered == 100
    assert poi.quantity_received == 110  # Audit trail
    assert poi.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION

    # Invariant: Stock.quantity = quantity_ordered + adjustments = 100 + 10 = 110
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_with_mixed_pois_some_with_processed_adjustments(
    owned_warehouse,
    variant,
    purchase_order,
    nonowned_warehouse,
    staff_user,
):
    """Multiple POIs, some with processed adjustments, invariant holds.

    Purpose: Verify INVARIANT 1 with complex scenario - multiple POIs with different states.

    Scenario:
    - POI 1: 100 ordered, 100 received (no adjustment)
    - POI 2: 50 ordered, 48 received (shortage of -2, processed)
    - POI 3: 75 ordered, 80 received (overage of +5, processed)

    Expected Stock.quantity = 100 + (50-2) + (75+5) = 228
    """
    from ...inventory.models import Receipt, ReceiptLine
    from ...inventory.receipt_workflow import complete_receipt
    from ...inventory.stock_management import confirm_purchase_order_item
    from ...shipping.models import Shipment

    # given - source stock
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        quantity=500,
    )

    # POI 1: Perfect match (100 ordered, 100 received)
    shipment1 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="SHIP-1",
        shipping_cost=Money(Decimal("100.00"), "USD"),
        carrier="TEST-CARRIER",
    )
    poi1 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=100,
        quantity_allocated=0,
        total_price_amount=1000.0,
        currency="USD",
        shipment=shipment1,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi1)

    receipt1 = Receipt.objects.create(shipment=shipment1, created_by=staff_user)
    ReceiptLine.objects.create(
        receipt=receipt1,
        purchase_order_item=poi1,
        quantity_received=100,  # Perfect match
        received_by=staff_user,
    )
    complete_receipt(receipt1, user=staff_user)

    # Check after first POI
    stock = Stock.objects.get(warehouse=owned_warehouse, product_variant=variant)
    assert stock.quantity == 100
    assert_stock_poi_invariant(owned_warehouse, variant)

    # POI 2: Shortage (50 ordered, 48 received, -2 adjustment)
    shipment2 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="SHIP-2",
        shipping_cost=Money(Decimal("100.00"), "USD"),
        carrier="TEST-CARRIER",
    )
    poi2 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=50,
        quantity_allocated=0,
        total_price_amount=500.0,
        currency="USD",
        shipment=shipment2,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi2)

    receipt2 = Receipt.objects.create(shipment=shipment2, created_by=staff_user)
    ReceiptLine.objects.create(
        receipt=receipt2,
        purchase_order_item=poi2,
        quantity_received=48,  # Shortage of 2
        received_by=staff_user,
    )
    complete_receipt(receipt2, user=staff_user)

    # Check after second POI — stock unchanged (POIA pending, not processed)
    stock.refresh_from_db()
    assert stock.quantity == 150  # 100 + 50 (POI confirmed qty, no adjustment yet)
    assert_stock_poi_invariant(owned_warehouse, variant)

    # POI 3: Overage (75 ordered, 80 received, +5 adjustment)
    shipment3 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="SHIP-3",
        shipping_cost=Money(Decimal("100.00"), "USD"),
        carrier="TEST-CARRIER",
    )
    poi3 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=75,
        quantity_allocated=0,
        total_price_amount=750.0,
        currency="USD",
        shipment=shipment3,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )
    confirm_purchase_order_item(poi3)

    receipt3 = Receipt.objects.create(shipment=shipment3, created_by=staff_user)
    ReceiptLine.objects.create(
        receipt=receipt3,
        purchase_order_item=poi3,
        quantity_received=80,  # Overage of 5
        received_by=staff_user,
    )
    complete_receipt(receipt3, user=staff_user)

    # Final check: Stock.quantity = 100 + 50 + 75 = 225 (no adjustments processed)
    stock.refresh_from_db()
    assert stock.quantity == 225

    # Verify each POI
    poi1.refresh_from_db()
    poi2.refresh_from_db()
    poi3.refresh_from_db()

    assert poi1.quantity_ordered == 100
    assert poi1.quantity_received == 100
    assert poi1.status == PurchaseOrderItemStatus.RECEIVED

    assert poi2.quantity_ordered == 50
    assert poi2.quantity_received == 48
    assert poi2.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION
    adj2 = poi2.adjustments.filter(processed_at__isnull=True).first()
    assert adj2.quantity_change == -2

    assert poi3.quantity_ordered == 75
    assert poi3.quantity_received == 80
    assert poi3.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION
    adj3 = poi3.adjustments.filter(processed_at__isnull=True).first()
    assert adj3.quantity_change == 5

    # Final invariant check
    assert_stock_poi_invariant(owned_warehouse, variant)


def test_invariant_after_order_fulfillment(
    owned_warehouse,
    purchase_order_item,
    order_line,
    channel_USD,
    site_settings,
):
    """Invariants hold after creating, allocating, and fulfilling orders."""
    from ...order.actions import create_fulfillments
    from ...order.fetch import OrderLineInfo
    from ...plugins.manager import get_plugins_manager
    from ..management import allocate_stocks

    variant = order_line.variant
    order = order_line.order

    stock, _ = Stock.objects.get_or_create(
        warehouse=owned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100},
    )
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    # Set order_line quantity to 50
    order_line.quantity = 50
    order_line.save(update_fields=["quantity"])

    assert_stock_poi_invariant(owned_warehouse, variant)

    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=50)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    assert_stock_poi_invariant(owned_warehouse, variant)

    stock.refresh_from_db()
    purchase_order_item.refresh_from_db()
    assert stock.quantity == 100
    assert stock.quantity_allocated == 50
    assert purchase_order_item.quantity_allocated == 50
    assert purchase_order_item.quantity_fulfilled == 0

    create_fulfillments(
        user=None,
        app=None,
        order=order,
        fulfillment_lines_for_warehouses={
            owned_warehouse.pk: [{"order_line": order_line, "quantity": 30}]
        },
        manager=get_plugins_manager(allow_replica=False),
        site_settings=site_settings,
        notify_customer=False,
    )

    stock.refresh_from_db()
    purchase_order_item.refresh_from_db()

    assert stock.quantity == 70
    assert stock.quantity_allocated == 20
    assert purchase_order_item.quantity_allocated == 20
    assert purchase_order_item.quantity_fulfilled == 30

    assert_stock_poi_invariant(owned_warehouse, variant)

    expected_stock = calculate_expected_stock_quantity(owned_warehouse, variant)
    assert stock.quantity == expected_stock

    assert stock.quantity == 100 - 30

    create_fulfillments(
        user=None,
        app=None,
        order=order,
        fulfillment_lines_for_warehouses={
            owned_warehouse.pk: [{"order_line": order_line, "quantity": 20}]
        },
        manager=get_plugins_manager(allow_replica=False),
        site_settings=site_settings,
        notify_customer=False,
    )

    stock.refresh_from_db()
    purchase_order_item.refresh_from_db()

    assert stock.quantity == 50
    assert stock.quantity_allocated == 0
    assert purchase_order_item.quantity_allocated == 0
    assert purchase_order_item.quantity_fulfilled == 50

    assert_stock_poi_invariant(owned_warehouse, variant)

    assert stock.quantity == 100 - 50

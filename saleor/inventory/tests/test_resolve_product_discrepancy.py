"""Tests for resolve_product_discrepancy and get_product_discrepancies."""

from decimal import Decimal

import pytest
from django.db.models import Sum

from ...order import OrderOrigin
from ...order.models import Order, OrderLine
from ...warehouse.models import Allocation, AllocationSource, Stock
from .. import PurchaseOrderItemStatus, ReceiptStatus
from ..models import (
    PurchaseOrderItem,
    PurchaseOrderItemAdjustment,
    Receipt,
    ReceiptLine,
)
from ..receipt_workflow import (
    complete_receipt,
    get_product_discrepancies,
    resolve_product_discrepancy,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def variant_a(product_variant_factory):
    return product_variant_factory(sku="RESOLVE-A")


@pytest.fixture
def variant_b(product_variant_factory):
    return product_variant_factory(sku="RESOLVE-B")


@pytest.fixture
def poi_a(purchase_order, variant_a, shipment, nonowned_warehouse, completed_receipt):
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_a,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_a,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
    )
    ReceiptLine.objects.create(
        receipt=completed_receipt,
        purchase_order_item=poi,
        quantity_received=8,
    )
    return poi


@pytest.fixture
def poi_b(purchase_order, variant_b, shipment, nonowned_warehouse, completed_receipt):
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_b,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_b,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
    )
    ReceiptLine.objects.create(
        receipt=completed_receipt,
        purchase_order_item=poi,
        quantity_received=12,
    )
    return poi


@pytest.fixture
def stock_a(owned_warehouse, variant_a):
    return Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_a,
        quantity=20,
        quantity_allocated=0,
    )


@pytest.fixture
def stock_b(owned_warehouse, variant_b):
    return Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_b,
        quantity=20,
        quantity_allocated=0,
    )


@pytest.fixture
def completed_receipt(shipment, staff_user):
    return Receipt.objects.create(
        shipment=shipment,
        status=ReceiptStatus.COMPLETED,
        created_by=staff_user,
    )


@pytest.fixture
def poia_a(poi_a, staff_user):
    return PurchaseOrderItemAdjustment.objects.create(
        purchase_order_item=poi_a,
        quantity_change=-2,
        reason="delivery_short",
        affects_payable=True,
        created_by=staff_user,
    )


@pytest.fixture
def poia_b(poi_b, staff_user):
    return PurchaseOrderItemAdjustment.objects.create(
        purchase_order_item=poi_b,
        quantity_change=2,
        reason="cycle_count_pos",
        affects_payable=False,
        created_by=staff_user,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_order(channel_USD, address):
    from ...order import OrderStatus

    return Order.objects.create(
        channel=channel_USD,
        billing_address=address,
        shipping_address=address,
        status=OrderStatus.UNCONFIRMED,
        origin=OrderOrigin.CHECKOUT,
        lines_count=1,
    )


def _make_line(order, variant, quantity):
    return OrderLine.objects.create(
        order=order,
        variant=variant,
        quantity=quantity,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal(str(quantity * 10)),
        total_price_net_amount=Decimal(str(quantity * 10)),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
    )


def _make_alloc_source(poi, order_line, stock, quantity):
    alloc, _ = Allocation.objects.get_or_create(
        order_line=order_line,
        stock=stock,
        defaults={"quantity_allocated": 0},
    )
    alloc.quantity_allocated += quantity
    alloc.save(update_fields=["quantity_allocated"])
    stock.quantity_allocated += quantity
    stock.save(update_fields=["quantity_allocated"])
    poi.quantity_allocated += quantity
    poi.save(update_fields=["quantity_allocated"])
    return AllocationSource.objects.create(
        purchase_order_item=poi,
        allocation=alloc,
        quantity=quantity,
    )


def _total_allocated_for_order(order):
    return (
        AllocationSource.objects.filter(allocation__order_line__order=order).aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )


# ---------------------------------------------------------------------------
# Tests — resolve_product_discrepancy
# ---------------------------------------------------------------------------


def test_resolve_removal_shorts_order(
    channel_USD,
    purchase_order,
    poi_a,
    poia_a,
    stock_a,
    variant_a,
    owned_warehouse,
    completed_receipt,
    staff_user,
):
    """Resolve a shortage by removing allocation — order gets shorted."""
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)

    line = _make_line(order, variant_a, 10)
    _make_alloc_source(poi_a, line, stock_a, 10)

    # when: resolve by giving order only 8 (matching received)
    result = resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[{"order": order, "variant": variant_a, "quantity": 8}],
        affects_payable=True,
        user=staff_user,
    )

    # then: POIA is marked processed
    assert len(result) == 1
    assert result[0].processed_at is not None
    assert result[0].affects_payable is True

    # and: order has 8 allocated
    assert _total_allocated_for_order(order) == 8

    # and: order line quantity updated
    line.refresh_from_db()
    assert line.quantity == 8

    # and: POI transitioned to RECEIVED
    poi_a.refresh_from_db()
    assert poi_a.status == PurchaseOrderItemStatus.RECEIVED

    # and: stock invariant holds
    stock_a.refresh_from_db()
    assert stock_a.quantity_allocated == 8


def test_resolve_substitute_variant(
    channel_USD,
    purchase_order,
    poi_a,
    poi_b,
    poia_a,
    poia_b,
    stock_a,
    stock_b,
    variant_a,
    variant_b,
    owned_warehouse,
    completed_receipt,
    staff_user,
):
    """Resolve by substituting: order had 10 A, give them 8 A + 2 B."""
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)

    line = _make_line(order, variant_a, 10)
    _make_alloc_source(poi_a, line, stock_a, 10)

    # when: substitute — keep 8 A, add 2 B
    result = resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[
            {"order": order, "variant": variant_a, "quantity": 8},
            {"order": order, "variant": variant_b, "quantity": 2},
        ],
        affects_payable=False,
        user=staff_user,
    )

    # then: both POIAs processed
    assert len(result) == 2
    for adj in result:
        assert adj.processed_at is not None
        assert adj.affects_payable is False

    # and: order total is 10
    assert _total_allocated_for_order(order) == 10

    # and: A line reduced to 8, B line created with 2
    line.refresh_from_db()
    assert line.quantity == 8
    line_b = OrderLine.objects.get(order=order, variant=variant_b)
    assert line_b.quantity == 2

    # and: both POIs transitioned to RECEIVED
    poi_a.refresh_from_db()
    poi_b.refresh_from_db()
    assert poi_a.status == PurchaseOrderItemStatus.RECEIVED
    assert poi_b.status == PurchaseOrderItemStatus.RECEIVED


def test_resolve_full_substitute(
    channel_USD,
    purchase_order,
    poi_a,
    poi_b,
    poia_a,
    poia_b,
    stock_a,
    stock_b,
    variant_a,
    variant_b,
    owned_warehouse,
    completed_receipt,
    staff_user,
):
    """Full substitute: order had 10 A, give them 10 B instead."""
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)

    line = _make_line(order, variant_a, 10)
    _make_alloc_source(poi_a, line, stock_a, 10)

    # when: full substitute to B
    resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[
            {"order": order, "variant": variant_b, "quantity": 10},
        ],
        affects_payable=True,
        user=staff_user,
    )

    # then: A line deleted, B line created
    assert not OrderLine.objects.filter(pk=line.pk).exists()
    line_b = OrderLine.objects.get(order=order, variant=variant_b)
    assert line_b.quantity == 10
    assert _total_allocated_for_order(order) == 10


def test_resolve_multi_order(
    channel_USD,
    purchase_order,
    poi_a,
    poia_a,
    stock_a,
    variant_a,
    owned_warehouse,
    completed_receipt,
    staff_user,
):
    """Resolve a shortage across multiple orders — user picks who gets shorted."""
    addr = purchase_order.source_warehouse.address
    order_1 = _make_order(channel_USD, addr)
    order_2 = _make_order(channel_USD, addr)

    line_1 = _make_line(order_1, variant_a, 5)
    line_2 = _make_line(order_2, variant_a, 5)
    _make_alloc_source(poi_a, line_1, stock_a, 5)
    _make_alloc_source(poi_a, line_2, stock_a, 5)

    # when: 8 received — give 5 to order_1, 3 to order_2 (order_2 shorted)
    resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[
            {"order": order_1, "variant": variant_a, "quantity": 5},
            {"order": order_2, "variant": variant_a, "quantity": 3},
        ],
        affects_payable=True,
        user=staff_user,
    )

    # then: order_1 keeps 5, order_2 shorted to 3
    assert _total_allocated_for_order(order_1) == 5
    assert _total_allocated_for_order(order_2) == 3

    line_1.refresh_from_db()
    line_2.refresh_from_db()
    assert line_1.quantity == 5
    assert line_2.quantity == 3


def test_resolve_over_allocate_raises(
    channel_USD,
    purchase_order,
    poi_a,
    poia_a,
    stock_a,
    variant_a,
    owned_warehouse,
    completed_receipt,
    staff_user,
):
    """Cannot allocate more than what was received."""
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)

    line = _make_line(order, variant_a, 10)
    _make_alloc_source(poi_a, line, stock_a, 10)

    # when/then: trying to allocate 9 but only 8 received
    with pytest.raises(ValueError, match="Cannot allocate 9"):
        resolve_product_discrepancy(
            receipt=completed_receipt,
            product=variant_a.product,
            resolutions=[
                {"order": order, "variant": variant_a, "quantity": 9},
            ],
            affects_payable=True,
            user=staff_user,
        )


def test_resolve_no_pending_pois_raises(
    completed_receipt,
    variant_a,
    staff_user,
):
    """Raises when there are no REQUIRES_ATTENTION POIs for the product."""
    with pytest.raises(ValueError, match="No pending POIAs"):
        resolve_product_discrepancy(
            receipt=completed_receipt,
            product=variant_a.product,
            resolutions=[],
            affects_payable=True,
            user=staff_user,
        )


def test_resolve_sets_affects_payable(
    channel_USD,
    purchase_order,
    poi_a,
    poia_a,
    stock_a,
    variant_a,
    owned_warehouse,
    completed_receipt,
    staff_user,
):
    """affects_payable flag is propagated to POIAs."""
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)

    line = _make_line(order, variant_a, 10)
    _make_alloc_source(poi_a, line, stock_a, 10)

    result = resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[{"order": order, "variant": variant_a, "quantity": 8}],
        affects_payable=False,
        user=staff_user,
    )

    assert result[0].affects_payable is False


def test_resolve_with_no_existing_allocations(
    purchase_order,
    poi_a,
    poia_a,
    variant_a,
    owned_warehouse,
    completed_receipt,
    staff_user,
):
    """Resolving when there are no existing AllocationSources (e.g. standalone stock)."""
    # when: resolve with empty resolutions (accept the loss)
    result = resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[],
        affects_payable=True,
        user=staff_user,
    )

    # then: POIA processed, POI transitioned
    assert len(result) == 1
    assert result[0].processed_at is not None
    poi_a.refresh_from_db()
    assert poi_a.status == PurchaseOrderItemStatus.RECEIVED


# ---------------------------------------------------------------------------
# Tests — stock adjustment on resolve
# ---------------------------------------------------------------------------


def test_resolve_surplus_no_orders_increases_stock(
    purchase_order,
    variant_a,
    owned_warehouse,
    nonowned_warehouse,
    completed_receipt,
    staff_user,
    shipment,
):
    """Pure surplus with no orders — stock must increase by the discrepancy.

    Regression test: resolve_product_discrepancy previously marked the POIA as
    processed without adjusting stock, leaving the surplus quantity missing
    from the destination warehouse.
    """
    # given: POI ordered 1, received 999
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_a,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_a,
        quantity_ordered=1,
        total_price_amount=Decimal("10.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
    )
    ReceiptLine.objects.create(
        receipt=completed_receipt,
        purchase_order_item=poi,
        quantity_received=999,
    )
    PurchaseOrderItemAdjustment.objects.create(
        purchase_order_item=poi,
        quantity_change=998,
        reason="cycle_count_pos",
        affects_payable=True,
        created_by=staff_user,
    )
    stock = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_a,
        quantity=1,
        quantity_allocated=0,
    )

    # when
    resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[],
        affects_payable=True,
        user=staff_user,
    )

    # then: stock increased by 998 (the surplus)
    stock.refresh_from_db()
    assert stock.quantity == 999


def test_resolve_shortage_no_orders_decreases_stock(
    purchase_order,
    variant_a,
    owned_warehouse,
    nonowned_warehouse,
    completed_receipt,
    staff_user,
    shipment,
):
    """Pure shortage with no orders — stock must decrease by the discrepancy."""
    # given: POI ordered 10, received 7
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_a,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_a,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
    )
    ReceiptLine.objects.create(
        receipt=completed_receipt,
        purchase_order_item=poi,
        quantity_received=7,
    )
    PurchaseOrderItemAdjustment.objects.create(
        purchase_order_item=poi,
        quantity_change=-3,
        reason="delivery_short",
        affects_payable=True,
        created_by=staff_user,
    )
    stock = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_a,
        quantity=10,
        quantity_allocated=0,
    )

    # when
    resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[],
        affects_payable=True,
        user=staff_user,
    )

    # then: stock decreased by 3 (the shortage)
    stock.refresh_from_db()
    assert stock.quantity == 7


def test_resolve_surplus_with_orders_increases_unallocated_stock(
    channel_USD,
    purchase_order,
    variant_a,
    owned_warehouse,
    nonowned_warehouse,
    completed_receipt,
    staff_user,
    shipment,
):
    """Surplus with orders — orders keep their allocation, remaining surplus goes to stock."""
    # given: POI ordered 5, received 8 — order has 5 allocated
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_a,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_a,
        quantity_ordered=5,
        total_price_amount=Decimal("50.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
    )
    ReceiptLine.objects.create(
        receipt=completed_receipt,
        purchase_order_item=poi,
        quantity_received=8,
    )
    PurchaseOrderItemAdjustment.objects.create(
        purchase_order_item=poi,
        quantity_change=3,
        reason="cycle_count_pos",
        affects_payable=True,
        created_by=staff_user,
    )
    stock = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_a,
        quantity=5,
        quantity_allocated=0,
    )

    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)
    line = _make_line(order, variant_a, 5)
    _make_alloc_source(poi, line, stock, 5)

    # when: resolve — order keeps 5
    resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[{"order": order, "variant": variant_a, "quantity": 5}],
        affects_payable=True,
        user=staff_user,
    )

    # then: stock increased by 3 (the surplus) on top of the 5 already there
    stock.refresh_from_db()
    assert stock.quantity == 8
    assert stock.quantity_allocated == 5


def test_resolve_variant_swap_balanced_no_double_adjustment(
    channel_USD,
    purchase_order,
    poi_a,
    poi_b,
    poia_a,
    poia_b,
    stock_a,
    stock_b,
    variant_a,
    variant_b,
    owned_warehouse,
    completed_receipt,
    staff_user,
):
    """Variant swap where product total balances.

    Stock moves between variants but does not double-adjust.
    """
    # given: poi_a ordered=10 received=8 (POIA=-2)
    #        poi_b ordered=10 received=12 (POIA=+2)
    #        stock_a=20 stock_b=20, order has 10xA allocated
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)

    line = _make_line(order, variant_a, 10)
    _make_alloc_source(poi_a, line, stock_a, 10)

    stock_a_before = stock_a.quantity  # 20
    stock_b_before = stock_b.quantity  # 20

    # when: substitute — give order 8 A + 2 B
    resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[
            {"order": order, "variant": variant_a, "quantity": 8},
            {"order": order, "variant": variant_b, "quantity": 2},
        ],
        affects_payable=False,
        user=staff_user,
    )

    # then: stock_a decreased by 2 (shortage), stock_b increased by 2 (surplus)
    # _apply_reallocation handles -2 on A (alloc moved 10→8) and +2 on B (alloc 0→2)
    # The discrepancy is also -2 on A and +2 on B, so net additional adjustment = 0
    stock_a.refresh_from_db()
    stock_b.refresh_from_db()
    assert stock_a.quantity == stock_a_before - 2
    assert stock_b.quantity == stock_b_before + 2


# ---------------------------------------------------------------------------
# Tests — get_product_discrepancies
# ---------------------------------------------------------------------------


def test_get_product_discrepancies_returns_variant_breakdown(
    channel_USD,
    purchase_order,
    poi_a,
    poi_b,
    stock_a,
    stock_b,
    variant_a,
    variant_b,
    owned_warehouse,
    completed_receipt,
):
    """get_product_discrepancies returns per-variant ordered/received/delta."""
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)

    line_a = _make_line(order, variant_a, 10)
    _make_alloc_source(poi_a, line_a, stock_a, 10)

    results = get_product_discrepancies(completed_receipt)

    assert len(results) == 1
    product_disc = results[0]
    assert product_disc["product"] == variant_a.product

    variant_map = {v["variant"]: v for v in product_disc["variants"]}
    assert variant_a in variant_map
    assert variant_map[variant_a]["quantity_ordered"] == 10
    assert variant_map[variant_a]["quantity_received"] == 8
    assert variant_map[variant_a]["delta"] == -2


def test_get_product_discrepancies_shows_affected_orders(
    channel_USD,
    purchase_order,
    poi_a,
    stock_a,
    variant_a,
    owned_warehouse,
    completed_receipt,
):
    """get_product_discrepancies lists orders with allocations."""
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)

    line = _make_line(order, variant_a, 5)
    _make_alloc_source(poi_a, line, stock_a, 5)

    results = get_product_discrepancies(completed_receipt)

    assert len(results) == 1
    affected = results[0]["affected_orders"]
    assert len(affected) == 1
    assert affected[0]["order"] == order


def test_get_product_discrepancies_empty_when_no_attention_pois(
    completed_receipt,
):
    """Returns empty list when no POIs need attention."""
    results = get_product_discrepancies(completed_receipt)
    assert results == []


# ---------------------------------------------------------------------------
# Tests — fulfillment creation after resolution
# ---------------------------------------------------------------------------


def test_resolve_last_product_triggers_fulfillment_creation(
    channel_USD,
    purchase_order,
    poi_a,
    poia_a,
    stock_a,
    variant_a,
    owned_warehouse,
    completed_receipt,
    staff_user,
    mocker,
):
    """When all POIs on a shipment are RECEIVED, fulfillments are created.

    Fulfillments are created for linked UNFULFILLED orders after resolution.
    """
    from ...order import FulfillmentStatus, OrderStatus
    from ...order.models import Fulfillment

    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    line = _make_line(order, variant_a, 8)
    _make_alloc_source(poi_a, line, stock_a, 8)

    assert Fulfillment.objects.filter(order=order).count() == 0

    mock_manager = mocker.Mock()

    # when: resolve (this is the only product, so all POIs become RECEIVED)
    resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[{"order": order, "variant": variant_a, "quantity": 8}],
        affects_payable=True,
        user=staff_user,
        manager=mock_manager,
    )

    # then: fulfillment created
    fulfillments = Fulfillment.objects.filter(order=order)
    assert fulfillments.count() == 1
    assert fulfillments.first().status == FulfillmentStatus.WAITING_FOR_APPROVAL


def test_resolve_partial_fulfills_unaffected_order(
    channel_USD,
    purchase_order,
    poi_a,
    poia_a,
    stock_a,
    variant_a,
    owned_warehouse,
    completed_receipt,
    staff_user,
    shipment,
    nonowned_warehouse,
    product_variant_factory,
    mocker,
):
    """Unaffected orders are fulfilled even when other products still need attention."""
    from ...order import OrderStatus
    from ...order.models import Fulfillment
    from ...product.models import Product, ProductType, ProductVariant

    # given: a second POI for a DIFFERENT product on the same shipment
    product_type = ProductType.objects.first()
    other_product = Product.objects.create(
        name="Other Product",
        slug="other-product-partial-test",
        product_type=product_type,
    )
    variant_c = ProductVariant.objects.create(product=other_product, sku="RESOLVE-C")
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_c,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    poi_c = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_c,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
    )
    ReceiptLine.objects.create(
        receipt=completed_receipt,
        purchase_order_item=poi_c,
        quantity_received=7,
    )
    PurchaseOrderItemAdjustment.objects.create(
        purchase_order_item=poi_c,
        quantity_change=-3,
        reason="delivery_short",
        affects_payable=True,
        created_by=staff_user,
    )

    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    line = _make_line(order, variant_a, 8)
    _make_alloc_source(poi_a, line, stock_a, 8)

    mock_manager = mocker.Mock()

    # when: resolve only product A (product C still needs attention)
    resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[{"order": order, "variant": variant_a, "quantity": 8}],
        affects_payable=True,
        user=staff_user,
        manager=mock_manager,
    )

    # then: fulfillment IS created for this order because its own POIs are
    # all received, even though poi_c (belonging to a different product/order)
    # still requires attention on the same shipment.
    assert Fulfillment.objects.filter(order=order).count() == 1

    # and: poi_c still requires attention
    poi_c.refresh_from_db()
    assert poi_c.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION


def test_no_partial_fulfillment_when_order_spans_shipments(
    channel_USD,
    purchase_order,
    poi_a,
    poia_a,
    stock_a,
    variant_a,
    owned_warehouse,
    completed_receipt,
    staff_user,
    shipment,
    nonowned_warehouse,
    product_variant_factory,
    mocker,
):
    """An order is NOT fulfilled if it has POIs on another shipment.

    Even when the current shipment's POIs are resolved, the order should
    not be fulfilled if it has unrecieved POIs on another shipment.
    """
    from ...order import OrderStatus
    from ...order.models import Fulfillment
    from ...product.models import Product, ProductType, ProductVariant
    from ...shipping.models import Shipment

    # given: an order with variant_a on shipment (being resolved)
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    line_a = _make_line(order, variant_a, 8)
    _make_alloc_source(poi_a, line_a, stock_a, 8)

    # and: the same order also has a variant on a DIFFERENT shipment
    # that hasn't been received yet
    from ...shipping import IncoTerm, ShipmentType

    other_shipment = Shipment.objects.create(
        source=purchase_order.source_warehouse.address,
        destination=purchase_order.destination_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-OTHER",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    product_type = ProductType.objects.first()
    other_product = Product.objects.create(
        name="Other Product",
        slug="other-product-cross-shipment",
        product_type=product_type,
    )
    variant_d = ProductVariant.objects.create(product=other_product, sku="RESOLVE-D")
    stock_d = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_d,
        quantity=20,
        quantity_allocated=0,
    )
    poi_d = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_d,
        quantity_ordered=5,
        total_price_amount=50,
        currency="USD",
        shipment=other_shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    line_d = _make_line(order, variant_d, 5)
    _make_alloc_source(poi_d, line_d, stock_d, 5)

    mock_manager = mocker.Mock()

    # when: resolve variant_a on this shipment
    resolve_product_discrepancy(
        receipt=completed_receipt,
        product=variant_a.product,
        resolutions=[{"order": order, "variant": variant_a, "quantity": 8}],
        affects_payable=True,
        user=staff_user,
        manager=mock_manager,
    )

    # then: no fulfillment because the order still has an unrecieved POI
    # on the other shipment
    assert Fulfillment.objects.filter(order=order).count() == 0


def test_complete_receipt_fulfills_unaffected_orders(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    channel_USD,
    staff_user,
    product_variant_factory,
):
    """Orders unaffected by a POIA are fulfilled during receipt completion.

    Even when other orders on the same shipment have discrepancies,
    unaffected orders should still be fulfilled.
    """
    from ...order import OrderStatus
    from ...order.models import Fulfillment
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    shipment = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-UNAFFECTED",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )

    # given: order_ok with variant_ok — will be received perfectly
    variant_ok = product_variant_factory(sku="OK-VARIANT")
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_ok,
        quantity=100,
        quantity_allocated=0,
    )
    stock_ok = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_ok,
        quantity=10,
        quantity_allocated=0,
    )
    poi_ok = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_ok,
        quantity_ordered=5,
        total_price_amount=50,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
    )

    addr = purchase_order.source_warehouse.address
    order_ok = _make_order(channel_USD, addr)
    order_ok.status = OrderStatus.UNFULFILLED
    order_ok.save(update_fields=["status"])
    line_ok = _make_line(order_ok, variant_ok, 5)
    _make_alloc_source(poi_ok, line_ok, stock_ok, 5)

    # and: order_bad with variant_bad — will have a shortage
    variant_bad = product_variant_factory(sku="BAD-VARIANT")
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_bad,
        quantity=100,
        quantity_allocated=0,
    )
    stock_bad = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_bad,
        quantity=10,
        quantity_allocated=0,
    )
    poi_bad = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_bad,
        quantity_ordered=10,
        total_price_amount=100,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
    )

    order_bad = _make_order(channel_USD, addr)
    order_bad.status = OrderStatus.UNFULFILLED
    order_bad.save(update_fields=["status"])
    line_bad = _make_line(order_bad, variant_bad, 10)
    _make_alloc_source(poi_bad, line_bad, stock_bad, 10)

    # and: a receipt where variant_ok matches but variant_bad is short
    receipt = Receipt.objects.create(
        shipment=shipment,
        status=ReceiptStatus.IN_PROGRESS,
        created_by=staff_user,
    )
    ReceiptLine.objects.create(
        receipt=receipt, purchase_order_item=poi_ok, quantity_received=5
    )
    ReceiptLine.objects.create(
        receipt=receipt, purchase_order_item=poi_bad, quantity_received=7
    )

    # when
    complete_receipt(receipt, user=staff_user)

    # then: order_ok is fulfilled (its POI is received)
    assert Fulfillment.objects.filter(order=order_ok).count() == 1

    # and: order_bad is NOT fulfilled (its POI requires attention)
    assert Fulfillment.objects.filter(order=order_bad).count() == 0

    # and: poi_bad has a POIA
    poi_bad.refresh_from_db()
    assert poi_bad.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION

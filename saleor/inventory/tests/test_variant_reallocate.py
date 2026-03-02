"""Tests for _variant_reallocate."""

from decimal import Decimal

import pytest
from django.db.models import Sum

from ...order.models import Order, OrderLine
from ...warehouse.models import Allocation, AllocationSource, Stock
from .. import PurchaseOrderItemStatus, ReceiptStatus
from ..exceptions import CannotReallocateVariants
from ..models import PurchaseOrderItem, Receipt, ReceiptLine
from ..receipt_workflow import _variant_reallocate

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def variant_x(product_variant_factory):
    return product_variant_factory(sku="REALLOC-X")


@pytest.fixture
def variant_y(product_variant_factory):
    return product_variant_factory(sku="REALLOC-Y")


@pytest.fixture
def poi_x(purchase_order, variant_x, shipment, nonowned_warehouse):
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_x,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    return PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_x,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )


@pytest.fixture
def poi_y(purchase_order, variant_y, shipment, nonowned_warehouse):
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_y,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    return PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_y,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )


@pytest.fixture
def stock_x(owned_warehouse, variant_x):
    return Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_x,
        quantity=10,
        quantity_allocated=0,
    )


@pytest.fixture
def stock_y(owned_warehouse, variant_y):
    return Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_y,
        quantity=10,
        quantity_allocated=0,
    )


@pytest.fixture
def realloc_receipt(shipment):
    return Receipt.objects.create(shipment=shipment, status=ReceiptStatus.IN_PROGRESS)


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


def _make_receipt_line(receipt, poi, quantity_received):
    return ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi,
        quantity_received=quantity_received,
    )


def _total_for_order(order):
    return (
        AllocationSource.objects.filter(allocation__order_line__order=order).aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )


def _stock_snapshot(warehouse, variants):
    return {
        s.product_variant_id: (s.quantity, s.quantity_allocated)
        for s in Stock.objects.filter(warehouse=warehouse, product_variant__in=variants)
    }


def _assert_stock_invariants(warehouse, variants, before):
    after = list(
        Stock.objects.filter(warehouse=warehouse, product_variant__in=variants)
    )

    # physical quantities unchanged — reallocation doesn't move goods
    for s in after:
        if s.product_variant_id in before:
            old_qty, _ = before[s.product_variant_id]
            assert s.quantity == old_qty, (
                f"Stock {s.pk} quantity changed {old_qty} -> {s.quantity}"
            )

    # product-level conservation — total allocated is a zero-sum game
    old_total = sum(alloc for _, alloc in before.values())
    new_total = sum(s.quantity_allocated for s in after)
    assert new_total == old_total, (
        f"Product total allocated changed: {old_total} -> {new_total}"
    )

    for s in after:
        # non-negativity
        assert s.quantity_allocated >= 0, f"Negative allocation on stock {s.pk}"
        # denorm consistency — Stock counter matches sum of its Allocations
        alloc_sum = (
            Allocation.objects.filter(stock=s).aggregate(t=Sum("quantity_allocated"))[
                "t"
            ]
            or 0
        )
        assert s.quantity_allocated == alloc_sum, (
            f"Stock {s.pk}: quantity_allocated={s.quantity_allocated} "
            f"!= sum(Allocation)={alloc_sum}"
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_variant_reallocate_preserves_per_order_totals_with_equal_weights(
    channel_USD,
    purchase_order,
    poi_x,
    poi_y,
    stock_x,
    stock_y,
    realloc_receipt,
    variant_x,
    variant_y,
):
    """Each order's total allocation is preserved when the variant mix changes.

    Regression for Bug 1: the old code called hamilton(total_entitlement, recv_qty)
    independently for each variant. With equal weights (A=5, B=5), every call hit
    a 0.5/0.5 tie and the same order always won the rounding bonus, inflating its
    total from 5 to 6 while the other dropped to 4.

    The two-stage fix calls Hamilton once on totals to get per-order quotas, then
    distributes variants using those quotas as weights — guaranteeing totals hold.
    """
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)
    order_b = _make_order(channel_USD, addr)

    # given - A has 3 of X and 2 of Y; B has 2 of X and 3 of Y (5 total each)
    line_a_x = _make_line(order_a, variant_x, 3)
    line_a_y = _make_line(order_a, variant_y, 2)
    line_b_x = _make_line(order_b, variant_x, 2)
    line_b_y = _make_line(order_b, variant_y, 3)
    ass = [
        _make_alloc_source(poi_x, line_a_x, stock_x, 3),
        _make_alloc_source(poi_x, line_b_x, stock_x, 2),
        _make_alloc_source(poi_y, line_a_y, stock_y, 2),
        _make_alloc_source(poi_y, line_b_y, stock_y, 3),
    ]

    # given - received: 3 of X, 7 of Y (different mix, same total 10)
    rs = [
        _make_receipt_line(realloc_receipt, poi_x, 3),
        _make_receipt_line(realloc_receipt, poi_y, 7),
    ]

    before = _stock_snapshot(stock_x.warehouse, [variant_x, variant_y])

    # when
    _variant_reallocate(rs, ass)

    # then - each order's total across all variants is unchanged at 5
    assert _total_for_order(order_a) == 5
    assert _total_for_order(order_b) == 5
    _assert_stock_invariants(stock_x.warehouse, [variant_x, variant_y], before)


def test_variant_reallocate_uses_correct_order_line_per_variant(
    channel_USD,
    purchase_order,
    poi_x,
    poi_y,
    stock_x,
    stock_y,
    realloc_receipt,
    variant_x,
    variant_y,
):
    """New allocations are linked to the order line matching each variant.

    Regression for Bug 2: the old code keyed order_line_by_order[order] without
    variant. The second variant's order_line clobbered the first, so both new
    allocations for that order ended up on the wrong order line.
    """
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    # given - A has separate order lines for X and Y
    line_a_x = _make_line(order_a, variant_x, 3)
    line_a_y = _make_line(order_a, variant_y, 2)
    ass = [
        _make_alloc_source(poi_x, line_a_x, stock_x, 3),
        _make_alloc_source(poi_y, line_a_y, stock_y, 2),
    ]

    # given - received: 1 of X, 4 of Y (mix shifted, total unchanged at 5)
    rs = [
        _make_receipt_line(realloc_receipt, poi_x, 1),
        _make_receipt_line(realloc_receipt, poi_y, 4),
    ]

    before = _stock_snapshot(stock_x.warehouse, [variant_x, variant_y])

    # when
    _variant_reallocate(rs, ass)

    # then - AllocationSource for X POI links to line_a_x (not line_a_y)
    for src in AllocationSource.objects.filter(purchase_order_item=poi_x):
        assert src.allocation.order_line == line_a_x

    # then - AllocationSource for Y POI links to line_a_y (not line_a_x)
    for src in AllocationSource.objects.filter(purchase_order_item=poi_y):
        assert src.allocation.order_line == line_a_y

    _assert_stock_invariants(stock_x.warehouse, [variant_x, variant_y], before)


def test_variant_reallocate_noop_when_received_matches_allocated(
    channel_USD,
    purchase_order,
    poi_x,
    stock_x,
    realloc_receipt,
    variant_x,
):
    """When received quantity matches allocated, nothing is touched."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)
    line_a = _make_line(order_a, variant_x, 5)
    alloc_source = _make_alloc_source(poi_x, line_a, stock_x, 5)

    rs = [_make_receipt_line(realloc_receipt, poi_x, 5)]
    ass = [alloc_source]

    before = _stock_snapshot(stock_x.warehouse, [variant_x])

    # when
    _variant_reallocate(rs, ass)

    # then - AllocationSource untouched
    alloc_source.refresh_from_db()
    assert alloc_source.quantity == 5

    _assert_stock_invariants(stock_x.warehouse, [variant_x], before)


def test_variant_reallocate_raises_on_shortage(
    channel_USD,
    purchase_order,
    poi_x,
    stock_x,
    realloc_receipt,
    variant_x,
):
    """A shortage (received < ordered) raises CannotReallocateVariants."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)
    order_b = _make_order(channel_USD, addr)

    # given - A entitled to 6, B to 4 (total 10)
    line_a = _make_line(order_a, variant_x, 6)
    line_b = _make_line(order_b, variant_x, 4)
    ass = [
        _make_alloc_source(poi_x, line_a, stock_x, 6),
        _make_alloc_source(poi_x, line_b, stock_x, 4),
    ]

    # given - only 8 received instead of 10
    rs = [_make_receipt_line(realloc_receipt, poi_x, 8)]

    before = _stock_snapshot(stock_x.warehouse, [variant_x])

    # when / then
    with pytest.raises(CannotReallocateVariants):
        _variant_reallocate(rs, ass)

    # then - stocks unchanged (raised before any mutation)
    _assert_stock_invariants(stock_x.warehouse, [variant_x], before)


def test_variant_reallocate_preserves_poi_quantity_ordered(
    channel_USD,
    purchase_order,
    poi_x,
    poi_y,
    stock_x,
    stock_y,
    realloc_receipt,
    variant_x,
    variant_y,
):
    """POI.quantity_ordered is NOT changed by reallocation — it's a historical record."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    # given - ordered 10 X and 10 Y
    line_a_x = _make_line(order_a, variant_x, 10)
    line_a_y = _make_line(order_a, variant_y, 10)
    ass = [
        _make_alloc_source(poi_x, line_a_x, stock_x, 10),
        _make_alloc_source(poi_y, line_a_y, stock_y, 10),
    ]

    # given - received 3 X and 17 Y (same total, different mix)
    rs = [
        _make_receipt_line(realloc_receipt, poi_x, 3),
        _make_receipt_line(realloc_receipt, poi_y, 17),
    ]

    # when
    _variant_reallocate(rs, ass)

    # then - quantity_ordered unchanged (discrepancy tracked via POIAs)
    poi_x.refresh_from_db()
    poi_y.refresh_from_db()
    assert poi_x.quantity_ordered == 10
    assert poi_y.quantity_ordered == 10


def test_variant_reallocate_handles_surplus_as_floor_stock(
    channel_USD,
    purchase_order,
    poi_x,
    poi_y,
    stock_x,
    stock_y,
    realloc_receipt,
    variant_x,
    variant_y,
):
    """Surplus (received > ordered) gives orders their full entitlement; leftovers are floor stock."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)
    order_b = _make_order(channel_USD, addr)

    # given - A entitled to 5, B entitled to 5 (total 10)
    line_a_x = _make_line(order_a, variant_x, 3)
    line_a_y = _make_line(order_a, variant_y, 2)
    line_b_x = _make_line(order_b, variant_x, 2)
    line_b_y = _make_line(order_b, variant_y, 3)
    ass = [
        _make_alloc_source(poi_x, line_a_x, stock_x, 3),
        _make_alloc_source(poi_x, line_b_x, stock_x, 2),
        _make_alloc_source(poi_y, line_a_y, stock_y, 2),
        _make_alloc_source(poi_y, line_b_y, stock_y, 3),
    ]

    # given - received 12 total (3X + 9Y) — surplus of 2
    rs = [
        _make_receipt_line(realloc_receipt, poi_x, 3),
        _make_receipt_line(realloc_receipt, poi_y, 9),
    ]

    before = _stock_snapshot(stock_x.warehouse, [variant_x, variant_y])

    # when
    _variant_reallocate(rs, ass)

    # then - each order gets their full entitlement
    assert _total_for_order(order_a) == 5
    assert _total_for_order(order_b) == 5

    # then - total allocated is 10 (not 12), 2 surplus units are floor stock
    _assert_stock_invariants(stock_x.warehouse, [variant_x, variant_y], before)


def test_poi_quantity_allocated_updated_after_reallocation(
    channel_USD,
    purchase_order,
    poi_x,
    poi_y,
    stock_x,
    stock_y,
    realloc_receipt,
    variant_x,
    variant_y,
):
    """POI.quantity_allocated is kept in sync with its AllocationSource rows.

    _remove_allocation_source and _add_allocation_source both mutate
    POI.quantity_allocated, but no existing test checks the post-call value.
    INVARIANT: poi.quantity_allocated == sum(AllocationSource.quantity for that POI).
    """
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)
    order_b = _make_order(channel_USD, addr)

    # given - same setup as the equal-weights test (3X+2Y for A, 2X+3Y for B)
    line_a_x = _make_line(order_a, variant_x, 3)
    line_a_y = _make_line(order_a, variant_y, 2)
    line_b_x = _make_line(order_b, variant_x, 2)
    line_b_y = _make_line(order_b, variant_y, 3)
    ass = [
        _make_alloc_source(poi_x, line_a_x, stock_x, 3),
        _make_alloc_source(poi_x, line_b_x, stock_x, 2),
        _make_alloc_source(poi_y, line_a_y, stock_y, 2),
        _make_alloc_source(poi_y, line_b_y, stock_y, 3),
    ]

    # given - received 3X + 7Y (same total, different mix)
    rs = [
        _make_receipt_line(realloc_receipt, poi_x, 3),
        _make_receipt_line(realloc_receipt, poi_y, 7),
    ]

    # when
    _variant_reallocate(rs, ass)

    # then - poi counters match their AllocationSource sums (INVARIANT)
    poi_x.refresh_from_db()
    poi_y.refresh_from_db()
    x_src_sum = (
        AllocationSource.objects.filter(purchase_order_item=poi_x).aggregate(
            t=Sum("quantity")
        )["t"]
        or 0
    )
    y_src_sum = (
        AllocationSource.objects.filter(purchase_order_item=poi_y).aggregate(
            t=Sum("quantity")
        )["t"]
        or 0
    )
    assert poi_x.quantity_allocated == x_src_sum
    assert poi_y.quantity_allocated == y_src_sum
    # all received units distributed (no surplus)
    assert x_src_sum == 3
    assert y_src_sum == 7


def test_poi_quantity_ordered_updated_to_received(
    channel_USD,
    purchase_order,
    poi_x,
    poi_y,
    stock_x,
    stock_y,
    realloc_receipt,
    variant_x,
    variant_y,
):
    """Reallocation redistributes variants but does not change quantity_ordered."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    # given - order_a entitled to 3X + 7Y
    line_a_x = _make_line(order_a, variant_x, 3)
    line_a_y = _make_line(order_a, variant_y, 7)
    ass = [
        _make_alloc_source(poi_x, line_a_x, stock_x, 3),
        _make_alloc_source(poi_y, line_a_y, stock_y, 7),
    ]

    # given - received 5X + 5Y (same total 10, different mix)
    rs = [
        _make_receipt_line(realloc_receipt, poi_x, 5),
        _make_receipt_line(realloc_receipt, poi_y, 5),
    ]

    before = _stock_snapshot(stock_x.warehouse, [variant_x, variant_y])

    # when
    _variant_reallocate(rs, ass)

    # then - quantity_ordered is NOT changed by reallocation
    poi_x.refresh_from_db()
    poi_y.refresh_from_db()
    assert poi_x.quantity_ordered == 10
    assert poi_y.quantity_ordered == 10

    # but allocations are redistributed: order_a gets 5X + 5Y
    new_ass_x = AllocationSource.objects.filter(
        purchase_order_item=poi_x,
        allocation__order_line__order=order_a,
    )
    new_ass_y = AllocationSource.objects.filter(
        purchase_order_item=poi_y,
        allocation__order_line__order=order_a,
    )
    assert new_ass_x.aggregate(total=Sum("quantity"))["total"] == 5
    assert new_ass_y.aggregate(total=Sum("quantity"))["total"] == 5

    _assert_stock_invariants(stock_x.warehouse, [variant_x, variant_y], before)


def test_order_line_deleted_when_variant_distribution_is_zero(
    channel_USD,
    purchase_order,
    poi_x,
    poi_y,
    stock_x,
    stock_y,
    realloc_receipt,
    variant_x,
    variant_y,
):
    """When an order receives zero of a variant, its OrderLine is deleted.

    _variant_reallocate calls line.delete() for any (order, variant) pair whose
    new distribution is zero. No existing test asserts the row is gone.
    """
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    # given - order_a has 5 of X and 5 of Y
    line_a_x = _make_line(order_a, variant_x, 5)
    line_a_y = _make_line(order_a, variant_y, 5)
    ass = [
        _make_alloc_source(poi_x, line_a_x, stock_x, 5),
        _make_alloc_source(poi_y, line_a_y, stock_y, 5),
    ]

    # given - received 0X + 10Y (X entirely absent)
    rs = [
        _make_receipt_line(realloc_receipt, poi_x, 0),
        _make_receipt_line(realloc_receipt, poi_y, 10),
    ]

    line_a_x_pk = line_a_x.pk
    before = _stock_snapshot(stock_x.warehouse, [variant_x, variant_y])

    # when
    _variant_reallocate(rs, ass)

    # then - X line is gone from the DB
    assert not OrderLine.objects.filter(pk=line_a_x_pk).exists()

    # then - Y line updated to absorb all entitlement
    line_a_y.refresh_from_db()
    assert line_a_y.quantity == 10

    _assert_stock_invariants(stock_x.warehouse, [variant_x, variant_y], before)


def test_new_order_line_created_for_redistributed_variant(
    channel_USD,
    purchase_order,
    poi_x,
    poi_y,
    stock_x,
    stock_y,
    realloc_receipt,
    variant_x,
    variant_y,
):
    """A new OrderLine is created when reallocation assigns a variant an order didn't have.

    When distribution produces an (order, variant) pair that had no prior AllocationSource,
    _variant_reallocate creates a new OrderLine (copying pricing from the template line).
    This code path was entirely untested.
    """
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)
    order_b = _make_order(channel_USD, addr)

    # given - A has only X, B has only Y
    line_a_x = _make_line(order_a, variant_x, 5)
    line_b_y = _make_line(order_b, variant_y, 5)
    ass = [
        _make_alloc_source(poi_x, line_a_x, stock_x, 5),
        _make_alloc_source(poi_y, line_b_y, stock_y, 5),
    ]

    # given - received 0X + 10Y; A's X goes away, A should get some Y instead
    rs = [
        _make_receipt_line(realloc_receipt, poi_x, 0),
        _make_receipt_line(realloc_receipt, poi_y, 10),
    ]

    before = _stock_snapshot(stock_x.warehouse, [variant_x, variant_y])

    # when
    _variant_reallocate(rs, ass)

    # then - a new Y line exists for order_a (didn't have one before)
    new_line = OrderLine.objects.filter(order=order_a, variant=variant_y).first()
    assert new_line is not None
    assert new_line.quantity == 5

    # then - AllocationSource for the new line points to poi_y
    assert AllocationSource.objects.filter(
        allocation__order_line=new_line,
        purchase_order_item=poi_y,
    ).exists()

    # then - original X line for A is gone
    assert not OrderLine.objects.filter(pk=line_a_x.pk).exists()

    _assert_stock_invariants(stock_x.warehouse, [variant_x, variant_y], before)


def test_multiple_pois_per_variant_distributed_by_hamilton(
    channel_USD,
    purchase_order,
    stock_x,
    realloc_receipt,
    variant_x,
    shipment,
    nonowned_warehouse,
):
    """When a variant has multiple POIs, Hamilton sub-distributes allocation across them.

    Lines 779-784 of stock_management.py run Hamilton a second time to split the
    per-order allocation across the contributing POIs. This branch was entirely untested.
    """
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_x,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    poi_x1 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_x,
        quantity_ordered=5,
        total_price_amount=Decimal("50.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    poi_x2 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_x,
        quantity_ordered=5,
        total_price_amount=Decimal("50.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)
    line_a_x = _make_line(order_a, variant_x, 7)

    # given - 4 units backed by poi_x1, 3 backed by poi_x2
    ass = [
        _make_alloc_source(poi_x1, line_a_x, stock_x, 4),
        _make_alloc_source(poi_x2, line_a_x, stock_x, 3),
    ]

    # given - poi_x1 received 3 (was 5), poi_x2 received 5 (was 5); total 8 vs entitlement 7
    rs = [
        _make_receipt_line(realloc_receipt, poi_x1, 3),
        _make_receipt_line(realloc_receipt, poi_x2, 5),
    ]

    before = _stock_snapshot(stock_x.warehouse, [variant_x])

    # when
    _variant_reallocate(rs, ass)

    # then - each POI's counter matches its AllocationSource sum
    poi_x1.refresh_from_db()
    poi_x2.refresh_from_db()
    x1_src = (
        AllocationSource.objects.filter(purchase_order_item=poi_x1).aggregate(
            t=Sum("quantity")
        )["t"]
        or 0
    )
    x2_src = (
        AllocationSource.objects.filter(purchase_order_item=poi_x2).aggregate(
            t=Sum("quantity")
        )["t"]
        or 0
    )
    assert poi_x1.quantity_allocated == x1_src
    assert poi_x2.quantity_allocated == x2_src
    # Hamilton({poi_x1:3, poi_x2:5}, 7): poi_x1 gets 3 (higher remainder), poi_x2 gets 4
    assert x1_src == 3
    assert x2_src == 4
    assert x1_src + x2_src == 7  # total == order entitlement

    _assert_stock_invariants(stock_x.warehouse, [variant_x], before)


def test_matched_variants_untouched_during_partial_mismatch(
    channel_USD,
    purchase_order,
    poi_x,
    poi_y,
    stock_x,
    stock_y,
    realloc_receipt,
    variant_x,
    variant_y,
):
    """AllocationSources for exactly-matched variants are not touched.

    When some variants match and others don't, _variant_reallocate should only
    rewrite the mismatched variants' AllocationSources. No test verified that
    matched variants' rows survive the call unchanged.
    """
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    # given - order_a has 5X and 5Y
    line_a_x = _make_line(order_a, variant_x, 5)
    line_a_y = _make_line(order_a, variant_y, 5)
    ass = [
        _make_alloc_source(poi_x, line_a_x, stock_x, 5),
        _make_alloc_source(poi_y, line_a_y, stock_y, 5),
    ]

    # given - X matches exactly (5 received), Y has surplus (8 received)
    rs = [
        _make_receipt_line(realloc_receipt, poi_x, 5),
        _make_receipt_line(realloc_receipt, poi_y, 8),
    ]

    x_as_pks_before = set(
        AllocationSource.objects.filter(purchase_order_item=poi_x).values_list(
            "pk", flat=True
        )
    )

    before = _stock_snapshot(stock_x.warehouse, [variant_x, variant_y])

    # when
    _variant_reallocate(rs, ass)

    # then - X's AllocationSource rows are identical (same PKs, not deleted/recreated)
    x_as_pks_after = set(
        AllocationSource.objects.filter(purchase_order_item=poi_x).values_list(
            "pk", flat=True
        )
    )
    assert x_as_pks_before == x_as_pks_after

    # then - Y reallocation happened normally (surplus 3 goes to floor stock)
    poi_y.refresh_from_db()
    assert poi_y.quantity_allocated == 5

    _assert_stock_invariants(stock_x.warehouse, [variant_x, variant_y], before)

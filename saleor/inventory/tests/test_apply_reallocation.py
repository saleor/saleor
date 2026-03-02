"""Tests for _apply_reallocation — the shared primitive for variant redistribution.

_apply_reallocation takes a set of AllocationSources to remove and a target
distribution, then atomically tears down the old world and rebuilds the new one.
It's used by both _variant_reallocate (automated Hamilton) and the future
POIA substitute resolution (user-driven).
"""

from decimal import Decimal

import pytest
from django.db.models import Sum

from ...order.models import Order, OrderLine
from ...warehouse.models import Allocation, AllocationSource, Stock
from .. import PurchaseOrderItemStatus
from ..models import PurchaseOrderItem
from ..receipt_workflow import _apply_reallocation

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def variant_m(product_variant_factory):
    return product_variant_factory(sku="APPLY-M")


@pytest.fixture
def variant_l(product_variant_factory):
    return product_variant_factory(sku="APPLY-L")


@pytest.fixture
def poi_m(purchase_order, variant_m, shipment, nonowned_warehouse):
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_m,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    return PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_m,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )


@pytest.fixture
def poi_l(purchase_order, variant_l, shipment, nonowned_warehouse):
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_l,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    return PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_l,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )


@pytest.fixture
def stock_m(owned_warehouse, variant_m):
    return Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_m,
        quantity=10,
        quantity_allocated=0,
    )


@pytest.fixture
def stock_l(owned_warehouse, variant_l):
    return Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_l,
        quantity=10,
        quantity_allocated=0,
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


def _assert_stock_invariants(warehouse, variants):
    stocks = list(
        Stock.objects.filter(warehouse=warehouse, product_variant__in=variants)
    )
    for s in stocks:
        assert s.quantity_allocated >= 0
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


def test_substitute_variant_for_one_order(
    channel_USD,
    purchase_order,
    poi_m,
    poi_l,
    stock_m,
    stock_l,
    variant_m,
    variant_l,
    owned_warehouse,
):
    """Substitute: order had 5 M, user says give them 5 L instead."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    # given: order_a has 5 units of variant_m via poi_m
    line_a_m = _make_line(order_a, variant_m, 5)
    as_m = _make_alloc_source(poi_m, line_a_m, stock_m, 5)

    # when: substitute all 5 M -> 5 L
    distribution = {(order_a, variant_l): 5}
    _apply_reallocation(
        removals=[as_m],
        distribution=distribution,
        poi_by_variant={variant_l: [poi_l]},
        received_by_poi={poi_l: 1},
        warehouse=owned_warehouse,
    )

    # then: old AllocationSource for M is gone
    assert not AllocationSource.objects.filter(pk=as_m.pk).exists()

    # and: new AllocationSource for L exists
    new_ass = AllocationSource.objects.filter(
        purchase_order_item=poi_l,
        allocation__order_line__order=order_a,
    )
    assert new_ass.count() == 1
    assert new_ass.first().quantity == 5

    # and: OrderLine for M was deleted (qty went to 0 in distribution)
    assert not OrderLine.objects.filter(pk=line_a_m.pk).exists()

    # and: new OrderLine for L was created
    new_line = OrderLine.objects.get(order=order_a, variant=variant_l)
    assert new_line.quantity == 5

    # and: stock invariants hold
    _assert_stock_invariants(owned_warehouse, [variant_m, variant_l])


def test_partial_substitute(
    channel_USD,
    purchase_order,
    poi_m,
    poi_l,
    stock_m,
    stock_l,
    variant_m,
    variant_l,
    owned_warehouse,
):
    """Partial substitute: order had 5 M, keep 3 M and give 2 L."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    line_a_m = _make_line(order_a, variant_m, 5)
    as_m = _make_alloc_source(poi_m, line_a_m, stock_m, 5)

    # when: keep 3 M and add 2 L
    distribution = {(order_a, variant_m): 3, (order_a, variant_l): 2}
    _apply_reallocation(
        removals=[as_m],
        distribution=distribution,
        poi_by_variant={variant_m: [poi_m], variant_l: [poi_l]},
        received_by_poi={poi_m: 1, poi_l: 1},
        warehouse=owned_warehouse,
    )

    # then: order_a total allocation is still 5
    assert _total_allocated_for_order(order_a) == 5

    # and: M line reduced to 3
    line_a_m.refresh_from_db()
    assert line_a_m.quantity == 3

    # and: L line created with 2
    new_line_l = OrderLine.objects.get(order=order_a, variant=variant_l)
    assert new_line_l.quantity == 2

    _assert_stock_invariants(owned_warehouse, [variant_m, variant_l])


def test_remove_allocation_entirely(
    channel_USD,
    purchase_order,
    poi_m,
    stock_m,
    variant_m,
    owned_warehouse,
):
    """Remove: order had 5 M, user says remove all (order gets shorted)."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    line_a_m = _make_line(order_a, variant_m, 5)
    as_m = _make_alloc_source(poi_m, line_a_m, stock_m, 5)

    # when: empty distribution (order gets nothing)
    _apply_reallocation(
        removals=[as_m],
        distribution={},
        poi_by_variant={},
        received_by_poi={},
        warehouse=owned_warehouse,
    )

    # then: AllocationSource gone
    assert (
        AllocationSource.objects.filter(allocation__order_line__order=order_a).count()
        == 0
    )

    # and: OrderLine deleted
    assert not OrderLine.objects.filter(pk=line_a_m.pk).exists()

    # and: stock deallocated
    stock_m.refresh_from_db()
    assert stock_m.quantity_allocated == 0

    _assert_stock_invariants(owned_warehouse, [variant_m])


def test_multi_order_substitute(
    channel_USD,
    purchase_order,
    poi_m,
    poi_l,
    stock_m,
    stock_l,
    variant_m,
    variant_l,
    owned_warehouse,
):
    """Two orders both get substituted from M to L."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)
    order_b = _make_order(channel_USD, addr)

    line_a_m = _make_line(order_a, variant_m, 3)
    line_b_m = _make_line(order_b, variant_m, 7)
    as_a = _make_alloc_source(poi_m, line_a_m, stock_m, 3)
    as_b = _make_alloc_source(poi_m, line_b_m, stock_m, 7)

    # when: both orders get L instead of M
    distribution = {
        (order_a, variant_l): 3,
        (order_b, variant_l): 7,
    }
    _apply_reallocation(
        removals=[as_a, as_b],
        distribution=distribution,
        poi_by_variant={variant_l: [poi_l]},
        received_by_poi={poi_l: 1},
        warehouse=owned_warehouse,
    )

    # then: each order has correct allocation to L
    assert _total_allocated_for_order(order_a) == 3
    assert _total_allocated_for_order(order_b) == 7

    # and: M lines deleted, L lines created
    assert not OrderLine.objects.filter(
        variant=variant_m, order__in=[order_a, order_b]
    ).exists()
    assert OrderLine.objects.get(order=order_a, variant=variant_l).quantity == 3
    assert OrderLine.objects.get(order=order_b, variant=variant_l).quantity == 7

    # and: M stock fully deallocated, L stock allocated
    stock_m.refresh_from_db()
    assert stock_m.quantity_allocated == 0
    stock_l.refresh_from_db()
    assert stock_l.quantity_allocated == 10

    _assert_stock_invariants(owned_warehouse, [variant_m, variant_l])


def test_preserves_order_line_pricing(
    channel_USD,
    purchase_order,
    poi_m,
    poi_l,
    stock_m,
    stock_l,
    variant_m,
    variant_l,
    owned_warehouse,
):
    """New OrderLines created by _apply_reallocation inherit pricing from the template."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    line_a_m = _make_line(order_a, variant_m, 5)
    as_m = _make_alloc_source(poi_m, line_a_m, stock_m, 5)

    _apply_reallocation(
        removals=[as_m],
        distribution={(order_a, variant_l): 3},
        poi_by_variant={variant_l: [poi_l]},
        received_by_poi={poi_l: 1},
        warehouse=owned_warehouse,
    )

    # then: new L line has correct pricing from the M template
    new_line = OrderLine.objects.get(order=order_a, variant=variant_l)
    assert new_line.unit_price_net_amount == Decimal("10.00")
    assert new_line.total_price_net_amount == Decimal("30.00")
    assert new_line.total_price_gross_amount == Decimal("30.00")


def test_poi_quantity_allocated_updated(
    channel_USD,
    purchase_order,
    poi_m,
    poi_l,
    stock_m,
    stock_l,
    variant_m,
    variant_l,
    owned_warehouse,
):
    """POI.quantity_allocated is correctly decremented and incremented."""
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    line_a_m = _make_line(order_a, variant_m, 5)
    _make_alloc_source(poi_m, line_a_m, stock_m, 5)

    assert poi_m.quantity_allocated == 5
    assert poi_l.quantity_allocated == 0

    removals = list(AllocationSource.objects.filter(purchase_order_item=poi_m))

    _apply_reallocation(
        removals=removals,
        distribution={(order_a, variant_l): 5},
        poi_by_variant={variant_l: [poi_l]},
        received_by_poi={poi_l: 1},
        warehouse=owned_warehouse,
    )

    poi_m.refresh_from_db()
    poi_l.refresh_from_db()
    assert poi_m.quantity_allocated == 0
    assert poi_l.quantity_allocated == 5


def test_empty_removals_and_distribution_is_noop(owned_warehouse):
    """Empty inputs produce no changes."""
    _apply_reallocation(
        removals=[],
        distribution={},
        poi_by_variant={},
        received_by_poi={},
        warehouse=owned_warehouse,
    )


def test_acquires_locks_on_stock_order_and_poi(
    channel_USD,
    purchase_order,
    poi_m,
    poi_l,
    stock_m,
    stock_l,
    variant_m,
    variant_l,
    owned_warehouse,
):
    """_apply_reallocation issues SELECT ... FOR UPDATE on Stock, Order, and POI rows."""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)

    line_a_m = _make_line(order_a, variant_m, 5)
    as_m = _make_alloc_source(poi_m, line_a_m, stock_m, 5)

    distribution = {(order_a, variant_l): 5}

    with CaptureQueriesContext(connection) as ctx:
        _apply_reallocation(
            removals=[as_m],
            distribution=distribution,
            poi_by_variant={variant_l: [poi_l]},
            received_by_poi={poi_l: 1},
            warehouse=owned_warehouse,
        )

    for_update_queries = [q["sql"] for q in ctx if "FOR UPDATE" in q["sql"]]
    assert len(for_update_queries) >= 3, (
        f"Expected at least 3 FOR UPDATE queries (Stock, Order, POI), "
        f"got {len(for_update_queries)}: {for_update_queries}"
    )


def test_shared_stock_correct_with_select_related(
    channel_USD,
    purchase_order,
    poi_m,
    poi_l,
    stock_m,
    stock_l,
    variant_m,
    variant_l,
    owned_warehouse,
):
    """Multiple removals sharing the same Stock work correctly even when loaded.

    AllocationSources are loaded with select_related (simulating production).
    Regression: without pre-locked Stock maps, select_related creates separate
    Python objects per FK join. The second removal's save() overwrites the
    first removal's decrement because it starts from a stale quantity_allocated.
    """
    addr = purchase_order.source_warehouse.address
    order_a = _make_order(channel_USD, addr)
    order_b = _make_order(channel_USD, addr)

    line_a_m = _make_line(order_a, variant_m, 3)
    line_b_m = _make_line(order_b, variant_m, 7)
    as_a = _make_alloc_source(poi_m, line_a_m, stock_m, 3)
    as_b = _make_alloc_source(poi_m, line_b_m, stock_m, 7)

    # Load with select_related — this creates separate Python objects for
    # the same Stock/POI row (the production code path via complete_receipt)
    loaded_ass = list(
        AllocationSource.objects.filter(
            pk__in=[as_a.pk, as_b.pk],
        ).select_related(
            "allocation__stock",
            "allocation__order_line__order",
            "purchase_order_item__product_variant",
        )
    )

    # Verify the FK cache objects are indeed separate Python instances
    assert loaded_ass[0].allocation.stock is not loaded_ass[1].allocation.stock
    assert loaded_ass[0].allocation.stock.pk == loaded_ass[1].allocation.stock.pk
    assert loaded_ass[0].purchase_order_item is not loaded_ass[1].purchase_order_item

    distribution = {
        (order_a, variant_l): 3,
        (order_b, variant_l): 7,
    }
    _apply_reallocation(
        removals=loaded_ass,
        distribution=distribution,
        poi_by_variant={variant_l: [poi_l]},
        received_by_poi={poi_l: 1},
        warehouse=owned_warehouse,
    )

    # Stock M should be fully deallocated (0, not 3 or 7 from stale overwrite)
    stock_m.refresh_from_db()
    assert stock_m.quantity_allocated == 0

    # Stock L should have exactly 10 allocated
    stock_l.refresh_from_db()
    assert stock_l.quantity_allocated == 10

    # POI M should be fully deallocated
    poi_m.refresh_from_db()
    assert poi_m.quantity_allocated == 0

    # POI L should have exactly 10 allocated
    poi_l.refresh_from_db()
    assert poi_l.quantity_allocated == 10

    _assert_stock_invariants(owned_warehouse, [variant_m, variant_l])

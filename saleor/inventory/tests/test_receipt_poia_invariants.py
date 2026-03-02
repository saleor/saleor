"""Tests validating that receipt POIAs never affect existing fulfillments.

Theory: Any POIA generated on receipt cannot require fulfillment amendments,
because fulfillments can only be created AFTER inventory is received.

The temporal ordering guarantee:
  Inventory received (POIA possible) -> Orders edited -> Fulfillments created -> Proformas sent

Exception: POIAs created AFTER receipt (shrinkage, cycle counts) can affect fulfillments.
"""

from decimal import Decimal

import pytest

from ...inventory.receipt_workflow import complete_receipt
from ...order import OrderStatus
from ...order.models import Fulfillment
from ...warehouse.management import allocate_sources
from ...warehouse.models import Allocation, Stock
from .. import PurchaseOrderItemStatus


def assert_receipt_poia_invariant(poia):
    """Assert that a receipt-time POIA doesn't affect fulfillments.

    Can be called in any test after receipt completion.
    """
    affected_sources = poia.purchase_order_item.allocation_sources.all()
    affected_orders = {
        source.allocation.order_line.order for source in affected_sources
    }

    fulfillments = Fulfillment.objects.filter(order__in=affected_orders)

    assert not fulfillments.exists(), (
        f"INVARIANT VIOLATION: Receipt POIA {poia.id} affects "
        f"{fulfillments.count()} existing fulfillments"
    )


def setup_order_with_poi_allocation(order_line, poi, stock, order_status, fully_paid):
    """Set up an order with allocation sourced from the given POI."""
    order = order_line.order
    order.status = order_status
    order.total_gross_amount = Decimal("1000.00")
    order.total_net_amount = Decimal("1000.00")
    order.total_charged_amount = Decimal("1000.00") if fully_paid else Decimal("0.00")
    order.save()

    order_line.quantity = 10
    order_line.variant = poi.product_variant
    order_line.save()

    allocation = Allocation.objects.create(
        order_line=order_line,
        stock=stock,
        quantity_allocated=10,
    )
    allocate_sources(allocation)
    return order


@pytest.mark.parametrize(
    ("order_status", "fully_paid"),
    [
        (OrderStatus.UNCONFIRMED, False),
        (OrderStatus.UNCONFIRMED, True),
        (OrderStatus.UNFULFILLED, False),
        (OrderStatus.UNFULFILLED, True),
    ],
)
@pytest.mark.django_db
def test_receipt_poia_never_affects_fulfillments(
    order_status,
    fully_paid,
    purchase_order_item,
    order_line,
    owned_warehouse,
    staff_user,
):
    """Receipt POIAs never affect fulfillments regardless of order state.

    The new complete_receipt tries variant reallocation first. For a
    single-variant shortage, reallocation always fails (CannotReallocateVariants)
    so a pending POIA is created. The POIA is never auto-processed — it always
    requires manual resolution.
    """
    poi = purchase_order_item
    stock = Stock.objects.get(
        warehouse=owned_warehouse,
        product_variant=poi.product_variant,
    )

    order = setup_order_with_poi_allocation(
        order_line, poi, stock, order_status, fully_paid
    )

    # Precondition: the invariant we're testing
    assert order.fulfillments.count() == 0

    # given: start receipt and record shortage
    from ..receipt_workflow import receive_item, start_receipt

    receipt = start_receipt(poi.shipment, user=staff_user)
    receive_item(
        receipt=receipt,
        product_variant=poi.product_variant,
        quantity=90,  # Ordered 100, shortage of 10
        user=staff_user,
    )

    # when
    result = complete_receipt(receipt, user=staff_user)

    # then: POIA created as pending (not auto-processed)
    assert len(result["adjustments_pending"]) > 0
    assert "adjustments_created" not in result

    poia = result["adjustments_pending"][0]
    assert poia.processed_at is None
    assert poia.quantity_change == -10
    assert poia.reason == "delivery_short"

    # and: POI marked as requires attention (blocks fulfillment)
    poi.refresh_from_db()
    assert poi.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION

    # INVARIANT: no fulfillments exist
    order.refresh_from_db()
    assert order.fulfillments.count() == 0

    # Invariant helper also passes
    for p in result["adjustments_pending"]:
        assert_receipt_poia_invariant(p)

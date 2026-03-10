"""Tests for delay_for_future_shipment."""

from decimal import Decimal

import pytest
from django.db.models import Sum

from ...order import OrderOrigin, OrderStatus
from ...order.models import Order, OrderLine
from ...warehouse.models import Allocation, AllocationSource, Stock
from .. import PurchaseOrderItemAdjustmentReason, PurchaseOrderItemStatus, ReceiptStatus
from ..models import (
    PurchaseOrderItem,
    PurchaseOrderItemAdjustment,
    Receipt,
    ReceiptLine,
)
from ..receipt_workflow import delay_for_future_shipment

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def variant_delay(product_variant_factory):
    return product_variant_factory(sku="DELAY-A")


@pytest.fixture
def completed_receipt(shipment, staff_user):
    return Receipt.objects.create(
        shipment=shipment,
        status=ReceiptStatus.COMPLETED,
        created_by=staff_user,
    )


@pytest.fixture
def poi_unreceived(
    purchase_order, variant_delay, shipment, nonowned_warehouse, completed_receipt
):
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_delay,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    return PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_delay,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
    )


@pytest.fixture
def poi_partially_received(
    purchase_order, variant_delay, shipment, nonowned_warehouse, completed_receipt
):
    Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant_delay,
        defaults={"quantity": 1000, "quantity_allocated": 0},
    )
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_delay,
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
    return poi


@pytest.fixture
def poia_unreceived(poi_unreceived, staff_user):
    return PurchaseOrderItemAdjustment.objects.create(
        purchase_order_item=poi_unreceived,
        quantity_change=-10,
        reason=PurchaseOrderItemAdjustmentReason.DELIVERY_SHORT,
        affects_payable=True,
        created_by=staff_user,
    )


@pytest.fixture
def stock_delay(owned_warehouse, variant_delay):
    return Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_delay,
        quantity=20,
        quantity_allocated=0,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_order(channel_USD, address):
    return Order.objects.create(
        channel=channel_USD,
        billing_address=address,
        shipping_address=address,
        status=OrderStatus.UNCONFIRMED,
        origin=OrderOrigin.CHECKOUT,
        lines_count=1,
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_delay_detaches_poi_and_deletes_poia(
    purchase_order,
    poi_unreceived,
    poia_unreceived,
    completed_receipt,
    staff_user,
):
    """Delaying an unreceived POI detaches it and deletes the auto-created POIA."""
    # given
    poia_pk = poia_unreceived.pk
    assert poi_unreceived.shipment is not None
    assert poi_unreceived.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION

    # when
    result = delay_for_future_shipment(
        receipt=completed_receipt,
        product=poi_unreceived.product_variant.product,
        user=staff_user,
    )

    # then: returns the delayed POIs
    assert len(result) == 1
    assert result[0].pk == poi_unreceived.pk

    # and: POI is detached from shipment and back to CONFIRMED
    poi_unreceived.refresh_from_db()
    assert poi_unreceived.shipment is None
    assert poi_unreceived.status == PurchaseOrderItemStatus.CONFIRMED

    # and: the POIA is deleted (no adjustment actually happened)
    assert not PurchaseOrderItemAdjustment.objects.filter(pk=poia_pk).exists()


def test_delay_preserves_allocations(
    channel_USD,
    purchase_order,
    poi_unreceived,
    poia_unreceived,
    stock_delay,
    variant_delay,
    completed_receipt,
    staff_user,
):
    """Allocations remain intact after delaying — orders still expect the stock."""
    addr = purchase_order.source_warehouse.address
    order = _make_order(channel_USD, addr)
    line = OrderLine.objects.create(
        order=order,
        variant=variant_delay,
        quantity=10,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("100.00"),
        total_price_net_amount=Decimal("100.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
    )
    _make_alloc_source(poi_unreceived, line, stock_delay, 10)

    # when
    delay_for_future_shipment(
        receipt=completed_receipt,
        product=variant_delay.product,
        user=staff_user,
    )

    # then: allocation source still points to the POI
    as_total = (
        AllocationSource.objects.filter(purchase_order_item=poi_unreceived).aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )
    assert as_total == 10

    # and: POI quantity_allocated is unchanged
    poi_unreceived.refresh_from_db()
    assert poi_unreceived.quantity_allocated == 10


def test_delay_rejects_partially_received(
    purchase_order,
    poi_partially_received,
    completed_receipt,
    staff_user,
):
    """Cannot delay a POI that was partially received."""
    PurchaseOrderItemAdjustment.objects.create(
        purchase_order_item=poi_partially_received,
        quantity_change=-3,
        reason=PurchaseOrderItemAdjustmentReason.DELIVERY_SHORT,
        affects_payable=True,
        created_by=staff_user,
    )

    with pytest.raises(ValueError, match="No unreceived POIs"):
        delay_for_future_shipment(
            receipt=completed_receipt,
            product=poi_partially_received.product_variant.product,
            user=staff_user,
        )


def test_delay_rejects_when_no_requires_attention_pois(
    purchase_order,
    variant_delay,
    completed_receipt,
    staff_user,
):
    """Raises when there are no REQUIRES_ATTENTION POIs for the product."""
    with pytest.raises(ValueError, match="No unreceived POIs"):
        delay_for_future_shipment(
            receipt=completed_receipt,
            product=variant_delay.product,
            user=staff_user,
        )

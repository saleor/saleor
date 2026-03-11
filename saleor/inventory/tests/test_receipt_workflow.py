"""Tests for receipt workflow (start_receipt, receive_item, complete_receipt, etc)."""

import pytest
from django.utils import timezone

from ...order import FulfillmentStatus, OrderOrigin, OrderStatus
from ...order.models import Fulfillment
from ...warehouse.models import Allocation, AllocationSource, Stock
from .. import PurchaseOrderItemStatus, ReceiptStatus
from ..exceptions import (
    ReceiptLineNotInProgress,
    ReceiptNotInProgress,
)
from ..models import (
    PurchaseOrderItem,
    PurchaseOrderRequestedAllocation,
    Receipt,
    ReceiptLine,
)
from ..receipt_workflow import (
    complete_receipt,
    delete_receipt,
    delete_receipt_line,
    receive_item,
    start_receipt,
)
from ..stock_management import confirm_purchase_order_item

# Tests for start_receipt function


def test_creates_receipt_successfully(shipment, staff_user):
    # given: a shipment without a receipt
    # when: starting a receipt
    receipt = start_receipt(shipment, user=staff_user)

    # then: receipt is created with correct status
    assert receipt.shipment == shipment
    assert receipt.status == ReceiptStatus.IN_PROGRESS
    assert receipt.created_by == staff_user
    assert receipt.created_at is not None
    assert receipt.completed_at is None


def test_resumes_existing_in_progress_receipt(shipment, staff_user):
    # given: a shipment with an in-progress receipt
    existing_receipt = start_receipt(shipment, user=staff_user)

    # when: starting another receipt for same shipment
    receipt = start_receipt(shipment, user=staff_user)

    # then: returns the existing receipt
    assert receipt.id == existing_receipt.id
    assert receipt.status == ReceiptStatus.IN_PROGRESS


def test_error_when_shipment_already_received(shipment, staff_user):
    # given: a shipment that has already been received
    shipment.arrived_at = timezone.now()
    shipment.save()

    # when/then: starting a receipt raises error
    with pytest.raises(ValueError, match="already marked as received"):
        start_receipt(shipment, user=staff_user)


def test_error_when_shipment_has_completed_receipt(
    shipment, staff_user, receipt_factory
):
    # given: a shipment with a completed receipt
    receipt_factory(shipment=shipment, status=ReceiptStatus.COMPLETED)

    # when/then: starting a new receipt raises error
    with pytest.raises(ValueError, match="already has a receipt"):
        start_receipt(shipment, user=staff_user)


# Tests for receive_item function


def test_receives_item_successfully(receipt, purchase_order_item, variant, staff_user):
    # given: an in-progress receipt and a POI with 0 received
    assert purchase_order_item.quantity_received == 0

    # when: receiving an item
    line = receive_item(receipt, variant, quantity=50, user=staff_user, notes="Test")

    # then: ReceiptLine created and POI updated
    assert line.receipt == receipt
    assert line.purchase_order_item == purchase_order_item
    assert line.quantity_received == 50
    assert line.received_by == staff_user
    assert line.notes == "Test"

    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_received == 50


def test_multiple_scans_increment_quantity(
    receipt, purchase_order_item, variant, staff_user
):
    # given: a POI that we scan multiple times
    receive_item(receipt, variant, quantity=30, user=staff_user)

    # when: scanning the same item again
    receive_item(receipt, variant, quantity=20, user=staff_user)

    # then: quantity_received is cumulative
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_received == 50

    # and: two separate receipt lines exist
    assert receipt.lines.count() == 2


def test_error_when_receipt_not_in_progress(receipt, variant, staff_user):
    # given: a completed receipt
    receipt.status = ReceiptStatus.COMPLETED
    receipt.save()

    # when/then: trying to receive items raises error
    with pytest.raises(ReceiptNotInProgress):
        receive_item(receipt, variant, quantity=10, user=staff_user)


def test_error_when_variant_not_in_shipment(
    receipt, product_variant_factory, staff_user
):
    # given: a variant whose product has no POIs on this shipment
    other_variant = product_variant_factory()

    # when/then: trying to receive it raises error
    with pytest.raises(ValueError, match="does not belong to any product"):
        receive_item(receipt, other_variant, quantity=10, user=staff_user)


def test_audit_trail_captured(receipt, purchase_order_item, variant, staff_user):
    # given/when: receiving an item
    before = timezone.now()
    line = receive_item(receipt, variant, quantity=10, user=staff_user)
    after = timezone.now()

    # then: audit fields are populated
    assert line.received_by == staff_user
    assert before <= line.received_at <= after


# Tests for complete_receipt function


def test_completes_receipt_with_no_discrepancies(
    receipt, purchase_order_item, staff_user, receipt_line_factory
):
    # given: a receipt where received == ordered
    purchase_order_item.quantity_ordered = 100
    purchase_order_item.save()

    receipt_line_factory(
        receipt=receipt,
        purchase_order_item=purchase_order_item,
        quantity_received=100,
        received_by=staff_user,
    )

    # when: completing the receipt
    result = complete_receipt(receipt, user=staff_user)

    # then: no adjustments created
    assert result["discrepancies"] == 0
    assert "adjustments_created" not in result
    assert len(result["adjustments_pending"]) == 0

    # and: receipt is completed
    receipt.refresh_from_db()
    assert receipt.status == ReceiptStatus.COMPLETED
    assert receipt.completed_at is not None
    assert receipt.completed_by == staff_user

    # and: POI status updated
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.status == "received"

    # and: shipment marked arrived
    assert receipt.shipment.arrived_at is not None


def test_creates_pending_poia_for_delivery_short(
    receipt, purchase_order_item, staff_user, receipt_line_factory
):
    # given: received less than ordered (single-variant shortage)
    purchase_order_item.quantity_ordered = 100
    purchase_order_item.save()

    receipt_line_factory(
        receipt=receipt,
        purchase_order_item=purchase_order_item,
        quantity_received=98,
        received_by=staff_user,
    )

    # when: completing the receipt
    result = complete_receipt(receipt, user=staff_user)

    # then: POIA created as pending (needs manual resolution)
    assert result["discrepancies"] == 1
    assert len(result["adjustments_pending"]) == 1
    assert "adjustments_created" not in result

    adjustment = result["adjustments_pending"][0]
    assert adjustment.quantity_change == -2
    assert adjustment.reason == "delivery_short"
    assert adjustment.affects_payable is True
    assert adjustment.processed_at is None

    # and: POI marked as requires attention
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION


def test_overage_creates_pending_poia(
    receipt, purchase_order_item, staff_user, receipt_line_factory
):
    # given: received more than ordered
    purchase_order_item.quantity_ordered = 100
    purchase_order_item.save()

    receipt_line_factory(
        receipt=receipt,
        purchase_order_item=purchase_order_item,
        quantity_received=105,
        received_by=staff_user,
    )

    # when: completing the receipt
    result = complete_receipt(receipt, user=staff_user)

    # then: POIA created for the overage
    assert result["discrepancies"] == 1
    assert len(result["adjustments_pending"]) == 1

    adjustment = result["adjustments_pending"][0]
    assert adjustment.quantity_change == 5
    assert adjustment.reason == "cycle_count_pos"
    assert adjustment.affects_payable is True
    assert adjustment.processed_at is None

    # and: POI marked as requires attention
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION


def test_sends_notification_for_pending_adjustments(
    receipt, purchase_order_item, staff_user, mocker, receipt_line_factory
):
    # given: a shortage
    purchase_order_item.quantity_ordered = 100
    purchase_order_item.save()

    receipt_line_factory(
        receipt=receipt,
        purchase_order_item=purchase_order_item,
        quantity_received=90,
        received_by=staff_user,
    )

    # and: a plugin manager
    mock_manager = mocker.Mock()

    # when: completing the receipt
    complete_receipt(receipt, user=staff_user, manager=mock_manager)

    # then: notification sent for pending adjustments
    mock_manager.notify.assert_called_once()
    call_args = mock_manager.notify.call_args
    assert call_args[0][0] == "pending_adjustments"


def test_error_when_completing_receipt_not_in_progress(receipt, staff_user):
    # given: a completed receipt
    receipt.status = ReceiptStatus.COMPLETED
    receipt.save()

    # when/then: trying to complete again raises error
    with pytest.raises(ReceiptNotInProgress):
        complete_receipt(receipt, user=staff_user)


# Tests for delete_receipt function


def test_deletes_receipt_and_reverts_quantities(
    receipt, purchase_order_item, variant, staff_user
):
    # given: a receipt with received items
    receive_item(receipt, variant, quantity=50, user=staff_user)
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_received == 50

    # when: deleting the receipt
    delete_receipt(receipt)

    # then: receipt is deleted
    from ...inventory.models import Receipt

    assert not Receipt.objects.filter(id=receipt.id).exists()

    # and: POI quantity reverted
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_received == 0


def test_error_when_receipt_completed(receipt, staff_user):
    # given: a completed receipt
    receipt.status = ReceiptStatus.COMPLETED
    receipt.save()

    # when/then: deleting raises error
    with pytest.raises(ReceiptNotInProgress):
        delete_receipt(receipt)


# Tests for delete_receipt_line function


def test_deletes_line_and_reverts_quantity(
    receipt, purchase_order_item, variant, staff_user
):
    # given: a receipt line
    line = receive_item(receipt, variant, quantity=50, user=staff_user)
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_received == 50

    # when: deleting the line
    delete_receipt_line(line)

    # then: line is deleted
    from ...inventory.models import ReceiptLine

    assert not ReceiptLine.objects.filter(id=line.id).exists()

    # and: POI quantity reverted
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_received == 0


def test_only_reverts_deleted_line_quantity(
    receipt, purchase_order_item, variant, staff_user
):
    # given: multiple lines for same POI
    line1 = receive_item(receipt, variant, quantity=30, user=staff_user)
    line2 = receive_item(receipt, variant, quantity=20, user=staff_user)
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_received == 50

    # when: deleting only line1
    delete_receipt_line(line1)

    # then: only line1's quantity reverted
    purchase_order_item.refresh_from_db()
    assert purchase_order_item.quantity_received == 20

    # and: line2 still exists
    from ...inventory.models import ReceiptLine

    assert ReceiptLine.objects.filter(id=line2.id).exists()


def test_error_when_receipt_line_completed(
    receipt, purchase_order_item, variant, staff_user
):
    # given: a line from a completed receipt
    line = receive_item(receipt, variant, quantity=50, user=staff_user)
    receipt.status = ReceiptStatus.COMPLETED
    receipt.save()

    # when/then: deleting the line raises error
    with pytest.raises(ReceiptLineNotInProgress):
        delete_receipt_line(line)


# Tests for fulfillment creation via complete_receipt


@pytest.fixture
def order_with_poi_and_receipt(
    order,
    nonowned_warehouse,
    owned_warehouse,
    purchase_order,
    variant,
    shipment,
    staff_user,
):
    """Scenario: UNCONFIRMED order -> POI confirmed -> in-progress receipt.

    Sets up an order with an allocation at nonowned_warehouse and a POI linked
    to the shipment. POI is NOT yet confirmed - the test controls that step.
    """
    order.status = OrderStatus.UNCONFIRMED
    order.save()

    line = order.lines.create(
        product_name=variant.product.name,
        variant_name=variant.name,
        product_sku=variant.sku,
        is_shipping_required=True,
        is_gift_card=False,
        quantity=5,
        variant=variant,
        unit_price_net_amount=10,
        unit_price_gross_amount=10,
        total_price_net_amount=50,
        total_price_gross_amount=50,
        undiscounted_unit_price_net_amount=10,
        undiscounted_unit_price_gross_amount=10,
        undiscounted_total_price_net_amount=50,
        undiscounted_total_price_gross_amount=50,
        currency="USD",
        tax_rate=0,
    )

    source_stock, _ = Stock.objects.get_or_create(
        warehouse=nonowned_warehouse,
        product_variant=variant,
        defaults={"quantity": 100, "quantity_allocated": 0},
    )

    allocation = Allocation.objects.create(
        order_line=line,
        stock=source_stock,
        quantity_allocated=5,
    )
    source_stock.quantity_allocated = 5
    source_stock.save()

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=5,
        total_price_amount=50.0,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
    )

    PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=poi.order, allocation=allocation
    )

    receipt = Receipt.objects.create(
        shipment=shipment,
        status=ReceiptStatus.IN_PROGRESS,
        created_by=staff_user,
    )

    return {"order": order, "line": line, "poi": poi, "receipt": receipt}


def test_confirm_poi_does_not_create_fulfillments_for_order(
    order_with_poi_and_receipt, staff_user
):
    # given
    order = order_with_poi_and_receipt["order"]
    poi = order_with_poi_and_receipt["poi"]

    assert Fulfillment.objects.filter(order=order).count() == 0

    # when
    confirm_purchase_order_item(poi, user=staff_user)

    # then
    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED
    assert Fulfillment.objects.filter(order=order).count() == 0


def test_complete_receipt_creates_fulfillments(order_with_poi_and_receipt, staff_user):
    # given
    order = order_with_poi_and_receipt["order"]
    poi = order_with_poi_and_receipt["poi"]
    receipt = order_with_poi_and_receipt["receipt"]

    confirm_purchase_order_item(poi, user=staff_user)

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED
    assert Fulfillment.objects.filter(order=order).count() == 0

    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi,
        quantity_received=5,
    )

    # when
    complete_receipt(receipt, user=staff_user)

    # then
    fulfillments = Fulfillment.objects.filter(order=order)
    assert fulfillments.count() == 1
    assert fulfillments.first().status == FulfillmentStatus.WAITING_FOR_APPROVAL


def test_complete_receipt_with_no_linked_orders_creates_no_fulfillments(
    receipt, purchase_order_item, staff_user, receipt_line_factory
):
    # given: POI has no order allocations (standalone stock receipt)
    purchase_order_item.quantity_ordered = 10
    purchase_order_item.save()

    receipt_line_factory(
        receipt=receipt,
        purchase_order_item=purchase_order_item,
        quantity_received=10,
        received_by=staff_user,
    )

    # when
    complete_receipt(receipt, user=staff_user)

    # then: no fulfillments since no orders are linked to this stock
    assert Fulfillment.objects.count() == 0


def test_variant_reallocation_adjusts_stock_quantity(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    product,
    channel_USD,
    staff_user,
):
    """Stock.quantity must be adjusted when reallocation moves entitlement across variants.

    Regression: reallocation updated Stock.quantity_allocated but not Stock.quantity,
    causing available_quantity to go negative and blocking fulfillment approval with
    InsufficientStock.

    Scenario: PO orders 6×S + 4×M (10 total). Receipt receives 4×S + 6×M.
    Reallocation succeeds (totals match). After reallocation:
      - stock_s.quantity should decrease by 2 (6→4)
      - stock_m.quantity should increase by 2 (4→6)
      - available_quantity (quantity - quantity_allocated) must be >= 0 for both
    """
    from decimal import Decimal

    from ...order import OrderStatus
    from ...order.models import Order, OrderLine
    from ...product.models import ProductVariant, ProductVariantChannelListing
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    # given - two variants of the same product
    variant_s = ProductVariant.objects.create(product=product, sku="STOCKFIX-S")
    variant_m = ProductVariant.objects.create(product=product, sku="STOCKFIX-M")
    for v in [variant_s, variant_m]:
        ProductVariantChannelListing.objects.create(
            variant=v,
            channel=channel_USD,
            price_amount=Decimal(10),
            discounted_price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )

    # given - stock at destination warehouse matching PO quantities
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_s,
        quantity=1000,
        quantity_allocated=0,
    )
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_m,
        quantity=1000,
        quantity_allocated=0,
    )
    stock_s = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_s,
        quantity=6,
        quantity_allocated=0,
    )
    stock_m = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_m,
        quantity=4,
        quantity_allocated=0,
    )

    # given - shipment and POIs: 6×S + 4×M
    ship = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-STOCKFIX",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    poi_s = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=6,
        total_price_amount=Decimal("60.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    poi_m = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_m,
        quantity_ordered=4,
        total_price_amount=Decimal("40.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # given - order with allocations: 6×S + 4×M
    addr = purchase_order.source_warehouse.address
    order_a = Order.objects.create(
        channel=channel_USD,
        billing_address=addr,
        shipping_address=addr,
        status=OrderStatus.UNCONFIRMED,
        lines_count=2,
    )
    line_a_s = OrderLine.objects.create(
        order=order_a,
        variant=variant_s,
        quantity=6,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("60.00"),
        total_price_net_amount=Decimal("60.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
    )
    line_a_m = OrderLine.objects.create(
        order=order_a,
        variant=variant_m,
        quantity=4,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("40.00"),
        total_price_net_amount=Decimal("40.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
    )

    alloc_s = Allocation.objects.create(
        order_line=line_a_s, stock=stock_s, quantity_allocated=6
    )
    stock_s.quantity_allocated = 6
    stock_s.save()
    poi_s.quantity_allocated = 6
    poi_s.save()
    AllocationSource.objects.create(
        purchase_order_item=poi_s, allocation=alloc_s, quantity=6
    )

    alloc_m = Allocation.objects.create(
        order_line=line_a_m, stock=stock_m, quantity_allocated=4
    )
    stock_m.quantity_allocated = 4
    stock_m.save()
    poi_m.quantity_allocated = 4
    poi_m.save()
    AllocationSource.objects.create(
        purchase_order_item=poi_m, allocation=alloc_m, quantity=4
    )

    # given - receipt with swapped quantities: 4×S + 6×M
    receipt = Receipt.objects.create(
        shipment=ship,
        status=ReceiptStatus.IN_PROGRESS,
        created_by=staff_user,
    )
    ReceiptLine.objects.create(
        receipt=receipt, purchase_order_item=poi_s, quantity_received=4
    )
    ReceiptLine.objects.create(
        receipt=receipt, purchase_order_item=poi_m, quantity_received=6
    )

    # when
    result = complete_receipt(receipt, user=staff_user)

    # then - reallocation succeeded, no POIAs
    assert result["adjustments_pending"] == []

    # then - Stock.quantity adjusted to match what was actually received
    stock_s.refresh_from_db()
    stock_m.refresh_from_db()
    assert stock_s.quantity == 4, (
        f"stock_s.quantity should be 4 (received 4, not 6), got {stock_s.quantity}"
    )
    assert stock_m.quantity == 6, (
        f"stock_m.quantity should be 6 (received 6, not 4), got {stock_m.quantity}"
    )

    # then - available_quantity must not be negative
    assert stock_s.quantity >= stock_s.quantity_allocated, (
        f"stock_s over-allocated: qty={stock_s.quantity} alloc={stock_s.quantity_allocated}"
    )
    assert stock_m.quantity >= stock_m.quantity_allocated, (
        f"stock_m over-allocated: qty={stock_m.quantity} alloc={stock_m.quantity_allocated}"
    )


def test_complete_receipt_updates_quantity_ordered_after_balanced_reallocation(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    product,
    channel_USD,
    staff_user,
):
    """When total received == ordered but variant mix differs, reallocation succeeds.

    Variant reallocation should succeed AND quantity_ordered on each POI should be
    updated to match quantity_received. No POIAs should be created.
    """
    from decimal import Decimal

    from ...order import OrderStatus
    from ...order.models import Order, OrderLine
    from ...product.models import ProductVariant, ProductVariantChannelListing
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    # given - two variants of the same product
    variant_s = ProductVariant.objects.create(product=product, sku="REALLOC-S")
    variant_m = ProductVariant.objects.create(product=product, sku="REALLOC-M")
    for v in [variant_s, variant_m]:
        ProductVariantChannelListing.objects.create(
            variant=v,
            channel=channel_USD,
            price_amount=Decimal(10),
            discounted_price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )

    # given - stock at both warehouses
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_s,
        quantity=1000,
        quantity_allocated=0,
    )
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_m,
        quantity=1000,
        quantity_allocated=0,
    )
    stock_s = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_s,
        quantity=10,
        quantity_allocated=0,
    )
    stock_m = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_m,
        quantity=10,
        quantity_allocated=0,
    )

    # given - a shipment and two confirmed POIs: 6×S and 4×M (10 total)
    ship = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-REALLOC",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    poi_s = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=6,
        total_price_amount=Decimal("60.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    poi_m = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_m,
        quantity_ordered=4,
        total_price_amount=Decimal("40.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # given - one order with allocation sources: 6×S + 4×M = 10 total
    addr = purchase_order.source_warehouse.address
    order_a = Order.objects.create(
        channel=channel_USD,
        billing_address=addr,
        shipping_address=addr,
        status=OrderStatus.UNCONFIRMED,
        lines_count=2,
    )
    line_a_s = OrderLine.objects.create(
        order=order_a,
        variant=variant_s,
        quantity=6,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("60.00"),
        total_price_net_amount=Decimal("60.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
    )
    line_a_m = OrderLine.objects.create(
        order=order_a,
        variant=variant_m,
        quantity=4,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("40.00"),
        total_price_net_amount=Decimal("40.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
    )

    # Wire up allocations + allocation sources
    alloc_s = Allocation.objects.create(
        order_line=line_a_s,
        stock=stock_s,
        quantity_allocated=6,
    )
    stock_s.quantity_allocated = 6
    stock_s.save()
    poi_s.quantity_allocated = 6
    poi_s.save()
    AllocationSource.objects.create(
        purchase_order_item=poi_s,
        allocation=alloc_s,
        quantity=6,
    )

    alloc_m = Allocation.objects.create(
        order_line=line_a_m,
        stock=stock_m,
        quantity_allocated=4,
    )
    stock_m.quantity_allocated = 4
    stock_m.save()
    poi_m.quantity_allocated = 4
    poi_m.save()
    AllocationSource.objects.create(
        purchase_order_item=poi_m,
        allocation=alloc_m,
        quantity=4,
    )

    # given - receipt with swapped quantities: 4×S and 6×M (still 10 total)
    receipt = Receipt.objects.create(
        shipment=ship,
        status=ReceiptStatus.IN_PROGRESS,
        created_by=staff_user,
    )
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi_s,
        quantity_received=4,
    )
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi_m,
        quantity_received=6,
    )

    # when
    result = complete_receipt(receipt, user=staff_user)

    # then - no POIAs since product-level totals balance
    assert result["adjustments_pending"] == []

    # then - quantity_ordered updated to match received
    poi_s.refresh_from_db()
    poi_m.refresh_from_db()
    assert poi_s.quantity_ordered == 4
    assert poi_m.quantity_ordered == 6

    # then - both POIs marked as received, not requires_attention
    assert poi_s.status == PurchaseOrderItemStatus.RECEIVED
    assert poi_m.status == PurchaseOrderItemStatus.RECEIVED


# Tests for receive_item FIFO with multiple POIs per variant


def test_receive_item_fifo_fills_first_poi(
    receipt,
    purchase_order,
    variant,
    shipment,
    staff_user,
):
    # given: two POIs for the same variant, ordered by pk
    poi_a = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=30,
        total_price_amount=300,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=20,
        total_price_amount=200,
        currency="USD",
        shipment=shipment,
        country_of_origin="CN",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # when: receiving 10 units
    line = receive_item(receipt, variant, quantity=10, user=staff_user)

    # then: goes to first POI (FIFO)
    assert line.purchase_order_item == poi_a


def test_receive_item_fifo_overflows_to_second_poi(
    receipt,
    purchase_order,
    variant,
    shipment,
    staff_user,
    receipt_line_factory,
):
    # given: two POIs, first is already full
    poi_a = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=10,
        total_price_amount=100,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    poi_b = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=20,
        total_price_amount=200,
        currency="USD",
        shipment=shipment,
        country_of_origin="CN",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # fill first POI to capacity
    receipt_line_factory(
        receipt=receipt,
        purchase_order_item=poi_a,
        quantity_received=10,
        received_by=staff_user,
    )

    # when: receiving more
    line = receive_item(receipt, variant, quantity=5, user=staff_user)

    # then: overflows to second POI
    assert line.purchase_order_item == poi_b


# Tests for receiving unexpected variant (same product, different size)


def test_receive_unexpected_variant_creates_zero_qty_poi(
    receipt,
    purchase_order,
    product,
    variant,
    shipment,
    staff_user,
    product_variant_factory,
):
    # given: a POI for variant_s on the shipment
    from ...product.models import ProductVariant

    variant_s = variant
    variant_m = ProductVariant.objects.create(product=product, sku="UNEXP-M")

    PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=10,
        total_price_amount=100,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # when: receiving variant_m (same product, not on any POI)
    line = receive_item(receipt, variant_m, quantity=5, user=staff_user)

    # then: a zero-qty POI was created for variant_m
    new_poi = line.purchase_order_item
    assert new_poi.product_variant == variant_m
    assert new_poi.quantity_ordered == 0
    assert new_poi.total_price_amount is None
    assert new_poi.currency == "USD"
    assert new_poi.country_of_origin == "US"
    assert new_poi.status == PurchaseOrderItemStatus.CONFIRMED
    assert new_poi.shipment == shipment
    assert new_poi.order == purchase_order
    assert line.quantity_received == 5


def test_receive_unexpected_variant_reuses_existing_zero_qty_poi(
    receipt,
    purchase_order,
    product,
    variant,
    shipment,
    staff_user,
):
    # given: a POI for variant_s and we already received variant_m once
    from ...product.models import ProductVariant

    variant_s = variant
    variant_m = ProductVariant.objects.create(product=product, sku="REUSE-M")

    PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=10,
        total_price_amount=100,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # first scan creates the zero-qty POI
    line1 = receive_item(receipt, variant_m, quantity=3, user=staff_user)
    created_poi = line1.purchase_order_item

    # when: scanning variant_m again
    line2 = receive_item(receipt, variant_m, quantity=2, user=staff_user)

    # then: reuses the same POI (no duplicate)
    assert line2.purchase_order_item == created_poi
    assert (
        PurchaseOrderItem.objects.filter(
            shipment=shipment, product_variant=variant_m
        ).count()
        == 1
    )


def test_receive_unexpected_variant_mixed_origin_raises(
    receipt,
    purchase_order,
    product,
    variant,
    shipment,
    staff_user,
):
    # given: two POIs for the same product but different countries of origin
    from ...product.models import ProductVariant

    variant_s = variant
    variant_m = ProductVariant.objects.create(product=product, sku="MIXORG-M")
    variant_l = ProductVariant.objects.create(product=product, sku="MIXORG-L")

    PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=10,
        total_price_amount=100,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_m,
        quantity_ordered=5,
        total_price_amount=50,
        currency="USD",
        shipment=shipment,
        country_of_origin="CN",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # when/then: receiving variant_l raises because siblings have mixed origins
    with pytest.raises(ValueError, match="mixed countries of origin"):
        receive_item(receipt, variant_l, quantity=3, user=staff_user)


def test_receive_variant_from_unrelated_product_raises(
    receipt,
    purchase_order,
    variant,
    shipment,
    staff_user,
):
    # given: a POI for variant on the shipment
    from ...product.models import Product, ProductType, ProductVariant

    PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=10,
        total_price_amount=100,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # and: a variant from a completely different product
    other_product_type = ProductType.objects.create(
        name="Other Type", slug="other-type"
    )
    other_product = Product.objects.create(
        name="Other Product",
        slug="other-product",
        product_type=other_product_type,
    )
    alien_variant = ProductVariant.objects.create(product=other_product, sku="ALIEN-V")

    # when/then: receiving it raises error
    with pytest.raises(ValueError, match="does not belong to any product"):
        receive_item(receipt, alien_variant, quantity=5, user=staff_user)


def test_receive_unexpected_variant_full_substitution_reallocation(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    product,
    channel_USD,
    staff_user,
):
    """Full substitution: ordered variant_s, received only variant_m.

    receive_item creates a zero-qty POI for variant_m. On complete_receipt,
    variant reallocation redistributes to orders that expected variant_s.
    """
    from decimal import Decimal

    from ...order import OrderStatus
    from ...order.models import Order, OrderLine
    from ...product.models import ProductVariant, ProductVariantChannelListing
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    # given: two variants of the same product
    variant_s = ProductVariant.objects.create(product=product, sku="FULLSUB-S")
    variant_m = ProductVariant.objects.create(product=product, sku="FULLSUB-M")
    for v in [variant_s, variant_m]:
        ProductVariantChannelListing.objects.create(
            variant=v,
            channel=channel_USD,
            price_amount=Decimal(10),
            discounted_price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )

    # given: stock at both warehouses
    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_s,
        quantity=1000,
        quantity_allocated=0,
    )
    stock_s = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_s,
        quantity=5,
        quantity_allocated=0,
    )
    Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_m,
        quantity=0,
        quantity_allocated=0,
    )

    # given: shipment with POI for variant_s only
    ship = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-FULLSUB",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    poi_s = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=5,
        total_price_amount=Decimal("50.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # given: order allocated against variant_s
    addr = purchase_order.source_warehouse.address
    order_a = Order.objects.create(
        channel=channel_USD,
        billing_address=addr,
        shipping_address=addr,
        status=OrderStatus.UNCONFIRMED,
        lines_count=1,
    )
    line_a_s = OrderLine.objects.create(
        order=order_a,
        variant=variant_s,
        quantity=5,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("50.00"),
        total_price_net_amount=Decimal("50.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
    )
    alloc_s = Allocation.objects.create(
        order_line=line_a_s, stock=stock_s, quantity_allocated=5
    )
    stock_s.quantity_allocated = 5
    stock_s.save()
    poi_s.quantity_allocated = 5
    poi_s.save()
    AllocationSource.objects.create(
        purchase_order_item=poi_s, allocation=alloc_s, quantity=5
    )

    # given: start receipt and receive variant_m instead of variant_s
    receipt = Receipt.objects.create(
        shipment=ship,
        status=ReceiptStatus.IN_PROGRESS,
        created_by=staff_user,
    )
    line = receive_item(receipt, variant_m, quantity=5, user=staff_user)
    poi_m = line.purchase_order_item
    assert poi_m.quantity_ordered == 0
    assert poi_m.product_variant == variant_m

    # also record 0 received for variant_s (via receipt line on its POI)
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi_s,
        quantity_received=0,
    )

    # when: completing the receipt
    result = complete_receipt(receipt, user=staff_user)

    # then: reallocation succeeded — no pending adjustments
    assert result["adjustments_pending"] == []

    # then: order_a now has variant_m instead of variant_s
    new_ass = AllocationSource.objects.filter(
        allocation__order_line__order=order_a
    ).select_related("purchase_order_item__product_variant")
    assert new_ass.count() == 1
    assert new_ass.first().purchase_order_item.product_variant == variant_m

    # then: stock quantities reflect what was actually received
    stock_s.refresh_from_db()
    stock_m = Stock.objects.get(warehouse=owned_warehouse, product_variant=variant_m)
    assert stock_s.quantity == 0, "S stock should be 0 (received 0, was 5)"
    assert stock_m.quantity == 5, "M stock should be 5 (received 5, was 0)"

    # then: stock.quantity_allocated matches sum of Allocations
    from django.db.models import Sum

    for s in [stock_s, stock_m]:
        alloc_sum = (
            Allocation.objects.filter(stock=s).aggregate(t=Sum("quantity_allocated"))[
                "t"
            ]
            or 0
        )
        assert s.quantity_allocated == alloc_sum, (
            f"Stock {s.product_variant.sku}: quantity_allocated={s.quantity_allocated} "
            f"!= sum(Allocation)={alloc_sum}"
        )

    # then: no negative available stock
    assert stock_s.quantity >= stock_s.quantity_allocated
    assert stock_m.quantity >= stock_m.quantity_allocated

    # then: total physical stock conserved across variants
    assert stock_s.quantity + stock_m.quantity == 5


def test_receive_unexpected_variant_partial_substitution_reallocation(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    product,
    channel_USD,
    staff_user,
):
    """Partial substitution: ordered 10×S, received 7×S + 3×M.

    variant_m has no POI initially. receive_item creates one.
    Reallocation redistributes so orders get the right total.
    """
    from decimal import Decimal

    from ...order import OrderStatus
    from ...order.models import Order, OrderLine
    from ...product.models import ProductVariant, ProductVariantChannelListing
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    variant_s = ProductVariant.objects.create(product=product, sku="PARTSUB-S")
    variant_m = ProductVariant.objects.create(product=product, sku="PARTSUB-M")
    for v in [variant_s, variant_m]:
        ProductVariantChannelListing.objects.create(
            variant=v,
            channel=channel_USD,
            price_amount=Decimal(10),
            discounted_price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )

    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_s,
        quantity=1000,
        quantity_allocated=0,
    )
    stock_s = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_s,
        quantity=10,
        quantity_allocated=0,
    )
    Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_m,
        quantity=0,
        quantity_allocated=0,
    )

    ship = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-PARTSUB",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    poi_s = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    addr = purchase_order.source_warehouse.address
    order_a = Order.objects.create(
        channel=channel_USD,
        billing_address=addr,
        shipping_address=addr,
        status=OrderStatus.UNCONFIRMED,
        lines_count=1,
    )
    line_a = OrderLine.objects.create(
        order=order_a,
        variant=variant_s,
        quantity=10,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("100.00"),
        total_price_net_amount=Decimal("100.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
    )
    alloc = Allocation.objects.create(
        order_line=line_a, stock=stock_s, quantity_allocated=10
    )
    stock_s.quantity_allocated = 10
    stock_s.save()
    poi_s.quantity_allocated = 10
    poi_s.save()
    AllocationSource.objects.create(
        purchase_order_item=poi_s, allocation=alloc, quantity=10
    )

    # given: receive 7×S + 3×M (variant_m creates zero-qty POI)
    receipt = Receipt.objects.create(
        shipment=ship,
        status=ReceiptStatus.IN_PROGRESS,
        created_by=staff_user,
    )
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi_s,
        quantity_received=7,
    )
    receive_item(receipt, variant_m, quantity=3, user=staff_user)

    # when
    result = complete_receipt(receipt, user=staff_user)

    # then: reallocation succeeded, total allocation preserved
    assert result["adjustments_pending"] == []

    total_allocated = sum(
        a.quantity
        for a in AllocationSource.objects.filter(allocation__order_line__order=order_a)
    )
    assert total_allocated == 10

    # then: stock quantities reflect what was actually received
    stock_s.refresh_from_db()
    stock_m = Stock.objects.get(warehouse=owned_warehouse, product_variant=variant_m)
    assert stock_s.quantity == 7, "S stock should be 7 (received 7, was 10)"
    assert stock_m.quantity == 3, "M stock should be 3 (received 3, was 0)"

    # then: stock.quantity_allocated matches sum of Allocations
    from django.db.models import Sum

    for s in [stock_s, stock_m]:
        alloc_sum = (
            Allocation.objects.filter(stock=s).aggregate(t=Sum("quantity_allocated"))[
                "t"
            ]
            or 0
        )
        assert s.quantity_allocated == alloc_sum, (
            f"Stock {s.product_variant.sku}: quantity_allocated={s.quantity_allocated} "
            f"!= sum(Allocation)={alloc_sum}"
        )

    # then: no negative available stock
    assert stock_s.quantity >= stock_s.quantity_allocated
    assert stock_m.quantity >= stock_m.quantity_allocated

    # then: total physical stock conserved (was 10, received 10)
    assert stock_s.quantity + stock_m.quantity == 10


def test_receive_unexpected_variant_shortage_creates_poia(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    product,
    channel_USD,
    staff_user,
):
    """Shortage: ordered 10×S, received 3×S + 4×M = 7 total (need 10).

    Reallocation fails (shortage), POIAs created for both POIs.
    """
    from decimal import Decimal

    from ...order import OrderStatus
    from ...order.models import Order, OrderLine
    from ...product.models import ProductVariant, ProductVariantChannelListing
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    variant_s = ProductVariant.objects.create(product=product, sku="SHORT-S")
    variant_m = ProductVariant.objects.create(product=product, sku="SHORT-M")
    for v in [variant_s, variant_m]:
        ProductVariantChannelListing.objects.create(
            variant=v,
            channel=channel_USD,
            price_amount=Decimal(10),
            discounted_price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )

    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_s,
        quantity=1000,
        quantity_allocated=0,
    )
    stock_s = Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_s,
        quantity=10,
        quantity_allocated=0,
    )
    Stock.objects.create(
        warehouse=owned_warehouse,
        product_variant=variant_m,
        quantity=0,
        quantity_allocated=0,
    )

    ship = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-SHORT",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    poi_s = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=10,
        total_price_amount=Decimal("100.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    addr = purchase_order.source_warehouse.address
    order_a = Order.objects.create(
        channel=channel_USD,
        billing_address=addr,
        shipping_address=addr,
        status=OrderStatus.UNCONFIRMED,
        lines_count=1,
    )
    line_a = OrderLine.objects.create(
        order=order_a,
        variant=variant_s,
        quantity=10,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("100.00"),
        total_price_net_amount=Decimal("100.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
    )
    alloc = Allocation.objects.create(
        order_line=line_a, stock=stock_s, quantity_allocated=10
    )
    stock_s.quantity_allocated = 10
    stock_s.save()
    poi_s.quantity_allocated = 10
    poi_s.save()
    AllocationSource.objects.create(
        purchase_order_item=poi_s, allocation=alloc, quantity=10
    )

    # given: receive 3×S + 4×M = 7 total (shortage of 3)
    receipt = Receipt.objects.create(
        shipment=ship,
        status=ReceiptStatus.IN_PROGRESS,
        created_by=staff_user,
    )
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi_s,
        quantity_received=3,
    )
    receive_item(receipt, variant_m, quantity=4, user=staff_user)

    # when
    result = complete_receipt(receipt, user=staff_user)

    # then: reallocation failed (7 received < 10 needed), POIAs created
    assert len(result["adjustments_pending"]) > 0

    # then: POIs marked as requires_attention
    poi_s.refresh_from_db()
    assert poi_s.status == PurchaseOrderItemStatus.REQUIRES_ATTENTION

    # then: stock unchanged (reallocation raised before mutating)
    stock_s.refresh_from_db()
    assert stock_s.quantity == 10, (
        "S stock should be unchanged after failed reallocation"
    )
    assert stock_s.quantity_allocated == 10, "S allocation should be unchanged"

    # then: stock.quantity_allocated still matches sum of Allocations
    from django.db.models import Sum

    alloc_sum = (
        Allocation.objects.filter(stock=stock_s).aggregate(t=Sum("quantity_allocated"))[
            "t"
        ]
        or 0
    )
    assert stock_s.quantity_allocated == alloc_sum


def test_receive_unexpected_variant_surplus_creates_poia(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    product,
    channel_USD,
    staff_user,
):
    """Surplus: ordered 5×S, received 5×S + 3×M. S matches exactly.

    variant_m's zero-qty POI is the only discrepancy. No allocation sources
    exist for it, so reallocation is skipped. POIA created for the surplus.
    """
    from decimal import Decimal

    from ...product.models import ProductVariant, ProductVariantChannelListing
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    variant_s = ProductVariant.objects.create(product=product, sku="SURPLUS-S")
    variant_m = ProductVariant.objects.create(product=product, sku="SURPLUS-M")
    for v in [variant_s, variant_m]:
        ProductVariantChannelListing.objects.create(
            variant=v,
            channel=channel_USD,
            price_amount=Decimal(10),
            discounted_price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )

    Stock.objects.create(
        warehouse=nonowned_warehouse,
        product_variant=variant_s,
        quantity=1000,
        quantity_allocated=0,
    )

    ship = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-SURPLUS",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    poi_s = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=5,
        total_price_amount=Decimal("50.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # given: receive 5×S (exact match) + 3×M (unexpected surplus)
    receipt = Receipt.objects.create(
        shipment=ship,
        status=ReceiptStatus.IN_PROGRESS,
        created_by=staff_user,
    )
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi_s,
        quantity_received=5,
    )
    receive_item(receipt, variant_m, quantity=3, user=staff_user)

    # when
    result = complete_receipt(receipt, user=staff_user)

    # then: poi_s is received (exact match)
    poi_s.refresh_from_db()
    assert poi_s.status == PurchaseOrderItemStatus.RECEIVED

    # then: variant_m's POI gets a POIA for the surplus
    assert len(result["adjustments_pending"]) == 1
    adj = result["adjustments_pending"][0]
    assert adj.quantity_change == 3
    assert adj.reason == "cycle_count_pos"


def test_floor_stock_size_swap_auto_resolves(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    product,
    channel_USD,
    staff_user,
):
    """Size swap with balanced product total and no orders auto-resolves.

    Ordered 4×S + 4×M, received 2×S + 6×M. Total 8=8, no allocations.
    Should not create POIAs — just adjust quantity_ordered to match received.
    """
    from decimal import Decimal

    from ...product.models import ProductVariant, ProductVariantChannelListing
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    variant_s = ProductVariant.objects.create(product=product, sku="SWAP-S")
    variant_m = ProductVariant.objects.create(product=product, sku="SWAP-M")
    for v in [variant_s, variant_m]:
        ProductVariantChannelListing.objects.create(
            variant=v,
            channel=channel_USD,
            price_amount=Decimal(10),
            discounted_price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )

    ship = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="TEST-SWAP",
        shipping_cost_amount=Decimal("100.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    poi_s = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_s,
        quantity_ordered=4,
        total_price_amount=Decimal("40.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    poi_m = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_m,
        quantity_ordered=4,
        total_price_amount=Decimal("40.00"),
        currency="USD",
        shipment=ship,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # given: stock exists from PO confirmation (4×S + 4×M)
    from ...warehouse.models import Stock

    stock_s = Stock.objects.create(
        warehouse=owned_warehouse, product_variant=variant_s, quantity=4
    )
    stock_m = Stock.objects.create(
        warehouse=owned_warehouse, product_variant=variant_m, quantity=4
    )

    # given: receive 2×S + 6×M (size swap, total balanced)
    receipt = Receipt.objects.create(
        shipment=ship,
        status=ReceiptStatus.IN_PROGRESS,
        created_by=staff_user,
    )
    ReceiptLine.objects.create(
        receipt=receipt, purchase_order_item=poi_s, quantity_received=2
    )
    ReceiptLine.objects.create(
        receipt=receipt, purchase_order_item=poi_m, quantity_received=6
    )

    # when
    result = complete_receipt(receipt, user=staff_user)

    # then: no POIAs created — auto-resolved as floor stock size swap
    assert len(result["adjustments_pending"]) == 0

    # and: POIs adjusted to match received quantities
    poi_s.refresh_from_db()
    poi_m.refresh_from_db()
    assert poi_s.quantity_ordered == 2
    assert poi_m.quantity_ordered == 6
    assert poi_s.status == PurchaseOrderItemStatus.RECEIVED
    assert poi_m.status == PurchaseOrderItemStatus.RECEIVED

    # and: stock adjusted to match received quantities
    stock_s.refresh_from_db()
    stock_m.refresh_from_db()
    assert stock_s.quantity == 2
    assert stock_m.quantity == 6


def test_complete_receipt_fulfills_only_unfulfilled_quantities_across_shipments(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    product,
    channel_USD,
    staff_user,
):
    """Completing a second shipment's receipt only fulfills remaining quantities.

    Regression: when an order spanned two shipments and the first shipment's receipt
    created a WAITING_FOR_APPROVAL fulfillment, completing the second shipment's receipt
    tried to fulfill ALL allocated quantities (including already-fulfilled lines),
    raising "Only 0 items remaining to fulfill."

    Scenario:
      - Order with 2 lines: variant_a (qty 3), variant_b (qty 2)
      - Shipment 1 has POI for variant_a (qty 3)
      - Shipment 2 has POI for variant_b (qty 2)
      - Complete receipt for shipment 1 → fulfillment for variant_a only
      - Complete receipt for shipment 2 → should fulfill variant_b only
    """
    from decimal import Decimal

    from ...order.models import FulfillmentLine, Order, OrderLine
    from ...product.models import ProductVariant, ProductVariantChannelListing
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    # given - two variants
    variant_a = ProductVariant.objects.create(product=product, sku="MULTI-SHIP-A")
    variant_b = ProductVariant.objects.create(product=product, sku="MULTI-SHIP-B")
    for v in [variant_a, variant_b]:
        ProductVariantChannelListing.objects.create(
            variant=v,
            channel=channel_USD,
            price_amount=Decimal("10.00"),
            currency="USD",
        )

    stock_a = Stock.objects.create(
        warehouse=owned_warehouse, product_variant=variant_a, quantity=3
    )
    stock_b = Stock.objects.create(
        warehouse=owned_warehouse, product_variant=variant_b, quantity=2
    )

    # given - two shipments
    ship1 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="SHIP-1",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    ship2 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="SHIP-2",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )

    # given - POIs on different shipments
    poi_a = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_a,
        quantity_ordered=3,
        total_price_amount=Decimal("30.00"),
        currency="USD",
        shipment=ship1,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    poi_b = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_b,
        quantity_ordered=2,
        total_price_amount=Decimal("20.00"),
        currency="USD",
        shipment=ship2,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # given - order with two lines
    order = Order.objects.create(
        status=OrderStatus.UNFULFILLED,
        origin=OrderOrigin.CHECKOUT,
        channel=channel_USD,
        currency="USD",
        total_gross_amount=Decimal("50.00"),
        total_net_amount=Decimal("50.00"),
        undiscounted_total_gross_amount=Decimal("50.00"),
        undiscounted_total_net_amount=Decimal("50.00"),
        shipping_price_gross_amount=Decimal(0),
        shipping_price_net_amount=Decimal(0),
        lines_count=2,
    )
    line_a = OrderLine.objects.create(
        order=order,
        variant=variant_a,
        product_sku="MULTI-SHIP-A",
        quantity=3,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("30.00"),
        total_price_net_amount=Decimal("30.00"),
        undiscounted_unit_price_gross_amount=Decimal("10.00"),
        undiscounted_unit_price_net_amount=Decimal("10.00"),
        undiscounted_total_price_gross_amount=Decimal("30.00"),
        undiscounted_total_price_net_amount=Decimal("30.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
        tax_rate=0,
    )
    line_b = OrderLine.objects.create(
        order=order,
        variant=variant_b,
        product_sku="MULTI-SHIP-B",
        quantity=2,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("20.00"),
        total_price_net_amount=Decimal("20.00"),
        undiscounted_unit_price_gross_amount=Decimal("10.00"),
        undiscounted_unit_price_net_amount=Decimal("10.00"),
        undiscounted_total_price_gross_amount=Decimal("20.00"),
        undiscounted_total_price_net_amount=Decimal("20.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
        tax_rate=0,
    )

    # given - allocations linked to POIs
    alloc_a = Allocation.objects.create(
        order_line=line_a, stock=stock_a, quantity_allocated=3
    )
    alloc_b = Allocation.objects.create(
        order_line=line_b, stock=stock_b, quantity_allocated=2
    )
    AllocationSource.objects.create(
        purchase_order_item=poi_a, allocation=alloc_a, quantity=3
    )
    AllocationSource.objects.create(
        purchase_order_item=poi_b, allocation=alloc_b, quantity=2
    )

    # given - receipt for shipment 1 (variant_a only)
    receipt1 = Receipt.objects.create(
        shipment=ship1, status=ReceiptStatus.IN_PROGRESS, created_by=staff_user
    )
    ReceiptLine.objects.create(
        receipt=receipt1, purchase_order_item=poi_a, quantity_received=3
    )

    # when - complete receipt for shipment 1
    # poi_b is still CONFIRMED so order is excluded from fulfillment
    # (orders_with_pending filter catches it)
    complete_receipt(receipt1, user=staff_user)

    # then - no fulfillment yet (poi_b still pending on shipment 2)
    assert Fulfillment.objects.filter(order=order).count() == 0

    # given - receipt for shipment 2 (variant_b only)
    receipt2 = Receipt.objects.create(
        shipment=ship2, status=ReceiptStatus.IN_PROGRESS, created_by=staff_user
    )
    ReceiptLine.objects.create(
        receipt=receipt2, purchase_order_item=poi_b, quantity_received=2
    )

    # when - complete receipt for shipment 2
    complete_receipt(receipt2, user=staff_user)

    # then - fulfillment created covering all lines
    fulfillments = Fulfillment.objects.filter(order=order)
    assert fulfillments.count() == 1
    fulfillment = fulfillments.first()
    assert fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL

    fl_by_sku = {
        fl.order_line.product_sku: fl.quantity
        for fl in FulfillmentLine.objects.filter(
            fulfillment=fulfillment
        ).select_related("order_line")
    }
    assert fl_by_sku == {"MULTI-SHIP-A": 3, "MULTI-SHIP-B": 2}


def test_second_shipment_receipt_fulfills_remaining_after_partial_fulfillment(
    purchase_order,
    owned_warehouse,
    nonowned_warehouse,
    product,
    channel_USD,
    staff_user,
):
    """Second shipment fulfills only remaining unfulfilled quantities.

    When a first shipment already created a partial fulfillment, the second
    shipment's receipt should only fulfill the remaining unfulfilled quantities.

    Scenario:
      - Order with 2 lines: variant_a (qty 2), variant_b (qty 3)
      - Shipment 1 has POIs for both: variant_a (qty 1), variant_b (qty 3)
      - Shipment 2 has POI for variant_a (qty 1)
      - Complete receipt 1 → fulfillment for variant_a=1, variant_b=3
      - Complete receipt 2 → should fulfill only variant_a=1
    """
    from decimal import Decimal

    from ...order.models import FulfillmentLine, Order, OrderLine
    from ...product.models import ProductVariant, ProductVariantChannelListing
    from ...shipping import IncoTerm, ShipmentType
    from ...shipping.models import Shipment

    # given - two variants
    variant_a = ProductVariant.objects.create(product=product, sku="PARTIAL-A")
    variant_b = ProductVariant.objects.create(product=product, sku="PARTIAL-B")
    for v in [variant_a, variant_b]:
        ProductVariantChannelListing.objects.create(
            variant=v,
            channel=channel_USD,
            price_amount=Decimal("10.00"),
            currency="USD",
        )

    stock_a = Stock.objects.create(
        warehouse=owned_warehouse, product_variant=variant_a, quantity=2
    )
    stock_b = Stock.objects.create(
        warehouse=owned_warehouse, product_variant=variant_b, quantity=3
    )

    # given - two shipments
    ship1 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="PARTIAL-SHIP-1",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )
    ship2 = Shipment.objects.create(
        source=nonowned_warehouse.address,
        destination=owned_warehouse.address,
        shipment_type=ShipmentType.INBOUND,
        tracking_url="PARTIAL-SHIP-2",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        carrier="TEST",
        inco_term=IncoTerm.DDP,
    )

    # given - POIs split across shipments
    poi_a1 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_a,
        quantity_ordered=1,
        total_price_amount=Decimal("10.00"),
        currency="USD",
        shipment=ship1,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    poi_b = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_b,
        quantity_ordered=3,
        total_price_amount=Decimal("30.00"),
        currency="USD",
        shipment=ship1,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )
    poi_a2 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant_a,
        quantity_ordered=1,
        total_price_amount=Decimal("10.00"),
        currency="USD",
        shipment=ship2,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.CONFIRMED,
    )

    # given - order with two lines
    order = Order.objects.create(
        status=OrderStatus.UNFULFILLED,
        origin=OrderOrigin.CHECKOUT,
        channel=channel_USD,
        currency="USD",
        total_gross_amount=Decimal("50.00"),
        total_net_amount=Decimal("50.00"),
        undiscounted_total_gross_amount=Decimal("50.00"),
        undiscounted_total_net_amount=Decimal("50.00"),
        shipping_price_gross_amount=Decimal(0),
        shipping_price_net_amount=Decimal(0),
        lines_count=2,
    )
    line_a = OrderLine.objects.create(
        order=order,
        variant=variant_a,
        product_sku="PARTIAL-A",
        quantity=2,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("20.00"),
        total_price_net_amount=Decimal("20.00"),
        undiscounted_unit_price_gross_amount=Decimal("10.00"),
        undiscounted_unit_price_net_amount=Decimal("10.00"),
        undiscounted_total_price_gross_amount=Decimal("20.00"),
        undiscounted_total_price_net_amount=Decimal("20.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
        tax_rate=0,
    )
    line_b = OrderLine.objects.create(
        order=order,
        variant=variant_b,
        product_sku="PARTIAL-B",
        quantity=3,
        unit_price_gross_amount=Decimal("10.00"),
        unit_price_net_amount=Decimal("10.00"),
        total_price_gross_amount=Decimal("30.00"),
        total_price_net_amount=Decimal("30.00"),
        undiscounted_unit_price_gross_amount=Decimal("10.00"),
        undiscounted_unit_price_net_amount=Decimal("10.00"),
        undiscounted_total_price_gross_amount=Decimal("30.00"),
        undiscounted_total_price_net_amount=Decimal("30.00"),
        currency="USD",
        is_shipping_required=True,
        is_gift_card=False,
        tax_rate=0,
    )

    # given - allocations: line_a has 2 allocated (split across 2 POIs via sources)
    alloc_a = Allocation.objects.create(
        order_line=line_a, stock=stock_a, quantity_allocated=2
    )
    alloc_b = Allocation.objects.create(
        order_line=line_b, stock=stock_b, quantity_allocated=3
    )
    AllocationSource.objects.create(
        purchase_order_item=poi_a1, allocation=alloc_a, quantity=1
    )
    AllocationSource.objects.create(
        purchase_order_item=poi_a2, allocation=alloc_a, quantity=1
    )
    AllocationSource.objects.create(
        purchase_order_item=poi_b, allocation=alloc_b, quantity=3
    )

    # given - complete receipt for shipment 1 (variant_a=1, variant_b=3)
    # poi_a2 is still CONFIRMED on ship2, so order is excluded
    receipt1 = Receipt.objects.create(
        shipment=ship1, status=ReceiptStatus.IN_PROGRESS, created_by=staff_user
    )
    ReceiptLine.objects.create(
        receipt=receipt1, purchase_order_item=poi_a1, quantity_received=1
    )
    ReceiptLine.objects.create(
        receipt=receipt1, purchase_order_item=poi_b, quantity_received=3
    )
    complete_receipt(receipt1, user=staff_user)

    # then - no fulfillment yet (poi_a2 still pending)
    assert Fulfillment.objects.filter(order=order).count() == 0

    # given - manually create the fulfillment that would exist from a prior
    # shipment completing all its POIs (simulating the real scenario where
    # the first shipment's discrepancy resolution triggers fulfillment)
    from ...order.models import FulfillmentLine as FL

    f1 = Fulfillment.objects.create(
        order=order, status=FulfillmentStatus.WAITING_FOR_APPROVAL
    )
    FL.objects.create(fulfillment=f1, order_line=line_a, quantity=1, stock=stock_a)
    FL.objects.create(fulfillment=f1, order_line=line_b, quantity=3, stock=stock_b)
    line_a.quantity_fulfilled = 1
    line_a.save(update_fields=["quantity_fulfilled"])
    line_b.quantity_fulfilled = 3
    line_b.save(update_fields=["quantity_fulfilled"])

    # when - complete receipt for shipment 2
    receipt2 = Receipt.objects.create(
        shipment=ship2, status=ReceiptStatus.IN_PROGRESS, created_by=staff_user
    )
    ReceiptLine.objects.create(
        receipt=receipt2, purchase_order_item=poi_a2, quantity_received=1
    )
    complete_receipt(receipt2, user=staff_user)

    # then - second fulfillment created for only the remaining quantity
    fulfillments = Fulfillment.objects.filter(order=order).order_by("created_at")
    assert fulfillments.count() == 2

    second_fulfillment = fulfillments.last()
    assert second_fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL

    fl_by_sku = {
        fl.order_line.product_sku: fl.quantity
        for fl in FulfillmentLine.objects.filter(
            fulfillment=second_fulfillment
        ).select_related("order_line")
    }
    # Only variant_a=1 remaining; variant_b already fully fulfilled
    assert fl_by_sku == {"PARTIAL-A": 1}

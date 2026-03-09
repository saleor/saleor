"""Tests for OrderFulfill receipt validation.

These tests ensure that orders cannot be fulfilled when the goods haven't been
physically received yet (PurchaseOrderItems not marked as received).
"""

import graphene
import pytest

from .....inventory import PurchaseOrderItemStatus
from .....inventory.models import PurchaseOrderItem
from .....order import OrderStatus
from .....order.error_codes import OrderErrorCode
from .....order.fetch import OrderLineInfo
from .....plugins.manager import get_plugins_manager
from .....warehouse.management import allocate_stocks
from .....warehouse.models import Allocation, AllocationSource, Stock
from ....tests.utils import get_graphql_content

ORDER_FULFILL_MUTATION = """
    mutation fulfillOrder(
        $order: ID, $input: OrderFulfillInput!
    ) {
        orderFulfill(
            order: $order,
            input: $input
        ) {
            fulfillments {
                id
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_order_fulfill_blocked_when_goods_not_received(
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    owned_warehouse,
    channel_USD,
    purchase_order,
    shipment,
    site_settings,
):
    """Cannot fulfill order when PurchaseOrderItems haven't been received.

    Given:
    - An UNFULFILLED order with allocations in owned warehouse
    - AllocationSources link to PurchaseOrderItems
    - PurchaseOrderItems are CONFIRMED but NOT yet RECEIVED

    When: Attempting to fulfill the order

    Then:
    - Fulfillment should fail with appropriate error
    - Error indicates goods must be received before fulfillment
    """
    from .....inventory.stock_management import confirm_purchase_order_item

    # given

    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    order_line = order.lines.first()
    variant = order_line.variant

    # Clear any existing stock from order_with_lines fixture (in non-owned warehouses)
    Stock.objects.filter(product_variant=variant).exclude(
        warehouse=owned_warehouse
    ).delete()

    # Setup purchase order
    purchase_order.destination_warehouse = owned_warehouse
    purchase_order.save()

    # Create stock at SOURCE warehouse (supplier)
    Stock.objects.create(
        warehouse=purchase_order.source_warehouse,
        product_variant=variant,
        quantity=1000,
    )

    # Create POI in DRAFT status
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=order_line.quantity * 2,
        total_price_amount=1000.00,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    # Confirm POI (moves stock to owned warehouse, creates AllocationSources)
    confirm_purchase_order_item(poi)

    # Allocate stocks (will link to POI via AllocationSources)
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=order_line.quantity)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # Verify allocation has sources linking to POI
    allocation = Allocation.objects.filter(order_line=order_line).first()
    assert allocation is not None
    assert allocation.stock.warehouse.is_owned is True

    allocation_sources = AllocationSource.objects.filter(allocation=allocation)
    assert allocation_sources.exists()
    assert allocation_sources.first().purchase_order_item == poi

    # Verify POI is confirmed but NOT received (no ReceiptLines)
    poi.refresh_from_db()
    assert poi.status == PurchaseOrderItemStatus.CONFIRMED
    assert poi.quantity_received == 0

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", owned_warehouse.id)

    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": False,
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [
                        {"quantity": order_line.quantity, "warehouse": warehouse_id}
                    ],
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        ORDER_FULFILL_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]

    # Should fail with error about unreceived goods
    assert data["errors"]
    error = data["errors"][0]
    assert error["code"] == OrderErrorCode.CANNOT_FULFILL_UNRECEIVED_STOCK.name
    assert (
        "received" in error["message"].lower()
        or "not arrived" in error["message"].lower()
    )

    # Order should still be UNFULFILLED (not fulfilled)
    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED
    assert not data["fulfillments"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_order_fulfill_blocked_when_goods_not_received_auto_approve_off(
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    owned_warehouse,
    channel_USD,
    purchase_order,
    shipment,
    site_settings,
):
    """Cannot fulfill unreceived items even with auto-approve disabled.

    Given:
    - fulfillment_auto_approve is OFF
    - PurchaseOrderItems are CONFIRMED but NOT RECEIVED

    When: Attempting to fulfill the order

    Then: Fulfillment should still fail (receipt check is not gated on auto-approve)
    """
    from .....inventory.stock_management import confirm_purchase_order_item

    # given
    site_settings.fulfillment_auto_approve = False
    site_settings.save(update_fields=["fulfillment_auto_approve"])

    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    order_line = order.lines.first()
    variant = order_line.variant

    Stock.objects.filter(product_variant=variant).exclude(
        warehouse=owned_warehouse
    ).delete()

    purchase_order.destination_warehouse = owned_warehouse
    purchase_order.save()

    Stock.objects.create(
        warehouse=purchase_order.source_warehouse,
        product_variant=variant,
        quantity=1000,
    )

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=order_line.quantity * 2,
        total_price_amount=1000.00,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    confirm_purchase_order_item(poi)

    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=order_line.quantity)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", owned_warehouse.id)

    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": False,
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [
                        {"quantity": order_line.quantity, "warehouse": warehouse_id}
                    ],
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        ORDER_FULFILL_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]

    assert data["errors"]
    error = data["errors"][0]
    assert error["code"] == OrderErrorCode.CANNOT_FULFILL_UNRECEIVED_STOCK.name

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED
    assert not data["fulfillments"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_order_fulfill_succeeds_when_goods_received(
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    owned_warehouse,
    channel_USD,
    purchase_order,
    shipment,
    site_settings,
):
    """Can fulfill order when PurchaseOrderItems have been received.

    Given:
    - An UNFULFILLED order with allocations in owned warehouse
    - AllocationSources link to PurchaseOrderItems
    - PurchaseOrderItems are RECEIVED (quantity_received > 0)
    - Fulfillment auto-approve is enabled

    When: Attempting to fulfill the order

    Then:
    - Fulfillment should succeed
    - Order transitions to appropriate status
    """
    from .....inventory.models import Receipt, ReceiptLine, ReceiptStatus
    from .....inventory.stock_management import confirm_purchase_order_item

    # given
    # Enable auto-approve
    site_settings.fulfillment_auto_approve = True
    site_settings.save(update_fields=["fulfillment_auto_approve"])

    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    order_line = order.lines.first()
    variant = order_line.variant

    # Clear any existing stock from order_with_lines fixture (in non-owned warehouses)
    Stock.objects.filter(product_variant=variant).exclude(
        warehouse=owned_warehouse
    ).delete()

    # Setup purchase order
    purchase_order.destination_warehouse = owned_warehouse
    purchase_order.save()

    # Create stock at SOURCE warehouse (supplier)
    Stock.objects.create(
        warehouse=purchase_order.source_warehouse,
        product_variant=variant,
        quantity=1000,
    )

    # Create POI in DRAFT status
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=order_line.quantity * 2,
        total_price_amount=1000.00,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    # Confirm POI (moves stock to owned warehouse)
    confirm_purchase_order_item(poi)

    # Create Receipt and ReceiptLine to mark goods as physically received
    receipt = Receipt.objects.create(
        shipment=shipment,
        status=ReceiptStatus.COMPLETED,
    )
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi,
        quantity_received=order_line.quantity * 2,  # All received
        received_by=staff_api_client.user,
    )

    # Allocate stocks (will link to POI via AllocationSources)
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=order_line.quantity)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # Verify allocation has sources linking to received POI
    allocation = Allocation.objects.filter(order_line=order_line).first()
    allocation_sources = AllocationSource.objects.filter(allocation=allocation)
    assert allocation_sources.first().purchase_order_item == poi

    # Verify POI IS received
    poi.refresh_from_db()
    assert poi.quantity_received > 0

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", owned_warehouse.id)

    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": False,
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [
                        {"quantity": order_line.quantity, "warehouse": warehouse_id}
                    ],
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        ORDER_FULFILL_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]

    # Should succeed
    assert not data["errors"]
    assert data["fulfillments"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_order_fulfill_blocked_when_partial_receipt(
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    owned_warehouse,
    channel_USD,
    purchase_order,
    shipment,
    site_settings,
):
    """Cannot fulfill order when only PART of the goods have been received.

    Given:
    - An UNFULFILLED order requesting 10 units
    - PurchaseOrderItem has only 5 units received (partial receipt)
    - Attempting to fulfill all 10 units
    - Fulfillment auto-approve is enabled

    When: Attempting to fulfill the full order

    Then:
    - Fulfillment should fail
    - Error indicates insufficient received stock
    """
    from .....inventory.models import Receipt, ReceiptLine, ReceiptStatus
    from .....inventory.stock_management import confirm_purchase_order_item

    # given
    # Enable auto-approve so receipt validation is enforced
    site_settings.fulfillment_auto_approve = True
    site_settings.save(update_fields=["fulfillment_auto_approve"])

    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    order_line = order.lines.first()
    order_line.quantity = 10  # Order 10 units
    order_line.save(update_fields=["quantity"])
    variant = order_line.variant

    # Clear any existing stock from order_with_lines fixture (in non-owned warehouses)
    Stock.objects.filter(product_variant=variant).exclude(
        warehouse=owned_warehouse
    ).delete()

    # Setup purchase order
    purchase_order.destination_warehouse = owned_warehouse
    purchase_order.save()

    # Create stock at SOURCE warehouse (supplier)
    Stock.objects.create(
        warehouse=purchase_order.source_warehouse,
        product_variant=variant,
        quantity=1000,
    )

    # Create POI in DRAFT status
    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=variant,
        quantity_ordered=10,
        total_price_amount=1000.00,
        currency="USD",
        shipment=shipment,
        country_of_origin="US",
        status=PurchaseOrderItemStatus.DRAFT,
    )

    # Confirm POI (moves stock to owned warehouse)
    confirm_purchase_order_item(poi)

    # Create Receipt and ReceiptLine to record partial receipt (5 out of 10)
    receipt = Receipt.objects.create(
        shipment=shipment,
        status=ReceiptStatus.IN_PROGRESS,
    )
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi,
        quantity_received=5,  # Only 5 out of 10 received!
        received_by=staff_api_client.user,
    )

    # Allocate stocks for all 10 units
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=10)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", owned_warehouse.id)

    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": False,
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [
                        {"quantity": 10, "warehouse": warehouse_id}
                    ],  # Try to fulfill all 10
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        ORDER_FULFILL_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]

    # Should fail - not enough received
    assert data["errors"]
    error = data["errors"][0]
    assert error["code"] == OrderErrorCode.CANNOT_FULFILL_UNRECEIVED_STOCK.name
    assert not data["fulfillments"]

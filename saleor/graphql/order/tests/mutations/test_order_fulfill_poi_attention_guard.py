"""Tests for OrderFulfill blocking when a linked POI requires attention."""

import graphene
import pytest

from .....inventory import PurchaseOrderItemStatus
from .....inventory.models import PurchaseOrderItem
from .....order import OrderStatus
from .....order.error_codes import OrderErrorCode
from .....order.fetch import OrderLineInfo
from .....plugins.manager import get_plugins_manager
from .....warehouse.management import allocate_stocks
from .....warehouse.models import Stock
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


def _setup_poi_with_allocation(
    purchase_order,
    shipment,
    owned_warehouse,
    variant,
    order_line,
    channel_USD,
    poi_status,
):
    from .....inventory.stock_management import confirm_purchase_order_item

    purchase_order.destination_warehouse = owned_warehouse
    purchase_order.save()

    Stock.objects.filter(product_variant=variant).exclude(
        warehouse=owned_warehouse
    ).delete()

    Stock.objects.get_or_create(
        warehouse=purchase_order.source_warehouse,
        product_variant=variant,
        defaults={"quantity": 1000},
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

    # Allocate while POI is CONFIRMED (active status), so AllocationSources are created
    allocate_stocks(
        [OrderLineInfo(line=order_line, variant=variant, quantity=order_line.quantity)],
        "US",
        channel_USD,
        manager=get_plugins_manager(allow_replica=False),
    )

    # Now flip the POI to the desired status (e.g. REQUIRES_ATTENTION)
    poi.status = poi_status
    poi.save(update_fields=["status"])

    return poi


@pytest.mark.django_db
def test_order_fulfill_blocked_when_poi_requires_attention(
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    owned_warehouse,
    channel_USD,
    purchase_order,
    shipment,
    site_settings,
):
    """Cannot fulfill when a linked POI has REQUIRES_ATTENTION status.

    Given:
    - An UNFULFILLED order with an AllocationSource linking to a POI
    - The POI has REQUIRES_ATTENTION status

    When: Attempting to fulfill the order

    Then:
    - Fulfillment fails with CANNOT_FULFILL_POI_REQUIRES_ATTENTION error
    - Order remains UNFULFILLED
    """
    # given
    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    order_line = order.lines.first()
    variant = order_line.variant

    _setup_poi_with_allocation(
        purchase_order,
        shipment,
        owned_warehouse,
        variant,
        order_line,
        channel_USD,
        poi_status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
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
    response = staff_api_client.post_graphql(ORDER_FULFILL_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]

    assert data["errors"]
    error = data["errors"][0]
    assert error["code"] == OrderErrorCode.CANNOT_FULFILL_POI_REQUIRES_ATTENTION.name
    assert not data["fulfillments"]

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED


@pytest.mark.django_db
def test_order_fulfill_allowed_when_no_poi_requires_attention(
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    owned_warehouse,
    channel_USD,
    purchase_order,
    shipment,
    site_settings,
):
    """Can fulfill when linked POI has RECEIVED status (not requiring attention).

    Given:
    - An UNFULFILLED order with an AllocationSource linking to a POI
    - The POI has RECEIVED status

    When: Attempting to fulfill the order

    Then:
    - Fulfillment succeeds (no REQUIRES_ATTENTION block)
    """
    from .....inventory.models import Receipt, ReceiptLine, ReceiptStatus

    # given
    site_settings.fulfillment_auto_approve = False
    site_settings.save(update_fields=["fulfillment_auto_approve"])

    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    order_line = order.lines.first()
    variant = order_line.variant

    poi = _setup_poi_with_allocation(
        purchase_order,
        shipment,
        owned_warehouse,
        variant,
        order_line,
        channel_USD,
        poi_status=PurchaseOrderItemStatus.RECEIVED,
    )

    receipt = Receipt.objects.create(
        shipment=shipment,
        status=ReceiptStatus.COMPLETED,
    )
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=poi,
        quantity_received=order_line.quantity * 2,
        received_by=staff_api_client.user,
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
    response = staff_api_client.post_graphql(ORDER_FULFILL_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]

    assert not data["errors"]
    assert data["fulfillments"]


@pytest.mark.django_db
def test_order_fulfill_blocked_regardless_of_auto_approve(
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    owned_warehouse,
    channel_USD,
    purchase_order,
    shipment,
    site_settings,
):
    """POI REQUIRES_ATTENTION check fires even when auto-approve is disabled.

    Given:
    - Fulfillment auto-approve is disabled
    - A POI linked to the order line has REQUIRES_ATTENTION status

    When: Attempting to fulfill the order

    Then:
    - Fulfillment still fails with CANNOT_FULFILL_POI_REQUIRES_ATTENTION
    """
    # given
    site_settings.fulfillment_auto_approve = False
    site_settings.save(update_fields=["fulfillment_auto_approve"])

    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    order_line = order.lines.first()
    variant = order_line.variant

    _setup_poi_with_allocation(
        purchase_order,
        shipment,
        owned_warehouse,
        variant,
        order_line,
        channel_USD,
        poi_status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
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
    response = staff_api_client.post_graphql(ORDER_FULFILL_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]

    assert data["errors"]
    error = data["errors"][0]
    assert error["code"] == OrderErrorCode.CANNOT_FULFILL_POI_REQUIRES_ATTENTION.name
    assert not data["fulfillments"]

import pytest

from ...order import OrderStatus
from ...order.models import Fulfillment
from ...warehouse.models import Allocation
from ..models import PurchaseOrderRequestedAllocation
from ..stock_management import confirm_purchase_order_item


@pytest.fixture
def unconfirmed_order_with_allocations(
    order, warehouse, warehouse_for_cc, product_variant_list
):
    """Order in UNCONFIRMED status with allocations in non-owned warehouse."""
    order.status = OrderStatus.UNCONFIRMED
    order.save()

    # Non-owned source warehouse
    warehouse_for_cc.is_owned = False
    warehouse_for_cc.save()

    # Owned destination warehouse
    warehouse.is_owned = True
    warehouse.save()

    # Create order lines
    variant = product_variant_list[0]
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

    # Create stock in both warehouses
    source_stock, _ = variant.stocks.get_or_create(
        warehouse=warehouse_for_cc,
        defaults={"quantity": 10, "quantity_allocated": 0},
    )
    dest_stock, _ = variant.stocks.get_or_create(
        warehouse=warehouse,
        defaults={"quantity": 0, "quantity_allocated": 0},
    )

    # Create allocation in non-owned warehouse (UNCONFIRMED orders allocate here)
    Allocation.objects.create(
        order_line=line,
        stock=source_stock,
        quantity_allocated=5,
    )

    # Update stock to reflect allocation
    source_stock.quantity_allocated = 5
    source_stock.save()

    return order


def test_confirm_poi_does_not_create_fulfillments(
    unconfirmed_order_with_allocations,
    purchase_order,
    warehouse,
    warehouse_for_cc,
    staff_user,
):
    # given
    order = unconfirmed_order_with_allocations
    line = order.lines.first()

    from ..models import PurchaseOrderItem

    poi = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=line.variant,
        quantity_ordered=5,
        total_price_amount=50.0,
        currency="USD",
        country_of_origin="US",
    )

    purchase_order.source_warehouse = warehouse_for_cc
    purchase_order.destination_warehouse = warehouse
    purchase_order.save()

    allocation = Allocation.objects.get(order_line=line)
    PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=purchase_order, allocation=allocation
    )

    assert order.status == OrderStatus.UNCONFIRMED
    assert Fulfillment.objects.filter(order=order).count() == 0

    # when
    confirm_purchase_order_item(poi, user=staff_user)

    # then
    order.refresh_from_db()

    # Order should be auto-confirmed
    assert order.status == OrderStatus.UNFULFILLED

    # No fulfillments should be created at confirm time - only after receipt
    assert Fulfillment.objects.filter(order=order).count() == 0


def test_confirm_poi_auto_confirms_order_without_creating_fulfillments(
    order, warehouse, warehouse_JPY, warehouse_for_cc, product_variant_list, staff_user
):
    # given
    order.status = OrderStatus.UNCONFIRMED
    order.save()

    warehouse_for_cc.is_owned = False
    warehouse_for_cc.save()
    warehouse.is_owned = True
    warehouse.save()
    warehouse_JPY.is_owned = True
    warehouse_JPY.channels.add(order.channel)
    warehouse_JPY.save()

    from ...inventory.models import PurchaseOrder

    po1 = PurchaseOrder.objects.create(
        source_warehouse=warehouse_for_cc,
        destination_warehouse=warehouse,
    )
    po2 = PurchaseOrder.objects.create(
        source_warehouse=warehouse_for_cc,
        destination_warehouse=warehouse_JPY,
    )

    # Create two order lines
    variant1 = product_variant_list[0]
    variant2 = product_variant_list[1]

    line1 = order.lines.create(
        product_name=variant1.product.name,
        variant_name=variant1.name,
        product_sku=variant1.sku,
        is_shipping_required=True,
        is_gift_card=False,
        quantity=3,
        variant=variant1,
        unit_price_net_amount=10,
        unit_price_gross_amount=10,
        total_price_net_amount=30,
        total_price_gross_amount=30,
        undiscounted_unit_price_net_amount=10,
        undiscounted_unit_price_gross_amount=10,
        undiscounted_total_price_net_amount=30,
        undiscounted_total_price_gross_amount=30,
        currency="USD",
        tax_rate=0,
    )

    line2 = order.lines.create(
        product_name=variant2.product.name,
        variant_name=variant2.name,
        product_sku=variant2.sku,
        is_shipping_required=True,
        is_gift_card=False,
        quantity=2,
        variant=variant2,
        unit_price_net_amount=20,
        unit_price_gross_amount=20,
        total_price_net_amount=40,
        total_price_gross_amount=40,
        undiscounted_unit_price_net_amount=20,
        undiscounted_unit_price_gross_amount=20,
        undiscounted_total_price_net_amount=40,
        undiscounted_total_price_gross_amount=40,
        currency="USD",
        tax_rate=0,
    )

    # Create stocks and allocations
    source_stock1, _ = variant1.stocks.get_or_create(
        warehouse=warehouse_for_cc,
        defaults={"quantity": 10, "quantity_allocated": 0},
    )
    dest_stock1, _ = variant1.stocks.get_or_create(
        warehouse=warehouse,
        defaults={"quantity": 0, "quantity_allocated": 0},
    )

    source_stock2, _ = variant2.stocks.get_or_create(
        warehouse=warehouse_for_cc,
        defaults={"quantity": 10, "quantity_allocated": 0},
    )
    dest_stock2, _ = variant2.stocks.get_or_create(
        warehouse=warehouse_JPY,
        defaults={"quantity": 0, "quantity_allocated": 0},
    )

    alloc1 = Allocation.objects.create(
        order_line=line1, stock=source_stock1, quantity_allocated=3
    )
    alloc2 = Allocation.objects.create(
        order_line=line2, stock=source_stock2, quantity_allocated=2
    )

    source_stock1.quantity_allocated = 3
    source_stock1.save()
    source_stock2.quantity_allocated = 2
    source_stock2.save()

    # Create POIs
    from ..models import PurchaseOrderItem

    poi1 = PurchaseOrderItem.objects.create(
        order=po1,
        product_variant=variant1,
        quantity_ordered=3,
        total_price_amount=30.0,
        currency="USD",
        country_of_origin="US",
    )
    PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=po1, allocation=alloc1
    )

    poi2 = PurchaseOrderItem.objects.create(
        order=po2,
        product_variant=variant2,
        quantity_ordered=2,
        total_price_amount=40.0,
        currency="USD",
        country_of_origin="US",
    )
    PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=po2, allocation=alloc2
    )

    # when - confirm both POIs
    confirm_purchase_order_item(poi1, user=staff_user)
    confirm_purchase_order_item(poi2, user=staff_user)

    # then
    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED

    # No fulfillments at confirm time - fulfillments are created after receipt
    assert Fulfillment.objects.filter(order=order).count() == 0


def test_confirm_poi_does_not_create_fulfillments_if_not_all_inventory_ready(
    unconfirmed_order_with_allocations,
    purchase_order,
    warehouse,
    warehouse_for_cc,
    product_variant_list,
    staff_user,
):
    # given
    order = unconfirmed_order_with_allocations

    # Add another line that doesn't have a POI yet
    variant2 = product_variant_list[1]
    line2 = order.lines.create(
        product_name=variant2.product.name,
        variant_name=variant2.name,
        product_sku=variant2.sku,
        is_shipping_required=True,
        is_gift_card=False,
        quantity=2,
        variant=variant2,
        unit_price_net_amount=20,
        unit_price_gross_amount=20,
        total_price_net_amount=40,
        total_price_gross_amount=40,
        undiscounted_unit_price_net_amount=20,
        undiscounted_unit_price_gross_amount=20,
        undiscounted_total_price_net_amount=40,
        undiscounted_total_price_gross_amount=40,
        currency="USD",
        tax_rate=0,
    )

    source_stock2, _ = variant2.stocks.get_or_create(
        warehouse=warehouse_for_cc,
        defaults={"quantity": 10, "quantity_allocated": 0},
    )

    Allocation.objects.create(
        order_line=line2, stock=source_stock2, quantity_allocated=2
    )
    source_stock2.quantity_allocated = 2
    source_stock2.save()

    # Only create POI for first line
    line1 = order.lines.first()
    from ..models import PurchaseOrderItem

    poi1 = PurchaseOrderItem.objects.create(
        order=purchase_order,
        product_variant=line1.variant,
        quantity_ordered=5,
        total_price_amount=50.0,
        currency="USD",
        country_of_origin="US",
    )

    purchase_order.source_warehouse = warehouse_for_cc
    purchase_order.destination_warehouse = warehouse
    purchase_order.save()

    line1_alloc = Allocation.objects.get(order_line=line1)
    PurchaseOrderRequestedAllocation.objects.create(
        purchase_order=purchase_order, allocation=line1_alloc
    )

    # when
    confirm_purchase_order_item(poi1, user=staff_user)

    # then
    order.refresh_from_db()

    # Order should still be UNCONFIRMED (not all allocations have sources)
    assert order.status == OrderStatus.UNCONFIRMED

    # No fulfillments should be created
    assert Fulfillment.objects.filter(order=order).count() == 0

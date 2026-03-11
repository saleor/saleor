from decimal import Decimal

import pytest

from ...invoice import InvoiceType
from ...payment import ChargeStatus, CustomPaymentChoices
from ...payment.models import Payment
from ..models import Fulfillment, FulfillmentLine


@pytest.fixture
def order_with_three_lines(order_with_lines, product_list):
    order = order_with_lines

    existing_lines = list(order.lines.all())
    if len(existing_lines) < 3:
        for i in range(3 - len(existing_lines)):
            product = product_list[i % len(product_list)]
            variant = product.variants.first()
            order.lines.create(
                product_name=product.name,
                variant_name=variant.name,
                product_sku=variant.sku,
                is_shipping_required=True,
                is_gift_card=False,
                quantity=5 * (i + 1),
                variant=variant,
                unit_price_net_amount=Decimal("20.00") * (i + 1),
                unit_price_gross_amount=Decimal("20.00") * (i + 1),
                total_price_net_amount=Decimal("100.00") * (i + 1),
                total_price_gross_amount=Decimal("100.00") * (i + 1),
                undiscounted_unit_price_net_amount=Decimal("20.00") * (i + 1),
                undiscounted_unit_price_gross_amount=Decimal("20.00") * (i + 1),
                undiscounted_total_price_net_amount=Decimal("100.00") * (i + 1),
                undiscounted_total_price_gross_amount=Decimal("100.00") * (i + 1),
                currency="USD",
                tax_rate=Decimal(0),
            )

    lines = list(order.lines.all()[:3])

    line1 = lines[0]
    line1.quantity = 10
    line1.unit_price_gross_amount = Decimal("10.00")
    line1.total_price_gross_amount = Decimal("100.00")
    line1.save()

    line2 = lines[1]
    line2.quantity = 5
    line2.unit_price_gross_amount = Decimal("20.00")
    line2.total_price_gross_amount = Decimal("100.00")
    line2.save()

    line3 = lines[2]
    line3.quantity = 8
    line3.unit_price_gross_amount = Decimal("15.00")
    line3.total_price_gross_amount = Decimal("120.00")
    line3.save()

    order.total_gross_amount = Decimal("320.00")
    order.save()

    return order


def _allocate_and_generate(order, fulfillment, manager):
    from saleor.order.proforma import (
        allocate_costs_to_fulfillments,
        generate_proforma_invoice,
    )

    allocate_costs_to_fulfillments(order, [fulfillment])
    fulfillment.save(
        update_fields=["deposit_allocated_amount", "shipping_allocated_net_amount"]
    )
    return generate_proforma_invoice(fulfillment, manager)


@pytest.mark.django_db
def test_multiple_partial_fulfillments_with_deposit_allocation(
    order_with_three_lines, warehouse, address
):
    from unittest.mock import Mock

    from saleor.inventory import PurchaseOrderItemStatus
    from saleor.inventory.models import (
        PurchaseOrder,
        PurchaseOrderItem,
        Receipt,
        ReceiptLine,
    )
    from saleor.shipping import ShipmentType
    from saleor.shipping.models import Shipment
    from saleor.warehouse.models import Allocation, AllocationSource, Warehouse

    order = order_with_three_lines
    lines = list(order.lines.all()[:3])

    order.deposit_required = True
    order.deposit_percentage = Decimal("30.00")
    order.status = "unfulfilled"
    order.save()

    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="XERO-DEPOSIT-WORKFLOW-001",
        total=Decimal("96.00"),
        captured_amount=Decimal("96.00"),
        charge_status=ChargeStatus.FULLY_CHARGED,
        currency=order.currency,
        is_active=True,
    )

    assert order.total_deposit_paid == Decimal("96.00")
    assert order.deposit_threshold_met is True

    supplier_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="Supplier Warehouse Workflow",
        slug="supplier-warehouse-workflow",
        email="supplier-workflow@example.com",
        is_owned=False,
    )

    po = PurchaseOrder.objects.create(
        source_warehouse=supplier_warehouse,
        destination_warehouse=warehouse,
    )

    pois = []
    for line in lines:
        poi = PurchaseOrderItem.objects.create(
            order=po,
            product_variant=line.variant,
            quantity_ordered=line.quantity,
            total_price_amount=line.total_price_gross_amount,
            currency="USD",
            country_of_origin="US",
            status=PurchaseOrderItemStatus.DRAFT,
        )

        shipment = Shipment.objects.create(
            source=supplier_warehouse.address,
            destination=warehouse.address,
            shipment_type=ShipmentType.INBOUND,
            arrived_at="2024-01-01T00:00:00Z",
            shipping_cost_amount=Decimal("50.00"),
            currency="USD",
        )
        poi.shipment = shipment
        poi.save()

        receipt = Receipt.objects.create(shipment=shipment)
        ReceiptLine.objects.create(
            receipt=receipt, purchase_order_item=poi, quantity_received=line.quantity
        )

        stock = warehouse.stock_set.filter(product_variant=line.variant).first()
        allocation = Allocation.objects.create(
            order_line=line, stock=stock, quantity_allocated=line.quantity
        )
        AllocationSource.objects.create(
            allocation=allocation, purchase_order_item=poi, quantity=line.quantity
        )

        pois.append(poi)

    manager = Mock()
    manager.fulfillment_proforma_invoice_generated.return_value = None

    fulfillment1 = Fulfillment.objects.create(
        order=order, status="waiting_for_approval"
    )
    FulfillmentLine.objects.create(
        order_line=lines[0], fulfillment=fulfillment1, quantity=10
    )

    invoice1 = _allocate_and_generate(order, fulfillment1, manager)

    assert invoice1.type == InvoiceType.PROFORMA
    assert invoice1.order == order
    assert invoice1.fulfillment == fulfillment1

    fulfillment1.refresh_from_db()
    # First fulfillment (only one in batch) gets full remaining deposit
    assert fulfillment1.deposit_allocated_amount == Decimal("96.00")

    fulfillment2 = Fulfillment.objects.create(
        order=order, status="waiting_for_approval"
    )
    FulfillmentLine.objects.create(
        order_line=lines[1], fulfillment=fulfillment2, quantity=5
    )

    invoice2 = _allocate_and_generate(order, fulfillment2, manager)

    assert invoice2.type == InvoiceType.PROFORMA
    assert invoice2.order == order
    assert invoice2.fulfillment == fulfillment2

    fulfillment2.refresh_from_db()
    # All deposit already allocated to F1, F2 gets 0
    assert fulfillment2.deposit_allocated_amount == Decimal("0.00")

    fulfillment3 = Fulfillment.objects.create(
        order=order, status="waiting_for_approval"
    )
    FulfillmentLine.objects.create(
        order_line=lines[2], fulfillment=fulfillment3, quantity=8
    )

    invoice3 = _allocate_and_generate(order, fulfillment3, manager)

    assert invoice3.type == InvoiceType.PROFORMA
    assert invoice3.order == order
    assert invoice3.fulfillment == fulfillment3

    fulfillment3.refresh_from_db()
    assert fulfillment3.deposit_allocated_amount == Decimal("0.00")

    total_allocated = (
        fulfillment1.deposit_allocated_amount
        + fulfillment2.deposit_allocated_amount
        + fulfillment3.deposit_allocated_amount
    )
    assert total_allocated == Decimal("96.00")
    assert total_allocated == order.total_deposit_paid

    order.refresh_from_db()
    assert order.get_remaining_deposit() == Decimal("0.00")


@pytest.mark.django_db
def test_deposit_allocation_exhausted_before_final_fulfillment(
    order_with_three_lines, warehouse, address
):
    from unittest.mock import Mock

    from saleor.inventory import PurchaseOrderItemStatus
    from saleor.inventory.models import (
        PurchaseOrder,
        PurchaseOrderItem,
        Receipt,
        ReceiptLine,
    )
    from saleor.shipping import ShipmentType
    from saleor.shipping.models import Shipment
    from saleor.warehouse.models import Allocation, AllocationSource, Warehouse

    order = order_with_three_lines
    lines = list(order.lines.all()[:3])

    order.deposit_required = True
    order.deposit_percentage = Decimal("20.00")
    order.status = "unfulfilled"
    order.save()

    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="XERO-DEPOSIT-WORKFLOW-002",
        total=Decimal("64.00"),
        captured_amount=Decimal("64.00"),
        charge_status=ChargeStatus.FULLY_CHARGED,
        currency=order.currency,
        is_active=True,
    )

    assert order.total_deposit_paid == Decimal("64.00")

    supplier_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="Supplier Warehouse Exhaust",
        slug="supplier-warehouse-exhaust",
        email="supplier-exhaust@example.com",
        is_owned=False,
    )

    po = PurchaseOrder.objects.create(
        source_warehouse=supplier_warehouse,
        destination_warehouse=warehouse,
    )

    for line in lines:
        poi = PurchaseOrderItem.objects.create(
            order=po,
            product_variant=line.variant,
            quantity_ordered=line.quantity,
            total_price_amount=line.total_price_gross_amount,
            currency="USD",
            country_of_origin="US",
            status=PurchaseOrderItemStatus.DRAFT,
        )

        shipment = Shipment.objects.create(
            source=supplier_warehouse.address,
            destination=warehouse.address,
            shipment_type=ShipmentType.INBOUND,
            arrived_at="2024-01-01T00:00:00Z",
            shipping_cost_amount=Decimal("50.00"),
            currency="USD",
        )
        poi.shipment = shipment
        poi.save()

        receipt = Receipt.objects.create(shipment=shipment)
        ReceiptLine.objects.create(
            receipt=receipt, purchase_order_item=poi, quantity_received=line.quantity
        )

        stock = warehouse.stock_set.filter(product_variant=line.variant).first()
        allocation = Allocation.objects.create(
            order_line=line, stock=stock, quantity_allocated=line.quantity
        )
        AllocationSource.objects.create(
            allocation=allocation, purchase_order_item=poi, quantity=line.quantity
        )

    manager = Mock()
    manager.fulfillment_proforma_invoice_generated.return_value = None

    fulfillment1 = Fulfillment.objects.create(
        order=order, status="waiting_for_approval"
    )
    FulfillmentLine.objects.create(
        order_line=lines[0], fulfillment=fulfillment1, quantity=10
    )
    _allocate_and_generate(order, fulfillment1, manager)

    fulfillment2 = Fulfillment.objects.create(
        order=order, status="waiting_for_approval"
    )
    FulfillmentLine.objects.create(
        order_line=lines[1], fulfillment=fulfillment2, quantity=5
    )
    _allocate_and_generate(order, fulfillment2, manager)

    fulfillment1.refresh_from_db()
    fulfillment2.refresh_from_db()

    # F1 gets all deposit (only one in its batch), F2 gets 0
    assert fulfillment1.deposit_allocated_amount == Decimal("64.00")
    assert fulfillment2.deposit_allocated_amount == Decimal("0.00")

    fulfillment3 = Fulfillment.objects.create(
        order=order, status="waiting_for_approval"
    )
    FulfillmentLine.objects.create(
        order_line=lines[2], fulfillment=fulfillment3, quantity=8
    )
    _allocate_and_generate(order, fulfillment3, manager)

    fulfillment3.refresh_from_db()

    assert fulfillment3.deposit_allocated_amount == Decimal("0.00")

    total_allocated = (
        fulfillment1.deposit_allocated_amount
        + fulfillment2.deposit_allocated_amount
        + fulfillment3.deposit_allocated_amount
    )
    assert total_allocated == Decimal("64.00")
    assert total_allocated <= order.total_deposit_paid

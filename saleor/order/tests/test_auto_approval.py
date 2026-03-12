import pytest
from django.utils import timezone

from ...payment import ChargeStatus, CustomPaymentChoices
from ...payment.models import Payment
from ...shipping.models import Shipment
from .. import FulfillmentStatus, OrderOrigin, PickStatus
from ..actions import (
    assign_shipment_to_fulfillment,
    auto_create_pick_for_fulfillment,
    complete_pick,
    start_pick,
    update_pick_item,
)


def _create_xero_payment(
    order, psp_reference, fulfillment=None, charge_status=ChargeStatus.FULLY_CHARGED
):
    return Payment.objects.create(
        order=order,
        fulfillment=fulfillment,
        gateway=CustomPaymentChoices.XERO,
        psp_reference=psp_reference,
        total=0,
        captured_amount=0,
        charge_status=charge_status,
        currency=order.currency,
        is_active=True,
    )


@pytest.fixture
def shipment_for_fulfillment(warehouse):
    from ...shipping import ShipmentType

    return Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        tracking_url="AUTO-APPROVE-TEST",
        shipping_cost_amount=0,
        currency="USD",
        inco_term="DDP",
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
        shipment_type=ShipmentType.OUTBOUND,
    )


def test_auto_approve_when_pick_completed_last(
    full_fulfillment_awaiting_approval,
    shipment_for_fulfillment,
    staff_user,
):
    fulfillment = full_fulfillment_awaiting_approval

    fulfillment.shipment = shipment_for_fulfillment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )

    assert fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL

    complete_pick(pick, user=staff_user, auto_approve=True)

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED


def test_auto_approve_when_shipment_assigned_last(
    full_fulfillment_awaiting_approval,
    shipment_for_fulfillment,
    staff_user,
):
    fulfillment = full_fulfillment_awaiting_approval

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user)

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL

    assign_shipment_to_fulfillment(
        fulfillment, shipment_for_fulfillment, staff_user, auto_approve=True
    )

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED


def test_no_auto_approve_when_pick_not_completed(
    full_fulfillment_awaiting_approval,
    shipment_for_fulfillment,
    staff_user,
):
    fulfillment = full_fulfillment_awaiting_approval

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)

    assign_shipment_to_fulfillment(
        fulfillment, shipment_for_fulfillment, staff_user, auto_approve=True
    )

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL
    assert pick.status == PickStatus.IN_PROGRESS


def test_no_auto_approve_when_no_shipment(
    full_fulfillment_awaiting_approval,
    staff_user,
):
    fulfillment = full_fulfillment_awaiting_approval

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user, auto_approve=True)

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL
    assert fulfillment.shipment is None


def test_no_auto_approve_when_pick_does_not_exist(
    full_fulfillment_awaiting_approval,
    shipment_for_fulfillment,
    staff_user,
):
    fulfillment = full_fulfillment_awaiting_approval

    assign_shipment_to_fulfillment(
        fulfillment, shipment_for_fulfillment, staff_user, auto_approve=True
    )

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL


def test_no_auto_approve_when_already_fulfilled(
    full_fulfillment_awaiting_approval,
    shipment_for_fulfillment,
    staff_user,
):
    fulfillment = full_fulfillment_awaiting_approval
    fulfillment.status = FulfillmentStatus.FULFILLED
    fulfillment.save(update_fields=["status"])

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user, auto_approve=True)

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED


def test_no_auto_approve_when_proforma_not_paid(
    full_fulfillment_awaiting_approval,
    shipment_for_fulfillment,
    staff_user,
):
    fulfillment = full_fulfillment_awaiting_approval
    order = fulfillment.order

    order.origin = OrderOrigin.DRAFT
    order.save(update_fields=["origin"])

    fulfillment.shipment = shipment_for_fulfillment
    fulfillment.save(update_fields=["shipment"])

    _create_xero_payment(
        order,
        psp_reference="PREPAY-001",
        fulfillment=fulfillment,
        charge_status=ChargeStatus.NOT_CHARGED,
    )

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user, auto_approve=True)

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL


def test_no_auto_approve_when_no_prepayment(
    full_fulfillment_awaiting_approval,
    shipment_for_fulfillment,
    staff_user,
):
    fulfillment = full_fulfillment_awaiting_approval
    order = fulfillment.order

    order.origin = OrderOrigin.DRAFT
    order.save(update_fields=["origin"])

    fulfillment.shipment = shipment_for_fulfillment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user, auto_approve=True)

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL


def test_auto_approve_when_proforma_paid(
    full_fulfillment_awaiting_approval,
    shipment_for_fulfillment,
    staff_user,
):
    from saleor.invoice import InvoiceType
    from saleor.invoice.models import Invoice

    fulfillment = full_fulfillment_awaiting_approval
    order = fulfillment.order

    order.origin = OrderOrigin.DRAFT
    order.save(update_fields=["origin"])

    fulfillment.shipment = shipment_for_fulfillment
    fulfillment.save(update_fields=["shipment"])

    _create_xero_payment(order, psp_reference="PREPAY-001", fulfillment=fulfillment)
    Invoice.objects.create(fulfillment=fulfillment, type=InvoiceType.FINAL)

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user, auto_approve=True)

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED

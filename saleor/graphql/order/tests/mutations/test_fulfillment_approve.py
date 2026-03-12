from unittest.mock import patch

import graphene

from .....giftcard.models import GiftCard
from .....order import (
    FulfillmentStatus,
    OrderEvents,
    OrderOrigin,
    OrderStatus,
    PickStatus,
)
from .....order.actions import (
    auto_create_pick_for_fulfillment,
    complete_pick,
    fulfill_order_lines,
    start_pick,
    update_pick_item,
)
from .....order.error_codes import OrderErrorCode
from .....order.fetch import OrderLineInfo
from .....order.models import OrderLine
from .....plugins.manager import get_plugins_manager
from .....product.models import Product
from ....tests.utils import assert_no_permission, get_graphql_content

APPROVE_FULFILLMENT_MUTATION = """
    mutation approveFulfillment(
        $id: ID!, $notifyCustomer: Boolean!, $allowStockToBeExceeded: Boolean = false
    ) {
        orderFulfillmentApprove(
                id: $id,
                notifyCustomer: $notifyCustomer,
                allowStockToBeExceeded: $allowStockToBeExceeded) {
            fulfillment {
                status
            }
            order {
                status
            }
            errors {
                field
                code
                message
                orderLines
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.xero_fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-APPROVE",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()
    assert data["order"]["status"] == OrderStatus.FULFILLED.upper()
    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED

    assert mock_email_fulfillment.call_count == 1
    events = fulfillment.order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event.type == OrderEvents.FULFILLMENT_FULFILLED_ITEMS
    assert event.user == staff_api_client.user
    mock_fulfillment_approved.assert_called_once_with(fulfillment)


def test_fulfillment_approve_by_user_no_channel_access(
    staff_api_client,
    partial_fulfillment_awaiting_approval,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    fulfillment = partial_fulfillment_awaiting_approval
    order = fulfillment.order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.xero_fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_by_app(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    app_api_client,
    full_fulfillment_awaiting_approval,
    permission_manage_orders,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    # given
    fulfillment = full_fulfillment_awaiting_approval

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-BY-APP",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()
    assert data["order"]["status"] == OrderStatus.FULFILLED.upper()
    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED

    assert mock_email_fulfillment.call_count == 1
    events = fulfillment.order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event.type == OrderEvents.FULFILLMENT_FULFILLED_ITEMS
    assert event.app == app_api_client.app
    assert event.user is None
    mock_fulfillment_approved.assert_called_once_with(fulfillment)


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_delete_products_before_approval_allow_stock_exceeded_true(
    mock_email_fulfillment,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-DELETE-TRUE",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    Product.objects.all().delete()

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {
        "id": fulfillment_id,
        "notifyCustomer": True,
        "allowStockToBeExceeded": True,
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()
    assert data["order"]["status"] == OrderStatus.FULFILLED.upper()
    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED

    assert mock_email_fulfillment.call_count == 1
    events = fulfillment.order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event.type == OrderEvents.FULFILLMENT_FULFILLED_ITEMS
    assert event.user == staff_api_client.user


@patch("saleor.plugins.manager.PluginsManager.xero_fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_delete_products_before_approval_allow_stock_exceeded_false(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    staff_api_client,
    partial_fulfillment_awaiting_approval,
    permission_group_manage_orders,
    django_capture_on_commit_callbacks,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = partial_fulfillment_awaiting_approval

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-DELETE-ERROR",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    Product.objects.all().delete()

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {
        "id": fulfillment_id,
        "notifyCustomer": True,
        "allowStockToBeExceeded": False,
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderFulfillmentApprove"]["errors"]

    assert len(errors) == 2

    error_field_and_code = {
        "field": "stocks",
        "code": "INSUFFICIENT_STOCK",
    }
    expected_errors = [
        {
            **error_field_and_code,
            "orderLines": [graphene.Node.to_global_id("OrderLine", line.order_line_id)],
            "message": "Insufficient product stock.",
        }
        for line in fulfillment.lines.all()
    ]

    for expected_error in expected_errors:
        assert expected_error in errors

    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL

    mock_email_fulfillment.assert_not_called()
    events = fulfillment.order.events.all()
    assert len(events) == 0
    mock_fulfillment_approved.assert_not_called()


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_gift_cards_created(
    mock_email_fulfillment,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
    gift_card_shippable_order_line,
    gift_card_non_shippable_order_line,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    gift_card_line_1 = gift_card_shippable_order_line
    gift_card_line_2 = gift_card_non_shippable_order_line
    stock_1 = gift_card_line_1.variant.stocks.first()
    stock_2 = gift_card_line_2.variant.stocks.first()
    fulfillment_line_1 = fulfillment.lines.create(
        order_line=gift_card_line_1, quantity=gift_card_line_1.quantity, stock=stock_1
    )
    fulfillment_line_2 = fulfillment.lines.create(
        order_line=gift_card_line_2, quantity=gift_card_line_2.quantity, stock=stock_2
    )

    fulfill_order_lines(
        [
            OrderLineInfo(
                line=gift_card_line_1,
                quantity=gift_card_line_1.quantity,
                warehouse_pk=stock_1.warehouse.pk,
            ),
            OrderLineInfo(
                line=gift_card_line_2,
                quantity=gift_card_line_2.quantity,
                warehouse_pk=stock_2.warehouse.pk,
            ),
        ],
        manager=get_plugins_manager(allow_replica=False),
    )

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-GIFTCARDS",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}
    assert GiftCard.objects.count() == 0

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()
    assert data["order"]["status"] == OrderStatus.FULFILLED.upper()
    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED

    assert mock_email_fulfillment.call_count == 1
    events = fulfillment.order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event.type == OrderEvents.FULFILLMENT_FULFILLED_ITEMS
    assert event.user == staff_api_client.user
    gift_cards = GiftCard.objects.all()
    assert gift_cards.count() == gift_card_line_1.quantity + gift_card_line_2.quantity
    for gift_card in gift_cards:
        if gift_card.product == gift_card_line_1.variant.product:
            assert gift_card.fulfillment_line == fulfillment_line_1
        else:
            assert gift_card.fulfillment_line == fulfillment_line_2


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_when_stock_is_exceeded_and_flag_enabled(
    mock_email_fulfillment,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    # make stocks exceeded
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    for stock in [
        line.stock for line in full_fulfillment_awaiting_approval.lines.all()
    ]:
        stock.quantity = -99
        stock.save()

    fulfillment = full_fulfillment_awaiting_approval

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-STOCK-EXCEEDED",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)

    # make response with flag disabled, raised error is expected
    variables = {
        "id": fulfillment_id,
        "notifyCustomer": True,
        "allowStockToBeExceeded": True,
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()
    assert data["order"]["status"] == OrderStatus.FULFILLED.upper()
    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED

    assert mock_email_fulfillment.call_count == 1
    events = fulfillment.order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event.type == OrderEvents.FULFILLMENT_FULFILLED_ITEMS
    assert event.user == staff_api_client.user


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_when_stock_is_exceeded_and_flag_disabled(
    mock_email_fulfillment,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    # make stocks exceeded
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    for stock in [
        line.stock for line in full_fulfillment_awaiting_approval.lines.all()
    ]:
        stock.quantity = -99
        stock.save()

    fulfillment = full_fulfillment_awaiting_approval

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-STOCK-DISABLED",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)

    variables = {
        "id": fulfillment_id,
        "notifyCustomer": True,
        "allowStockToBeExceeded": False,
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["data"]["orderFulfillmentApprove"]["errors"]

    assert len(errors) == 2

    error_field_and_code = {
        "field": "stocks",
        "code": "INSUFFICIENT_STOCK",
    }

    expected_errors = [
        {
            **error_field_and_code,
            "message": "Insufficient product stock.",
            "orderLines": [graphene.Node.to_global_id("OrderLine", line.order_line_id)],
        }
        for line in fulfillment.lines.all()
    ]

    for expected_error in expected_errors:
        assert expected_error in errors


@patch("saleor.plugins.manager.PluginsManager.xero_fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_partial_order_fulfill(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    staff_api_client,
    partial_fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = APPROVE_FULFILLMENT_MUTATION
    order = partial_fulfillment_awaiting_approval.order

    second_fulfillment = order.fulfillments.create()
    line_1 = order.lines.first()
    line_2 = order.lines.last()
    second_fulfillment.lines.create(
        order_line=line_1, quantity=line_1.quantity - line_1.quantity_fulfilled
    )
    second_fulfillment.lines.create(
        order_line=line_2, quantity=line_2.quantity - line_2.quantity_fulfilled
    )
    second_fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    second_fulfillment.save()

    line_1.quantity_fulfilled = line_1.quantity
    line_2.quantity_fulfilled = line_2.quantity

    OrderLine.objects.bulk_update([line_1, line_2], ["quantity_fulfilled"])

    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    warehouse = partial_fulfillment_awaiting_approval.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-PARTIAL",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    partial_fulfillment_awaiting_approval.shipment = shipment
    partial_fulfillment_awaiting_approval.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(partial_fulfillment_awaiting_approval)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    fulfillment_id = graphene.Node.to_global_id(
        "Fulfillment", partial_fulfillment_awaiting_approval.id
    )
    variables = {"id": fulfillment_id, "notifyCustomer": False}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()
    assert data["order"]["status"] == "PARTIALLY_FULFILLED"
    partial_fulfillment_awaiting_approval.refresh_from_db()
    assert partial_fulfillment_awaiting_approval.status == FulfillmentStatus.FULFILLED

    assert mock_email_fulfillment.call_count == 0
    mock_fulfillment_approved.assert_called_once_with(
        partial_fulfillment_awaiting_approval
    )


def test_fulfillment_approve_invalid_status(
    staff_api_client,
    fulfillment,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert data["errors"][0]["code"] == OrderErrorCode.INVALID.name


def test_fulfillment_approve_draft_order_prepayment_not_paid(
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....payment import ChargeStatus, CustomPaymentChoices
    from .....payment.models import Payment
    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval
    order = fulfillment.order
    order.origin = OrderOrigin.DRAFT
    order.save(update_fields=["origin"])

    Payment.objects.create(
        order=order,
        fulfillment=fulfillment,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="PREPAY-001",
        total=0,
        captured_amount=0,
        charge_status=ChargeStatus.NOT_CHARGED,
        currency=order.currency,
        is_active=True,
    )

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-UNPAID",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    # when
    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert data["errors"][0]["code"] == OrderErrorCode.CANNOT_FULFILL_UNPAID_ORDER.name


@patch("saleor.plugins.manager.PluginsManager.xero_fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_draft_order_prepayment_paid(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....payment import ChargeStatus, CustomPaymentChoices
    from .....payment.models import Payment
    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval
    order = fulfillment.order
    order.origin = OrderOrigin.DRAFT
    order.save(update_fields=["origin"])

    Payment.objects.create(
        order=order,
        fulfillment=fulfillment,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="PREPAY-001",
        total=0,
        captured_amount=0,
        charge_status=ChargeStatus.FULLY_CHARGED,
        currency=order.currency,
        is_active=True,
    )

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-PROFORMA-PAID",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    from .....invoice import InvoiceType
    from .....invoice.models import Invoice

    def create_final_invoice(f):
        Invoice.objects.update_or_create(
            fulfillment=f,
            type=InvoiceType.FINAL,
            defaults={"order": f.order},
        )

    mock_fulfillment_approved.side_effect = create_final_invoice

    # when
    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()
    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED

    assert mock_email_fulfillment.call_count == 1
    mock_fulfillment_approved.assert_called_once_with(fulfillment)


def test_fulfillment_approve_preorder(
    staff_api_client, fulfillment, permission_group_manage_orders, site_settings
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    site_settings.fulfillment_auto_approve = False
    site_settings.save(update_fields=["fulfillment_auto_approve"])

    order_line = fulfillment.order.lines.first()
    variant = order_line.variant
    variant.is_preorder = True
    variant.save(update_fields=["is_preorder"])
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-PREORDER",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    query = APPROVE_FULFILLMENT_MUTATION

    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": False}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert data["errors"]

    error = data["errors"][0]
    assert error["field"] == "orderLineId"
    assert error["code"] == OrderErrorCode.FULFILL_ORDER_LINE.name


@patch("saleor.plugins.manager.PluginsManager.xero_fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_trigger_webhook_event(
    mock_email_fulfillment,
    mock_xero_fulfillment_approved,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    warehouse = fulfillment.lines.first().stock.warehouse
    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-WEBHOOK",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment)
    start_pick(pick)
    for pick_item in pick.items.all():
        update_pick_item(pick_item, quantity_picked=pick_item.quantity_to_pick)
    complete_pick(pick)

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}

    # when
    staff_api_client.post_graphql(query, variables)

    # then
    mock_xero_fulfillment_approved.assert_called_once_with(fulfillment)


def test_fulfillment_approve_fails_without_pick(
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": False}

    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert data["errors"]
    assert data["errors"][0]["code"] == OrderErrorCode.INVALID.name
    assert "must have a Pick" in data["errors"][0]["message"]


def test_fulfillment_approve_fails_when_pick_not_started(
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
    staff_user,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    assert pick.status == PickStatus.NOT_STARTED

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": False}

    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert data["errors"]
    assert data["errors"][0]["code"] == OrderErrorCode.INVALID.name
    assert "Pick must be completed" in data["errors"][0]["message"]
    assert "Not Started" in data["errors"][0]["message"]


def test_fulfillment_approve_fails_when_pick_in_progress(
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
    staff_user,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    assert pick.status == PickStatus.IN_PROGRESS

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": False}

    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert data["errors"]
    assert data["errors"][0]["code"] == OrderErrorCode.INVALID.name
    assert "Pick must be completed" in data["errors"][0]["message"]
    assert "In Progress" in data["errors"][0]["message"]


@patch("saleor.plugins.manager.PluginsManager.xero_fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_succeeds_when_pick_completed(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
    staff_user,
    warehouse,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-123",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user)
    assert pick.status == PickStatus.COMPLETED

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}

    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()
    assert data["order"]["status"] == OrderStatus.FULFILLED.upper()
    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED

    assert mock_email_fulfillment.call_count == 1
    events = fulfillment.order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event.type == OrderEvents.FULFILLMENT_FULFILLED_ITEMS
    assert event.user == staff_api_client.user
    mock_fulfillment_approved.assert_called_once_with(fulfillment)


def test_fulfillment_approve_fails_without_shipment(
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
    staff_user,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user)
    assert pick.status == PickStatus.COMPLETED

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": False}

    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert data["errors"]
    assert data["errors"][0]["code"] == OrderErrorCode.INVALID.name
    assert "must have a Shipment" in data["errors"][0]["message"]


@patch("saleor.plugins.manager.PluginsManager.xero_fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_succeeds_with_shipment_and_completed_pick(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
    staff_user,
    warehouse,
):
    from decimal import Decimal

    from django.utils import timezone

    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-COMPLETE",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user)
    assert pick.status == PickStatus.COMPLETED

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}

    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()
    fulfillment.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.FULFILLED
    assert fulfillment.shipment == shipment

    mock_fulfillment_approved.assert_called_once_with(fulfillment)


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_creates_fulfillment_sources_from_allocation_sources(
    mock_email_fulfillment,
    staff_api_client,
    full_fulfillment_awaiting_approval,
    permission_group_manage_orders,
    staff_user,
    warehouse,
    shipping_zone,
    channel_USD,
):
    from decimal import Decimal

    from django.db.models import Sum
    from django.utils import timezone

    from .....inventory import PurchaseOrderItemStatus
    from .....inventory.models import PurchaseOrder, PurchaseOrderItem
    from .....shipping import IncoTerm, ShipmentType
    from .....shipping.models import Shipment
    from .....warehouse.models import (
        Allocation,
        AllocationSource,
        FulfillmentSource,
        Warehouse,
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment = full_fulfillment_awaiting_approval

    warehouse.is_owned = True
    warehouse.save(update_fields=["is_owned"])

    supplier_warehouse = Warehouse.objects.create(
        name="Supplier Warehouse",
        slug="supplier-warehouse",
        address=warehouse.address,
        email="supplier@example.com",
        is_owned=False,
    )
    supplier_warehouse.shipping_zones.add(shipping_zone)
    supplier_warehouse.channels.add(channel_USD)

    shipment = Shipment.objects.create(
        source=warehouse.address,
        destination=warehouse.address,
        shipment_type=ShipmentType.OUTBOUND,
        tracking_url="TEST-SOURCE",
        shipping_cost_amount=Decimal("50.00"),
        currency="USD",
        inco_term=IncoTerm.DDP,
        carrier="TEST-CARRIER",
        departed_at=timezone.now(),
    )
    fulfillment.shipment = shipment
    fulfillment.save(update_fields=["shipment"])

    order = fulfillment.order
    po = PurchaseOrder.objects.create(
        source_warehouse=supplier_warehouse,
        destination_warehouse=warehouse,
    )

    for fulfillment_line in fulfillment.lines.all():
        order_line = fulfillment_line.order_line
        stock = fulfillment_line.stock
        quantity = fulfillment_line.quantity

        allocation = Allocation.objects.create(
            order_line=order_line,
            stock=stock,
            quantity_allocated=quantity,
        )

        variant = stock.product_variant
        poi = PurchaseOrderItem.objects.create(
            order=po,
            product_variant=variant,
            quantity_ordered=quantity,
            quantity_allocated=quantity,
            quantity_fulfilled=0,
            total_price_amount=quantity * 10.00,
            currency=order.currency,
            country_of_origin="US",
            status=PurchaseOrderItemStatus.CONFIRMED,
            confirmed_at=timezone.now(),
        )

        AllocationSource.objects.create(
            allocation=allocation,
            purchase_order_item=poi,
            quantity=quantity,
        )

    pick = auto_create_pick_for_fulfillment(fulfillment, user=staff_user)
    start_pick(pick, user=staff_user)
    for pick_item in pick.items.all():
        update_pick_item(
            pick_item, quantity_picked=pick_item.quantity_to_pick, user=staff_user
        )
    complete_pick(pick, user=staff_user)

    assert FulfillmentSource.objects.count() == 0
    assert AllocationSource.objects.filter(allocation__order_line__order=order).exists()

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": False}

    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert not data["errors"]
    assert data["fulfillment"]["status"] == FulfillmentStatus.FULFILLED.upper()

    fulfillment_sources = FulfillmentSource.objects.filter(
        fulfillment_line__fulfillment=fulfillment
    )
    assert fulfillment_sources.exists()

    total_fulfillment_source_quantity = fulfillment_sources.aggregate(
        total=Sum("quantity")
    )["total"]
    total_fulfillment_line_quantity = sum(
        line.quantity for line in fulfillment.lines.all()
    )
    assert total_fulfillment_source_quantity == total_fulfillment_line_quantity

    assert not AllocationSource.objects.filter(
        allocation__order_line__order=order
    ).exists()

    for poi in PurchaseOrderItem.objects.filter(order=po):
        assert poi.quantity_allocated == 0
        assert poi.quantity_fulfilled > 0

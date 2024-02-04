from unittest.mock import patch

import graphene

from .....giftcard.models import GiftCard
from .....order import FulfillmentStatus, OrderEvents, OrderStatus
from .....order.actions import fulfill_order_lines
from .....order.error_codes import OrderErrorCode
from .....order.fetch import OrderLineInfo
from .....order.models import OrderLine
from .....plugins.manager import get_plugins_manager
from .....product.models import Product
from .....webhook.event_types import WebhookEventAsyncType
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


@patch("saleor.plugins.manager.PluginsManager.fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    staff_api_client,
    fulfillment,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
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
    mock_fulfillment_approved.assert_called_once_with(fulfillment, True)


def test_fulfillment_approve_by_user_no_channel_access(
    staff_api_client,
    fulfillment,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = fulfillment.order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_by_app(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    app_api_client,
    fulfillment,
    permission_manage_orders,
):
    # given
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
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
    mock_fulfillment_approved.assert_called_once_with(fulfillment, True)


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_delete_products_before_approval_allow_stock_exceeded_true(
    mock_email_fulfillment,
    staff_api_client,
    fulfillment,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])

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


@patch("saleor.plugins.manager.PluginsManager.fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_delete_products_before_approval_allow_stock_exceeded_false(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    staff_api_client,
    fulfillment,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])

    Product.objects.all().delete()

    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {
        "id": fulfillment_id,
        "notifyCustomer": True,
        "allowStockToBeExceeded": False,
    }
    response = staff_api_client.post_graphql(query, variables)

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

    assert mock_email_fulfillment.call_count == 1
    events = fulfillment.order.events.all()
    assert len(events) == 0
    mock_fulfillment_approved.assert_not_called()


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_gift_cards_created(
    mock_email_fulfillment,
    staff_api_client,
    fulfillment,
    permission_group_manage_orders,
    gift_card_shippable_order_line,
    gift_card_non_shippable_order_line,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])

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
    fulfillment,
    permission_group_manage_orders,
):
    # make stocks exceeded
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    for stock in [line.stock for line in fulfillment.lines.all()]:
        stock.quantity = -99
        stock.save()

    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
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
    fulfillment,
    permission_group_manage_orders,
):
    # make stocks exceeded
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    for stock in [line.stock for line in fulfillment.lines.all()]:
        stock.quantity = -99
        stock.save()

    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
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


@patch("saleor.plugins.manager.PluginsManager.fulfillment_approved")
@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer", autospec=True)
def test_fulfillment_approve_partial_order_fulfill(
    mock_email_fulfillment,
    mock_fulfillment_approved,
    staff_api_client,
    fulfillment_awaiting_approval,
    permission_group_manage_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = APPROVE_FULFILLMENT_MUTATION
    order = fulfillment_awaiting_approval.order

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

    fulfillment_id = graphene.Node.to_global_id(
        "Fulfillment", fulfillment_awaiting_approval.id
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
    fulfillment_awaiting_approval.refresh_from_db()
    assert fulfillment_awaiting_approval.status == FulfillmentStatus.FULFILLED

    assert mock_email_fulfillment.call_count == 0
    mock_fulfillment_approved.assert_called_once_with(
        fulfillment_awaiting_approval, False
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


def test_fulfillment_approve_order_unpaid(
    staff_api_client,
    fulfillment,
    site_settings,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    site_settings.fulfillment_allow_unpaid = False
    site_settings.save(update_fields=["fulfillment_allow_unpaid"])
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentApprove"]
    assert data["errors"][0]["code"] == OrderErrorCode.CANNOT_FULFILL_UNPAID_ORDER.name


def test_fulfillment_approve_preorder(
    staff_api_client, fulfillment, permission_group_manage_orders, site_settings
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    site_settings.fulfillment_auto_approve = False
    site_settings.save(update_fields=["fulfillment_auto_approve"])

    order_line = fulfillment.order.lines.first()
    variant = order_line.variant
    variant.is_preorder = True
    variant.save(update_fields=["is_preorder"])
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
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


@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_fulfillment_approve_trigger_webhook_event(
    mocked_trigger_async,
    staff_api_client,
    fulfillment,
    permission_group_manage_orders,
    settings,
    subscription_fulfillment_approved_webhook,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
    query = APPROVE_FULFILLMENT_MUTATION
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    variables = {"id": fulfillment_id, "notifyCustomer": True}

    # when
    staff_api_client.post_graphql(query, variables)

    # then
    mocked_trigger_async.assert_called_once()
    assert mocked_trigger_async.call_args[0][1] == (
        WebhookEventAsyncType.FULFILLMENT_APPROVED
    )
    assert mocked_trigger_async.call_args[0][3] == {
        "fulfillment": fulfillment,
        "notify_customer": True,
    }

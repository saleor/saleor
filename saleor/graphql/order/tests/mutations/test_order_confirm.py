import uuid
from unittest.mock import ANY, patch

import graphene

from .....core.notify_events import NotifyEventType
from .....core.tests.utils import get_site_context_payload
from .....order import OrderStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....order.fetch import fetch_order_info
from .....order.models import OrderEvent
from .....order.notifications import get_default_order_payload
from .....order.utils import updates_amounts_for_order
from .....payment import TransactionAction, TransactionEventType
from .....payment.models import TransactionItem
from .....product.models import ProductVariant
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_CONFIRM_MUTATION = """
    mutation orderConfirm($id: ID!) {
        orderConfirm(id: $id) {
            errors {
                field
                code
            }
            order {
                status
            }
        }
    }
"""


@patch("saleor.order.actions.handle_fully_paid_order")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.payment.gateway.capture")
def test_order_confirm(
    capture_mock,
    mocked_notify,
    handle_fully_paid_order_mock,
    staff_api_client,
    order_unconfirmed,
    permission_group_manage_orders,
    payment_txn_preauth,
    site_settings,
):
    # given
    payment_txn_preauth.order = order_unconfirmed
    payment_txn_preauth.captured_amount = order_unconfirmed.total.gross.amount
    payment_txn_preauth.total = order_unconfirmed.total.gross.amount
    payment_txn_preauth.save(update_fields=["order", "captured_amount", "total"])

    order_unconfirmed.total_charged = order_unconfirmed.total.gross
    order_unconfirmed.save(update_fields=["total_charged_amount"])
    updates_amounts_for_order(order_unconfirmed)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    assert not OrderEvent.objects.exists()

    # when
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
    )

    # then
    order_data = get_graphql_content(response)["data"]["orderConfirm"]["order"]

    assert order_data["status"] == OrderStatus.UNFULFILLED.upper()
    order_unconfirmed.refresh_from_db()
    assert order_unconfirmed.status == OrderStatus.UNFULFILLED
    assert OrderEvent.objects.count() == 2
    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.CONFIRMED,
    ).exists()

    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.PAYMENT_CAPTURED,
        parameters__amount=payment_txn_preauth.get_total().amount,
    ).exists()

    capture_mock.assert_called_once_with(
        payment_txn_preauth, ANY, channel_slug=order_unconfirmed.channel.slug
    )
    expected_payload = {
        "order": get_default_order_payload(order_unconfirmed, ""),
        "recipient_email": order_unconfirmed.user.email,
        "requester_user_id": to_global_id_or_none(staff_api_client.user),
        "requester_app_id": None,
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMED,
        expected_payload,
        channel_slug=order_unconfirmed.channel.slug,
    )
    order_info = fetch_order_info(order_unconfirmed)
    handle_fully_paid_order_mock.assert_called_once_with(
        ANY, order_info, staff_api_client.user, None, site_settings
    )


@patch("saleor.graphql.order.mutations.order_confirm.request_charge_action")
def test_order_confirm_charge_transaction_items(
    request_charge_action_mock,
    staff_api_client,
    order_unconfirmed_with_lines,
    permission_group_manage_orders,
):
    # given
    transaction = TransactionItem.objects.create(
        token=uuid.uuid4(),
        name="ti",
        order_id=order_unconfirmed_with_lines.id,
        available_actions=[TransactionAction.CHARGE],
        authorized_value=order_unconfirmed_with_lines.total.gross.amount,
        currency=order_unconfirmed_with_lines.currency,
    )

    order_unconfirmed_with_lines.total_charged = (
        order_unconfirmed_with_lines.total.gross
    )
    order_unconfirmed_with_lines.save(update_fields=["total_charged_amount"])
    updates_amounts_for_order(order_unconfirmed_with_lines)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    assert not OrderEvent.objects.exists()

    # when
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed_with_lines.id)},
    )

    # then
    assert not get_graphql_content(response)["data"]["orderConfirm"]["errors"]

    request_charge_action_mock.assert_called_once_with(
        channel_slug=order_unconfirmed_with_lines.channel.slug,
        user=staff_api_client.user,
        app=None,
        transaction=transaction,
        manager=ANY,
        charge_value=order_unconfirmed_with_lines.total.gross.amount,
        request_event=ANY,
    )
    assert transaction.events.filter(type=TransactionEventType.CHARGE_REQUEST).exists()


@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.payment.gateway.capture")
def test_order_confirm_without_sku(
    capture_mock,
    mocked_notify,
    staff_api_client,
    order_unconfirmed,
    permission_group_manage_orders,
    payment_txn_preauth,
    site_settings,
):
    order_unconfirmed.lines.update(product_sku=None)
    ProductVariant.objects.update(sku=None)

    payment_txn_preauth.order = order_unconfirmed
    payment_txn_preauth.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    assert not OrderEvent.objects.exists()
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
    )
    order_data = get_graphql_content(response)["data"]["orderConfirm"]["order"]

    assert order_data["status"] == OrderStatus.UNFULFILLED.upper()
    order_unconfirmed.refresh_from_db()
    assert order_unconfirmed.status == OrderStatus.UNFULFILLED
    assert OrderEvent.objects.count() == 2
    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.CONFIRMED,
    ).exists()

    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.PAYMENT_CAPTURED,
        parameters__amount=payment_txn_preauth.get_total().amount,
    ).exists()

    capture_mock.assert_called_once_with(
        payment_txn_preauth, ANY, channel_slug=order_unconfirmed.channel.slug
    )
    expected_payload = {
        "order": get_default_order_payload(order_unconfirmed, ""),
        "recipient_email": order_unconfirmed.user.email,
        "requester_user_id": to_global_id_or_none(staff_api_client.user),
        "requester_app_id": None,
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMED,
        expected_payload,
        channel_slug=order_unconfirmed.channel.slug,
    )


def test_order_confirm_unfulfilled(
    staff_api_client, order, permission_group_manage_orders
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION, {"id": graphene.Node.to_global_id("Order", order.id)}
    )
    content = get_graphql_content(response)["data"]["orderConfirm"]
    errors = content["errors"]

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED
    assert content["order"] is None
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


def test_order_confirm_no_products_in_order(
    staff_api_client, order_unconfirmed, permission_group_manage_orders
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_unconfirmed.lines.set([])
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
    )
    content = get_graphql_content(response)["data"]["orderConfirm"]
    errors = content["errors"]

    order_unconfirmed.refresh_from_db()
    assert order_unconfirmed.is_unconfirmed()
    assert content["order"] is None
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


@patch("saleor.payment.gateway.capture")
def test_order_confirm_wont_call_capture_for_non_active_payment(
    capture_mock,
    staff_api_client,
    order_unconfirmed,
    permission_group_manage_orders,
    payment_txn_preauth,
):
    payment_txn_preauth.order = order_unconfirmed
    payment_txn_preauth.is_active = False
    payment_txn_preauth.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    assert not OrderEvent.objects.exists()
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
    )
    order_data = get_graphql_content(response)["data"]["orderConfirm"]["order"]

    assert order_data["status"] == OrderStatus.UNFULFILLED.upper()
    order_unconfirmed.refresh_from_db()
    assert order_unconfirmed.status == OrderStatus.UNFULFILLED
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.CONFIRMED,
    ).exists()
    assert not capture_mock.called


def test_order_confirm_update_display_gross_prices(
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    channel = order.channel
    tax_config = channel.tax_configuration

    # Change the current display_gross_prices to the opposite of what is set in the
    # order.display_gross_prices.
    new_display_gross_prices = not order.display_gross_prices

    tax_config.display_gross_prices = new_display_gross_prices
    tax_config.save()
    tax_config.country_exceptions.all().delete()

    # when
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order.id)},
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderConfirm"]["errors"]
    order.refresh_from_db()
    assert order.display_gross_prices == new_display_gross_prices


def test_order_confirm_by_user_no_channel_access(
    staff_api_client,
    order_unconfirmed,
    permission_group_all_perms_channel_USD_only,
    payment_txn_preauth,
    channel_PLN,
):
    # given
    order_unconfirmed.total_charged = order_unconfirmed.total.gross
    order_unconfirmed.channel = channel_PLN
    order_unconfirmed.save(update_fields=["total_charged_amount", "channel"])

    payment_txn_preauth.order = order_unconfirmed
    payment_txn_preauth.captured_amount = order_unconfirmed.total.gross.amount
    payment_txn_preauth.total = order_unconfirmed.total.gross.amount
    payment_txn_preauth.save(update_fields=["order", "captured_amount", "total"])

    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    assert not OrderEvent.objects.exists()

    # when
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
    )

    # then
    assert_no_permission(response)


@patch("saleor.order.actions.handle_fully_paid_order")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.payment.gateway.capture")
def test_order_confirm_by_app(
    capture_mock,
    mocked_notify,
    handle_fully_paid_order_mock,
    app_api_client,
    order_unconfirmed,
    permission_manage_orders,
    payment_txn_preauth,
    site_settings,
):
    # given
    payment_txn_preauth.order = order_unconfirmed
    payment_txn_preauth.captured_amount = order_unconfirmed.total.gross.amount
    payment_txn_preauth.total = order_unconfirmed.total.gross.amount
    payment_txn_preauth.save(update_fields=["order", "captured_amount", "total"])

    order_unconfirmed.total_charged = order_unconfirmed.total.gross
    order_unconfirmed.save(update_fields=["total_charged_amount"])
    updates_amounts_for_order(order_unconfirmed)

    assert not OrderEvent.objects.exists()

    # when
    response = app_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
        permissions=(permission_manage_orders,),
    )

    # then
    order_data = get_graphql_content(response)["data"]["orderConfirm"]["order"]

    assert order_data["status"] == OrderStatus.UNFULFILLED.upper()
    order_unconfirmed.refresh_from_db()
    assert order_unconfirmed.status == OrderStatus.UNFULFILLED
    assert OrderEvent.objects.count() == 2
    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        app=app_api_client.app,
        type=order_events.OrderEvents.CONFIRMED,
    ).exists()

    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        app=app_api_client.app,
        type=order_events.OrderEvents.PAYMENT_CAPTURED,
        parameters__amount=payment_txn_preauth.get_total().amount,
    ).exists()

    capture_mock.assert_called_once_with(
        payment_txn_preauth, ANY, channel_slug=order_unconfirmed.channel.slug
    )
    expected_payload = {
        "order": get_default_order_payload(order_unconfirmed, ""),
        "recipient_email": order_unconfirmed.user.email,
        "requester_user_id": None,
        "requester_app_id": to_global_id_or_none(app_api_client.app),
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMED,
        expected_payload,
        channel_slug=order_unconfirmed.channel.slug,
    )
    order_info = fetch_order_info(order_unconfirmed)
    handle_fully_paid_order_mock.assert_called_once_with(
        ANY, order_info, None, app_api_client.app, site_settings
    )

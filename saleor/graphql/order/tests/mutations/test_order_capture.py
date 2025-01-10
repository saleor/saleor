from unittest.mock import ANY, call, patch

import graphene
from django.test import override_settings

from .....core.models import EventDelivery
from .....core.notify import NotifyEventType
from .....core.tests.utils import get_site_context_payload
from .....order import OrderStatus
from .....order import events as order_events
from .....order.actions import call_order_event, order_charged
from .....order.notifications import get_default_order_payload
from .....payment import ChargeStatus
from .....payment.models import Payment
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....payment.types import PaymentChargeStatusEnum
from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_CAPTURE_MUTATION = """
        mutation captureOrder($id: ID!, $amount: PositiveDecimal!) {
            orderCapture(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    paymentStatusDisplay
                    isPaid
                    totalCharged {
                        amount
                    }
                    totalCaptured {
                        amount
                    }
                }
                errors{
                    field
                    message
                    code
                }
            }
        }
"""


@patch(
    "saleor.graphql.order.mutations.order_capture.order_charged", wraps=order_charged
)
@patch("saleor.giftcard.utils.fulfill_non_shippable_gift_cards")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_order_capture(
    mocked_notify,
    fulfill_non_shippable_gift_cards_mock,
    order_charged_mock,
    staff_api_client,
    permission_group_manage_orders,
    payment_txn_preauth,
    staff_user,
    site_settings,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = payment_txn_preauth.order

    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_preauth.total)
    variables = {"id": order_id, "amount": amount}

    # when
    response = staff_api_client.post_graphql(ORDER_CAPTURE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCapture"]["order"]
    order.refresh_from_db()
    assert data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_CHARGED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.FULLY_CHARGED)
    assert data["paymentStatusDisplay"] == payment_status_display
    assert data["isPaid"]
    assert data["totalCaptured"]["amount"] == float(amount)
    assert data["totalCharged"]["amount"] == float(amount)

    event_captured, event_order_fully_paid = order.events.all()

    assert event_captured.type == order_events.OrderEvents.PAYMENT_CAPTURED
    assert event_captured.user == staff_user
    assert event_captured.parameters == {
        "amount": str(amount),
        "payment_gateway": "mirumee.payments.dummy",
        "payment_id": "",
    }

    assert event_order_fully_paid.type == order_events.OrderEvents.ORDER_FULLY_PAID
    assert event_order_fully_paid.user == staff_user

    payment = Payment.objects.get()
    expected_payment_payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "payment": {
            "created": payment.created_at,
            "modified": payment.modified_at,
            "charge_status": payment.charge_status,
            "total": payment.total,
            "captured_amount": payment.captured_amount,
            "currency": payment.currency,
        },
        **get_site_context_payload(site_settings.site),
    }

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ORDER_PAYMENT_CONFIRMATION
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payment_payload
    assert called_kwargs["channel_slug"] == order.channel.slug

    fulfill_non_shippable_gift_cards_mock.assert_called_once_with(
        order, list(order.lines.all()), site_settings, staff_api_client.user, None, ANY
    )
    assert order_charged_mock.called


def test_order_capture_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    payment_txn_preauth,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = payment_txn_preauth.order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_preauth.total)
    variables = {"id": order_id, "amount": amount}

    # when
    response = staff_api_client.post_graphql(ORDER_CAPTURE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_order_capture_by_app(
    app_api_client,
    payment_txn_preauth,
    permission_manage_orders,
):
    # given
    order = payment_txn_preauth.order

    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_preauth.total)
    variables = {"id": order_id, "amount": amount}

    # when
    response = app_api_client.post_graphql(
        ORDER_CAPTURE_MUTATION, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCapture"]["order"]
    order.refresh_from_db()
    assert data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_CHARGED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.FULLY_CHARGED)
    assert data["paymentStatusDisplay"] == payment_status_display
    assert data["isPaid"]
    assert data["totalCaptured"]["amount"] == float(amount)


@patch(
    "saleor.order.actions.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(
    PLUGINS=[
        "saleor.plugins.webhook.plugin.WebhookPlugin",
        "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin",
    ]
)
def test_order_capture_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    staff_api_client,
    permission_group_manage_orders,
    payment_txn_preauth,
    staff_user,
    settings,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_PAID,
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_FULLY_PAID,
        ]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = payment_txn_preauth.order
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])
    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_preauth.total)
    variables = {"id": order_id, "amount": amount}

    # when
    response = staff_api_client.post_graphql(ORDER_CAPTURE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderCapture"]["errors"]

    # confirm that event delivery was generated for each async webhook.
    order_paid_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_PAID,
    )
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    order_fully_paid_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_FULLY_PAID,
    )

    order_deliveries = [
        order_fully_paid_delivery,
        order_paid_delivery,
        order_updated_delivery,
    ]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

    tax_delivery_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )

    assert wrapped_call_order_event.called

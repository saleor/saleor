"""After the order commits, one refused webhook publish loses the rest of order creation.

checkoutComplete commits the order, then runs two ``transaction.on_commit``
callbacks: ``order_created`` (the order's events and webhooks) and
``send_order_confirmation``. Django stops running on-commit callbacks at the first
that raises, so when the broker refuses the ORDER_CREATED webhook's publish, the
customer's confirmation, the webhooks after it and the order's history are lost,
and nothing runs them again. See https://github.com/saleor/saleor/issues/19835.
"""

from unittest.mock import patch

import pytest
from kombu.exceptions import OperationalError

from .....checkout import calculations
from .....checkout import complete_checkout as complete_checkout_module
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.payment_utils import update_checkout_payment_statuses
from .....core.models import EventDelivery
from .....order import OrderChargeStatus
from .....order.models import Order
from .....plugins.manager import get_plugins_manager
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook
from .....webhook.transport.asynchronous.transport import send_webhook_request_async
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_COMPLETE = """
mutation checkoutComplete($id: ID) {
  checkoutComplete(id: $id) {
    order { id }
    errors { field code message }
  }
}
"""

ORDER_EVENTS = {
    WebhookEventAsyncType.ORDER_CREATED,
    WebhookEventAsyncType.ORDER_FULLY_PAID,
    WebhookEventAsyncType.ORDER_CONFIRMED,
}


def _pay_in_full(checkout, address, checkout_delivery, transaction_item_generator):
    checkout.shipping_address = address
    checkout.billing_address = address
    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.save()
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines
    )
    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=total.gross.amount
    )
    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
        checkout_has_lines=bool(lines),
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "broker_refuses_a_publish",
    [
        pytest.param(False, id="broker up"),
        pytest.param(
            True,
            id="broker refuses one publish",
            marks=pytest.mark.xfail(
                strict=True,
                reason=(
                    "a refused publish in order_created skips every later on-commit "
                    "callback: https://github.com/saleor/saleor/issues/19835"
                ),
            ),
        ),
    ],
)
def test_checkout_complete_confirms_and_announces_a_paid_order(
    broker_refuses_a_publish,
    settings,
    user_api_client,
    checkout_with_item,
    address,
    checkout_delivery,
    transaction_item_generator,
    webhook_app,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook = Webhook.objects.create(
        name="erp", app=webhook_app, target_url="https://erp.example.com/saleor"
    )
    for event_type in ORDER_EVENTS:
        webhook.events.create(event_type=event_type)
    checkout = checkout_with_item
    _pay_in_full(checkout, address, checkout_delivery, transaction_item_generator)
    checkout.channel.automatically_confirm_all_new_orders = True
    checkout.channel.save()

    publishes = []

    def broker(*args, **kwargs):
        publishes.append(kwargs)
        if broker_refuses_a_publish and len(publishes) == 1:
            raise OperationalError("[Errno 111] Connection refused")

    # when
    with (
        patch.object(send_webhook_request_async, "apply_async", side_effect=broker),
        patch.object(
            complete_checkout_module,
            "send_order_confirmation",
            wraps=complete_checkout_module.send_order_confirmation,
        ) as send_order_confirmation,
    ):
        response = user_api_client.post_graphql(
            MUTATION_CHECKOUT_COMPLETE, {"id": to_global_id_or_none(checkout)}
        )

    # then
    order = Order.objects.get()
    assert order.charge_status == OrderChargeStatus.FULL
    assert send_order_confirmation.call_count == 1, (
        "the customer was never sent the order confirmation"
    )
    created = set(
        EventDelivery.objects.filter(webhook=webhook).values_list(
            "event_type", flat=True
        )
    )
    assert created == ORDER_EVENTS, (
        f"webhooks never created for {sorted(ORDER_EVENTS - created)}"
    )
    content = get_graphql_content(response)
    assert content["data"]["checkoutComplete"]["order"]["id"] == to_global_id_or_none(
        order
    )

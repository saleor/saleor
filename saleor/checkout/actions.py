from collections.abc import Iterable
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Callable, Optional, cast

from django.utils import timezone

from ..core.utils.events import (
    call_event_including_protected_events,
    webhook_async_event_requires_sync_webhooks_to_trigger,
)
from ..payment.models import TransactionItem
from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..webhook.utils import get_webhooks_for_multiple_events
from . import CheckoutChargeStatus
from .calculations import fetch_checkout_data
from .fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from .models import Checkout
from .payment_utils import update_refundable_for_checkout

if TYPE_CHECKING:
    from ..account.models import Address
    from ..plugins.manager import PluginsManager
    from ..webhook.models import Webhook


def call_checkout_event_for_checkout(
    manager: "PluginsManager",
    event_func: Callable,
    event_name: str,
    checkout: "Checkout",
):
    webhook_event_map = get_webhooks_for_multiple_events(
        [event_name, *WebhookEventSyncType.CHECKOUT_EVENTS]
    )
    if not webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name,
        webhook_event_map,
        possible_sync_events=WebhookEventSyncType.CHECKOUT_EVENTS,
    ):
        call_event_including_protected_events(event_func, checkout)
        return

    lines_info, _ = fetch_checkout_lines(
        checkout,
    )
    checkout_info = fetch_checkout_info(
        checkout,
        lines_info,
        manager,
    )
    call_checkout_event_for_checkout_info(
        manager=manager,
        event_func=event_func,
        event_name=event_name,
        checkout_info=checkout_info,
        lines=lines_info,
        webhook_event_map=webhook_event_map,
    )
    return


def call_checkout_event_for_checkout_info(
    manager: "PluginsManager",
    event_func: Callable,
    event_name: str,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"] = None,
    webhook_event_map: Optional[dict[str, set["Webhook"]]] = None,
):
    checkout = checkout_info.checkout
    if webhook_event_map is None:
        webhook_event_map = get_webhooks_for_multiple_events(
            [event_name, *WebhookEventSyncType.CHECKOUT_EVENTS]
        )

    # No need to trigger additional sync webhook when we don't have active webhook or
    # we don't have active sync checkout webhooks
    if not webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name,
        webhook_event_map,
        possible_sync_events=WebhookEventSyncType.CHECKOUT_EVENTS,
    ):
        call_event_including_protected_events(event_func, checkout)
        return None

    _ = checkout_info.all_shipping_methods

    # + timedelta(seconds=10) to confirm that triggered webhooks will still have a
    # valid prices. Triggered only when we have active sync tax webhook
    if (
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES in webhook_event_map
        and checkout.price_expiration < timezone.now() + timedelta(seconds=10)
    ):
        fetch_checkout_data(
            checkout_info=checkout_info,
            manager=manager,
            lines=lines,
            address=address
            or checkout_info.shipping_address
            or checkout_info.billing_address,
            force_update=True,
        )

    call_event_including_protected_events(event_func, checkout)
    return None


def update_last_transaction_modified_at_for_checkout(
    checkout: Checkout, transaction: TransactionItem
):
    if (
        not checkout.last_transaction_modified_at
        or checkout.last_transaction_modified_at < transaction.modified_at
    ):
        checkout.last_transaction_modified_at = transaction.modified_at
        checkout.save(update_fields=["last_transaction_modified_at"])


def transaction_amounts_for_checkout_updated(
    transaction: TransactionItem,
    manager: "PluginsManager",
):
    if not transaction.checkout_id:
        return
    checkout = cast(Checkout, transaction.checkout)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    previous_charge_status = checkout_info.checkout.charge_status
    fetch_checkout_data(checkout_info, manager, lines, force_status_update=True)
    previous_charge_status_is_fully_paid = previous_charge_status in [
        CheckoutChargeStatus.FULL,
        CheckoutChargeStatus.OVERCHARGED,
    ]
    current_status_is_fully_paid = checkout_info.checkout.charge_status in [
        CheckoutChargeStatus.FULL,
        CheckoutChargeStatus.OVERCHARGED,
    ]

    update_last_transaction_modified_at_for_checkout(checkout, transaction)

    refundable = transaction.last_refund_success and (
        transaction.authorized_value > Decimal(0)
        or transaction.charged_value > Decimal(0)
    )
    if refundable != checkout.automatically_refundable:
        # if last_refund_status is different than automatically_refundable
        # we need to recalculate automatically_refundable based on the rest of
        # checkout's transactions
        update_refundable_for_checkout(checkout.pk)

    if not previous_charge_status_is_fully_paid and current_status_is_fully_paid:
        call_checkout_event_for_checkout_info(
            manager,
            event_func=manager.checkout_fully_paid,
            event_name=WebhookEventAsyncType.CHECKOUT_FULLY_PAID,
            checkout_info=checkout_info,
            lines=lines,
        )

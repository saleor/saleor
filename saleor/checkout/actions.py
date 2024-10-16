import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, cast

from django.utils import timezone

from ..core.utils.events import (
    call_event_including_protected_events,
    webhook_async_event_requires_sync_webhooks_to_trigger,
)
from ..payment.models import TransactionItem
from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..webhook.utils import get_webhooks_for_multiple_events
from . import CheckoutAuthorizeStatus, CheckoutChargeStatus
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
    from ..account.models import Address, User
    from ..app.models import App
    from ..webhook.models import Webhook

from ..plugins.manager import PluginsManager

CHECKOUT_WEBHOOK_EVENT_MAP = {
    WebhookEventAsyncType.CHECKOUT_CREATED: PluginsManager.checkout_created.__name__,
    WebhookEventAsyncType.CHECKOUT_UPDATED: PluginsManager.checkout_updated.__name__,
    WebhookEventAsyncType.CHECKOUT_FULLY_PAID: PluginsManager.checkout_fully_paid.__name__,
    WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED: PluginsManager.checkout_metadata_updated.__name__,
}


def call_checkout_event(
    manager: "PluginsManager",
    event_name: str,
    checkout: "Checkout",
):
    if event_name not in CHECKOUT_WEBHOOK_EVENT_MAP:
        raise ValueError(f"Event {event_name} not found in CHECKOUT_WEBHOOK_EVENT_MAP.")

    webhook_event_map = get_webhooks_for_multiple_events(
        [event_name, *WebhookEventSyncType.CHECKOUT_EVENTS]
    )
    webhooks = webhook_event_map.get(event_name, set())
    if not webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name,
        webhook_event_map,
        possible_sync_events=WebhookEventSyncType.CHECKOUT_EVENTS,
    ):
        plugin_manager_method_name = CHECKOUT_WEBHOOK_EVENT_MAP[event_name]
        event_func = getattr(manager, plugin_manager_method_name)
        call_event_including_protected_events(event_func, checkout, webhooks=webhooks)
        return

    lines_info, _ = fetch_checkout_lines(
        checkout,
    )
    checkout_info = fetch_checkout_info(
        checkout,
        lines_info,
        manager,
    )
    call_checkout_info_event(
        manager=manager,
        event_name=event_name,
        checkout_info=checkout_info,
        lines=lines_info,
        webhook_event_map=webhook_event_map,
    )
    return


def _trigger_checkout_sync_webhooks(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    webhook_event_map: dict[str, set["Webhook"]],
    address: Optional["Address"] = None,
):
    _ = checkout_info.all_shipping_methods

    # + timedelta(seconds=10) to confirm that triggered webhooks will still have
    # valid prices. Triggered only when we have active sync tax webhook.
    if webhook_event_map.get(
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    ) and checkout_info.checkout.price_expiration < timezone.now() + datetime.timedelta(
        seconds=10
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


def call_checkout_events(
    manager: "PluginsManager",
    event_names: list[str],
    checkout: "Checkout",
):
    missing_events = set(event_names).difference(CHECKOUT_WEBHOOK_EVENT_MAP.keys())
    if missing_events:
        raise ValueError(
            f"Events {missing_events} not found in CHECKOUT_WEBHOOK_EVENT_MAP."
        )

    webhook_event_map = get_webhooks_for_multiple_events(
        [*event_names, *WebhookEventSyncType.CHECKOUT_EVENTS]
    )
    any_event_requires_sync_webhooks = any(
        webhook_async_event_requires_sync_webhooks_to_trigger(
            event_name,
            webhook_event_map,
            possible_sync_events=WebhookEventSyncType.CHECKOUT_EVENTS,
        )
        for event_name in event_names
    )
    if any_event_requires_sync_webhooks:
        lines_info, _ = fetch_checkout_lines(
            checkout,
        )
        checkout_info = fetch_checkout_info(
            checkout,
            lines_info,
            manager,
        )
        _trigger_checkout_sync_webhooks(
            manager, checkout_info, lines_info, webhook_event_map=webhook_event_map
        )

    for event_name in event_names:
        plugin_manager_method_name = CHECKOUT_WEBHOOK_EVENT_MAP[event_name]
        webhooks = webhook_event_map.get(event_name, set())
        event_func = getattr(manager, plugin_manager_method_name)
        call_event_including_protected_events(event_func, checkout, webhooks=webhooks)


def call_checkout_info_event(
    manager: "PluginsManager",
    event_name: str,
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    address: Optional["Address"] = None,
    webhook_event_map: Optional[dict[str, set["Webhook"]]] = None,
) -> None:
    checkout = checkout_info.checkout
    if webhook_event_map is None:
        webhook_event_map = get_webhooks_for_multiple_events(
            [event_name, *WebhookEventSyncType.CHECKOUT_EVENTS]
        )
    if event_name not in CHECKOUT_WEBHOOK_EVENT_MAP:
        raise ValueError(f"Event {event_name} not found in CHECKOUT_WEBHOOK_EVENT_MAP.")

    webhooks = webhook_event_map.get(event_name, set())

    plugin_manager_method_name = CHECKOUT_WEBHOOK_EVENT_MAP[event_name]
    event_func = getattr(manager, plugin_manager_method_name)

    # No need to trigger additional sync webhook when we don't have active webhook or
    # we don't have active sync checkout webhooks
    if not webhook_async_event_requires_sync_webhooks_to_trigger(
        event_name,
        webhook_event_map,
        possible_sync_events=WebhookEventSyncType.CHECKOUT_EVENTS,
    ):
        call_event_including_protected_events(event_func, checkout, webhooks=webhooks)
        return

    _trigger_checkout_sync_webhooks(
        manager,
        checkout_info,
        lines,
        address=address,
        webhook_event_map=webhook_event_map,
    )

    call_event_including_protected_events(event_func, checkout, webhooks=webhooks)
    return


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
    user: Optional["User"],
    app: Optional["App"],
):
    from .tasks import automatic_checkout_completion_task

    if not transaction.checkout_id:
        return
    checkout = cast(Checkout, transaction.checkout)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    previous_charge_status = checkout_info.checkout.charge_status
    previous_authorize_status = checkout_info.checkout.authorize_status
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
        call_checkout_info_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_FULLY_PAID,
            checkout_info=checkout_info,
            lines=lines,
        )

    channel = checkout_info.channel
    if (
        channel.automatically_complete_fully_paid_checkouts
        and
        # ensure that checkout completion is triggered only once
        (
            previous_authorize_status != CheckoutAuthorizeStatus.FULL
            and checkout_info.checkout.authorize_status == CheckoutAuthorizeStatus.FULL
        )
    ):
        user_id = user.id if user else None
        app_id = app.id if app else None
        automatic_checkout_completion_task.delay(checkout.pk, user_id, app_id)

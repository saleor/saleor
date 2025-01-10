from django.db import transaction

from ...checkout.fetch import CheckoutInfo
from ...checkout.models import Checkout
from ...order.fetch import OrderInfo
from ...order.models import Order
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.models import Webhook


def get_is_deferred_payload(event_name: str) -> bool:
    """Return True if the event has deferred payload.

    When the event has deferred payload, the payload will be generated in the Celery
    task during webhook delivery. In such case, any additional sync calls needed to
    generated the payload are also run in this task, and we don't need to call them
    manually before.
    """
    return WebhookEventAsyncType.EVENT_MAP.get(event_name, {}).get(
        "is_deferred_payload", False
    )


def any_webhook_has_subscription(
    events: list[str], webhook_event_map: dict[str, set["Webhook"]]
) -> bool:
    event_has_subscription = False
    for event in events:
        event_has_subscription = any(
            bool(webhook.subscription_query)
            for webhook in webhook_event_map.get(event, [])
        )
        if event_has_subscription:
            break
    return event_has_subscription


def any_webhook_is_active_for_events(
    events: list[str], webhook_event_map: dict[str, set["Webhook"]]
) -> bool:
    """Check if any webhook is active for given events."""

    active_webhook_events = {
        event for event, webhooks in webhook_event_map.items() if webhooks
    }
    if not active_webhook_events.intersection(events):
        return False
    return True


def _validate_event_name(event_name, webhook_event_map):
    is_async_event = event_name in WebhookEventAsyncType.ALL
    if not is_async_event:
        raise ValueError(f"Event {event_name} is not an async event.")

    if event_name not in webhook_event_map:
        raise ValueError(f"Event {event_name} not found in webhook_event_map.")


def _validate_webhook_event_map(webhook_event_map, possible_sync_events):
    missing_possible_sync_events_in_map = set(possible_sync_events).difference(
        webhook_event_map.keys()
    )
    if missing_possible_sync_events_in_map:
        raise ValueError(
            f"Event {missing_possible_sync_events_in_map} not found in webhook_event_map."
        )


def webhook_async_event_requires_sync_webhooks_to_trigger(
    event_name: str,
    webhook_event_map: dict[str, set["Webhook"]],
    possible_sync_events: list[str],
) -> bool:
    """Check if calling the event requires additional actions.

    In case of having active webhook with the `event_name`, the function will return
    True, when any sync from `possible_sync_events`'s webhooks are active. `True`
    means that sync webhook should be triggered first, before calling async webhook.
    """
    _validate_event_name(event_name, webhook_event_map)
    _validate_webhook_event_map(webhook_event_map, possible_sync_events)

    is_deferred_payload = get_is_deferred_payload(event_name)
    if is_deferred_payload:
        return False

    if not webhook_event_map[event_name] and not webhook_event_map.get(
        WebhookEventAsyncType.ANY
    ):
        return False

    if not any_webhook_is_active_for_events(possible_sync_events, webhook_event_map):
        return False

    async_webhooks_have_subscriptions = any_webhook_has_subscription(
        [event_name], webhook_event_map
    )
    if not async_webhooks_have_subscriptions:
        return False

    sync_events_have_subscriptions = any_webhook_has_subscription(
        possible_sync_events, webhook_event_map
    )
    if not sync_events_have_subscriptions:
        return False
    return True


def call_event_including_protected_events(func_obj, *func_args, **func_kwargs):
    """Call event without additional validation.

    This function triggers the event without any additional validation. It should be
    used when all additional actions are already handled. Additional actions like
    triggering all existing sync webhooks before calling async webhooks.
    """
    connection = transaction.get_connection()
    if connection.in_atomic_block:
        transaction.on_commit(lambda: func_obj(*func_args, **func_kwargs))
    else:
        func_obj(*func_args, **func_kwargs)


def call_event(func_obj, *func_args, **func_kwargs):
    """Call webhook event with given args.

    Ensures that in atomic transaction event is called on_commit.
    """
    is_protected_instance = any(
        isinstance(arg, (Checkout, CheckoutInfo, Order, OrderInfo)) for arg in func_args
    )
    func_obj_self = getattr(func_obj, "__self__", None)
    is_plugin_manager_method = "PluginsManager" in str(
        getattr(func_obj_self, "__class__", "")
    )
    if is_protected_instance and is_plugin_manager_method:
        raise NotImplementedError("`call_event` doesn't support checkout/order events.")
    call_event_including_protected_events(func_obj, *func_args, **func_kwargs)

from django.db import transaction

from ...checkout.fetch import CheckoutInfo
from ...checkout.models import Checkout
from ...order.fetch import OrderInfo
from ...order.models import Order
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.models import Webhook


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
    is_async_event = event_name in WebhookEventAsyncType.ALL
    if not is_async_event:
        raise ValueError(f"Event {event_name} is not an async event.")

    if event_name not in webhook_event_map:
        raise ValueError(f"Event {event_name} not found in webhook_event_map.")

    missing_possible_sync_events_in_map = set(possible_sync_events).difference(
        webhook_event_map.keys()
    )
    if missing_possible_sync_events_in_map:
        raise ValueError(
            f"Event {missing_possible_sync_events_in_map} not found in webhook_event_map."
        )

    if not webhook_event_map[event_name] and not webhook_event_map.get(
        WebhookEventAsyncType.ANY
    ):
        return False

    active_webhook_events = set(
        [event for event, webhooks in webhook_event_map.items() if webhooks]
    )
    if not active_webhook_events.intersection(possible_sync_events):
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
        [
            isinstance(arg, (Checkout, CheckoutInfo, Order, OrderInfo))
            for arg in func_args
        ]
    )
    func_obj_self = getattr(func_obj, "__self__", None)
    is_plugin_manager_method = "PluginsManager" in str(
        getattr(func_obj_self, "__class__", "")
    )
    if is_protected_instance and is_plugin_manager_method:
        raise NotImplementedError("`call_event` doesn't support checkout/order events.")
    call_event_including_protected_events(func_obj, *func_args, **func_kwargs)

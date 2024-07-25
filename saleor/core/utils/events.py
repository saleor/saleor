from django.db import transaction

from ...checkout.fetch import CheckoutInfo
from ...checkout.models import Checkout


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
    is_checkout_instance = any(
        [isinstance(arg, (Checkout, CheckoutInfo)) for arg in func_args]
    )

    if is_checkout_instance:
        raise NotImplementedError("`call_event` doesn't support checkout/order events.")
    call_event_including_protected_events(func_obj, *func_args, **func_kwargs)

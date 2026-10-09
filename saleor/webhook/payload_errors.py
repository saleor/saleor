import logging

import graphene
from django.core.cache import cache
from django.db.transaction import on_commit
from redis import RedisError

from ..app.tasks import create_app_problem_task
from .const import (
    WEBHOOK_PAYLOAD_ERROR_PROBLEM_AGGREGATION_PERIOD,
    WEBHOOK_PAYLOAD_ERROR_PROBLEM_TTL,
    WebhookPayloadErrorReason,
)
from .models import Webhook
from .transport.metrics import record_webhook_payload_error

logger = logging.getLogger(__name__)

INVALID_SUBSCRIPTION_QUERY_PROBLEM_KEY_PREFIX = "invalid-subscription-query"


def get_app_global_id(app_pk: int) -> str:
    """Identify an app the way a customer addresses it: by global (GraphQL) id."""
    return graphene.Node.to_global_id("App", app_pk)


def get_webhook_global_id(webhook_pk: int) -> str:
    """Identify a webhook the way a customer addresses it: by global (GraphQL) id."""
    return graphene.Node.to_global_id("Webhook", webhook_pk)


def get_invalid_subscription_query_problem_key(webhook_pk: int) -> str:
    """Build the app problem key identifying one webhook's broken subscription query."""
    return f"{INVALID_SUBSCRIPTION_QUERY_PROBLEM_KEY_PREFIX}:{webhook_pk}"


def _describe_webhook(webhook: Webhook) -> str:
    """Describe a webhook for a human reading the problem on the dashboard.

    Both name and identifier are optional, so fall back to the webhook's global id,
    which is what an app or staff member can look the webhook up by.
    """
    if webhook.name and webhook.identifier:
        return f'Webhook "{webhook.name}" (identifier: {webhook.identifier})'
    if webhook.name:
        return f'Webhook "{webhook.name}"'
    if webhook.identifier:
        return f"Webhook with identifier: {webhook.identifier}"
    return f"Webhook {get_webhook_global_id(webhook.pk)}"


def build_invalid_subscription_query_message(
    webhook: Webhook, event_type: str, error: str
) -> str:
    """Explain that a webhook delivers nothing and name the field that broke it.

    The invalid query is a property of the whole subscription document, so every event
    the webhook subscribes to stops being delivered - not only the one being dispatched
    when the failure was noticed.
    """
    return (
        f"{_describe_webhook(webhook)} has an invalid subscription query and is not "
        f"delivering any of its events. Detected while dispatching {event_type}. "
        f"GraphQL error: {error}"
    )


def report_payload_generation_error(
    webhook: Webhook,
    event_type: str,
    reason: WebhookPayloadErrorReason,
    error: str = "",
) -> None:
    """Report an event dropped because its payload could not be generated.

    Always records a metric, as the volume of dropped events is what tells an operator
    how much data was lost. An app problem is raised only for an invalid subscription
    query, where the app is certainly broken and needs to act - an empty payload can be
    the legitimate outcome of a filterable subscription resolving to nothing.
    """
    record_webhook_payload_error(
        app_id=get_app_global_id(webhook.app_id),
        webhook_id=get_webhook_global_id(webhook.pk),
        event_type=event_type,
        reason=reason,
    )

    if reason != WebhookPayloadErrorReason.INVALID_SUBSCRIPTION_QUERY:
        return

    if not _open_problem_reporting_window(webhook.pk):
        return

    key = get_invalid_subscription_query_problem_key(webhook.pk)
    message = build_invalid_subscription_query_message(webhook, event_type, error)
    app_id = webhook.app_id
    on_commit(
        lambda: create_app_problem_task.delay(
            app_id,
            key,
            message,
            # The webhook is already dropping events, so the first report is critical.
            critical_threshold=1,
            aggregation_period=WEBHOOK_PAYLOAD_ERROR_PROBLEM_AGGREGATION_PERIOD,
        )
    )


def _open_problem_reporting_window(webhook_pk: int) -> bool:
    """Claim the reporting window for a webhook, returning False if already claimed.

    A broken webhook fails on every event it is subscribed to, so the problem must be
    written at most once per window instead of once per dropped event. ``cache.add`` is
    a single atomic ``SET NX EX``, which keeps the claim correct across pods.
    """
    try:
        return bool(
            cache.add(
                f"webhook-subscription-error:{webhook_pk}",
                1,
                WEBHOOK_PAYLOAD_ERROR_PROBLEM_TTL,
            )
        )
    except RedisError:
        # Without the cache there is no way to throttle, and writing a problem per
        # dropped event would overwhelm the database. The metric still records the drop.
        logger.warning(
            "Cannot report invalid subscription query for webhook %s, cache unavailable.",
            webhook_pk,
        )
        return False

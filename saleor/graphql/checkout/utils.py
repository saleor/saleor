import graphene
from django.conf import settings
from django.core.exceptions import ValidationError

from ...channel.models import Channel
from ...checkout.models import Checkout
from ...core.exceptions import CircularSubscriptionSyncEvent
from ...webhook.event_types import WebhookEventSyncType


def prepare_insufficient_stock_checkout_validation_error(exc):
    variants = [str(item.variant) for item in exc.items]
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", item.variant.pk)
        for item in exc.items
    ]
    return ValidationError(
        f"Insufficient product stock: {', '.join(variants)}",
        code=exc.code.value,
        params={"variants": variant_ids},
    )


def prevent_sync_event_circular_query(func):
    """Prevent circular dependencies in synchronous events resolvers.

    Synchronous events are not allowed to request fields that are resolved using other
    synchronous events, which would lead to circular calls of the webhook.
    Using this decorator prevents such circular events resolution.

    :raises CircularSubscriptionSyncEvent: When a field being resolved from a
    synchronous webhook's payload uses another synchronous webhook internally.
    """

    def wrapper(*args, **kwargs):
        info = next(arg for arg in args if isinstance(arg, graphene.ResolveInfo))
        sync_event = getattr(info.context, "sync_event", False)
        event_type = getattr(info.context, "event_type", None)
        event_allowed = (
            event_type and event_type in WebhookEventSyncType.ALLOWED_IN_CIRCULAR_QUERY
        )

        if sync_event and not event_allowed:
            raise CircularSubscriptionSyncEvent(
                "Resolving this field is not allowed in synchronous events."
            )
        return func(*args, **kwargs)

    return wrapper


def use_gift_card_transactions_flow(
    channel: "Channel",
    checkout: "Checkout",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Check whether gift card transactions flow should be used.

    Despite channel having the flag enabled there is still a possibility where checkout can
    have an active payment. Mixing payments and transaction is not allowed therefore in
    this case the new flow is not applied.
    """
    return (
        channel.create_transactions_for_gift_cards
        and checkout.get_last_active_payment(database_connection_name) is None
    )

import graphene
from django.core.exceptions import ValidationError

from ...core.exceptions import CircularSubscriptionSyncEvent


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
        if getattr(info.context, "sync_event", False):
            raise CircularSubscriptionSyncEvent(
                "Resolving this field is not allowed in synchronous events."
            )
        return func(*args, **kwargs)

    return wrapper

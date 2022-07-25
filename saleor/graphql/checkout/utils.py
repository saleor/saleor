import graphene
from django.core.exceptions import ValidationError
from graphql import ResolveInfo

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
    """Prevent from resolving field in a synchronous event.

    Synchronous events are not allowed to request fields that are resolved using
    synchronous events. This prevents circular events call.
    """

    def wrapper(*args, **kwargs):
        info = next(arg for arg in args if isinstance(arg, ResolveInfo))
        if getattr(info.context, "sync_event", False):
            raise CircularSubscriptionSyncEvent(
                "Resolving this field is not allowed in synchronous events."
            )
        return func(*args, **kwargs)

    return wrapper

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
    def wrapper(*args, **kwargs):
        info = next(arg for arg in args if isinstance(arg, ResolveInfo))
        if hasattr(info.context, "sync_event") and info.context.sync_event:
            raise CircularSubscriptionSyncEvent(
                "Resolving this field is not allowed in synchronous events."
            )
        return func(*args, **kwargs)

    return wrapper

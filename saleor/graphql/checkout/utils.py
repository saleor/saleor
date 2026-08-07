import graphene
from django.core.exceptions import ValidationError

from ...core.exceptions import CircularSubscriptionSyncEvent, InsufficientStockData
from ...webhook.event_types import WebhookEventSyncType


def get_insufficient_stock_checkout_error_params(
    item: InsufficientStockData, existing_lines=None
) -> dict:
    """Build CheckoutError params for an insufficient-stock item.

    Always includes the variant GraphQL ID when available. Includes checkout line
    IDs when the stock error is tied to an existing checkout line.
    """
    params: dict = {}
    if item.variant and item.variant.pk is not None:
        params["variants"] = [
            graphene.Node.to_global_id("ProductVariant", item.variant.pk)
        ]

    checkout_line = item.checkout_line
    if checkout_line is None and existing_lines and item.variant:
        for line_info in existing_lines:
            if line_info.variant.pk == item.variant.pk:
                checkout_line = line_info.line
                break

    if checkout_line is not None and checkout_line.pk is not None:
        params["lines"] = [
            graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)
        ]
    return params


def prepare_insufficient_stock_checkout_validation_error(exc):
    variants = [str(item.variant) for item in exc.items]
    variant_ids = []
    line_ids = []
    for item in exc.items:
        params = get_insufficient_stock_checkout_error_params(item)
        variant_ids.extend(params.get("variants", []))
        line_ids.extend(params.get("lines", []))
    error_params: dict = {}
    if variant_ids:
        error_params["variants"] = variant_ids
    if line_ids:
        error_params["lines"] = line_ids
    return ValidationError(
        f"Insufficient product stock: {', '.join(variants)}",
        code=exc.code.value,
        params=error_params,
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

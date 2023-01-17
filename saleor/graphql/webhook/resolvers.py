from ...checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    get_all_shipping_methods_list,
)
from ...core.exceptions import PermissionDenied
from ...core.permissions import AppPermission
from ...webhook import models, payloads
from ...webhook.deprecated_event_types import WebhookEventType
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..core.tracing import traced_resolver
from ..core.utils import from_global_id_or_error
from ..discount.dataloaders import load_discounts
from .types import Webhook, WebhookEvent


def resolve_webhook(info, id, app):
    _, id = from_global_id_or_error(id, Webhook)
    if app:
        return app.webhooks.filter(id=id).first()
    user = info.context.user
    if user.has_perm(AppPermission.MANAGE_APPS):
        return models.Webhook.objects.filter(pk=id).first()
    raise PermissionDenied(permissions=[AppPermission.MANAGE_APPS])


def resolve_webhook_events():
    return [
        WebhookEvent(event_type=event_type[0])
        for event_type in WebhookEventType.CHOICES
    ]


@traced_resolver
def resolve_sample_payload(info, event_name, app):
    user = info.context.user
    required_permission = WebhookEventAsyncType.PERMISSIONS.get(
        event_name, WebhookEventSyncType.PERMISSIONS.get(event_name)
    )
    if not required_permission:
        return payloads.generate_sample_payload(event_name)
    else:
        if app and app.has_perm(required_permission):
            return payloads.generate_sample_payload(event_name)
        if user and user.has_perm(required_permission):
            return payloads.generate_sample_payload(event_name)
        raise PermissionDenied(permissions=[required_permission])


def resolve_shipping_methods_for_checkout(info, checkout, manager):
    discounts = load_discounts(info.context)
    lines, _ = fetch_checkout_lines(checkout)
    shipping_channel_listings = checkout.channel.shipping_method_listings.all()
    checkout_info = fetch_checkout_info(
        checkout,
        lines,
        discounts,
        manager,
        shipping_channel_listings,
        fetch_delivery_methods=False,
    )
    all_shipping_methods = get_all_shipping_methods_list(
        checkout_info,
        checkout.shipping_address,
        lines,
        discounts,
        shipping_channel_listings,
        manager,
    )
    return all_shipping_methods

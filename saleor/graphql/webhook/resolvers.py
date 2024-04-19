from django.conf import settings
from django.db.models import Exists, OuterRef, Q

from ...app.models import App
from ...checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    get_all_shipping_methods_list,
)
from ...core.exceptions import PermissionDenied
from ...permission.enums import AppPermission
from ...webhook import models, payloads
from ...webhook.deprecated_event_types import WebhookEventType
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..core.tracing import traced_resolver
from ..core.utils import from_global_id_or_error
from .types import Webhook, WebhookEvent


def resolve_webhook(info: ResolveInfo, id, app):
    _, id = from_global_id_or_error(id, Webhook)
    if app:
        return app.webhooks.filter(id=id).first()
    user = info.context.user
    database_connection_name = get_database_connection_name(info.context)
    if user and user.has_perm(AppPermission.MANAGE_APPS):
        apps = (
            App.objects.using(database_connection_name)
            .filter(removed_at__isnull=True)
            .values("pk")
        )
        return (
            models.Webhook.objects.using(database_connection_name)
            .filter(Q(pk=id), Exists(apps.filter(id=OuterRef("app_id"))))
            .first()
        )
    raise PermissionDenied(permissions=[AppPermission.MANAGE_APPS])


def resolve_webhook_events():
    return [
        WebhookEvent(event_type=event_type[0])
        for event_type in WebhookEventType.CHOICES
    ]


@traced_resolver
def resolve_sample_payload(info: ResolveInfo, event_name, app):
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


def resolve_shipping_methods_for_checkout(
    info: ResolveInfo,
    checkout,
    manager,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    lines, _ = fetch_checkout_lines(checkout)
    shipping_channel_listings = checkout.channel.shipping_method_listings.all()
    checkout_info = fetch_checkout_info(
        checkout,
        lines,
        manager,
        shipping_channel_listings,
        database_connection_name=database_connection_name,
    )
    all_shipping_methods = get_all_shipping_methods_list(
        checkout_info,
        checkout.shipping_address,
        lines,
        shipping_channel_listings,
        manager,
        database_connection_name=database_connection_name,
    )
    return all_shipping_methods

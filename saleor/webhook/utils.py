from collections import defaultdict
from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef

from ..app.models import App
from .event_types import WebhookEventAsyncType, WebhookEventSyncType
from .models import Webhook, WebhookEvent

if TYPE_CHECKING:
    from django.db.models import QuerySet


def get_filter_for_single_webhook_event(
    event_type: str,
    apps_ids: Optional["list[int]"] = None,
    apps_identifier: Optional[list[str]] = None,
):
    permissions = {}
    required_permission = WebhookEventAsyncType.PERMISSIONS.get(
        event_type, WebhookEventSyncType.PERMISSIONS.get(event_type)
    )
    if required_permission:
        app_label, codename = required_permission.value.split(".")
        permissions["permissions__content_type__app_label"] = app_label
        permissions["permissions__codename"] = codename

    # In this function we use the replica database for all queryset reads, as there is
    # no risk that any mutation would change the result of these querysets.

    app_kwargs: dict = {"is_active": True, **permissions}
    if event_type != WebhookEventAsyncType.APP_DELETED:
        app_kwargs["removed_at__isnull"] = True
    if apps_ids:
        app_kwargs["id__in"] = apps_ids
    if apps_identifier:
        app_kwargs["identifier__in"] = apps_identifier

    apps = App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).filter(
        **app_kwargs
    )
    event_types = [event_type]
    if event_type in WebhookEventAsyncType.ALL:
        event_types.append(WebhookEventAsyncType.ANY)

    webhook_events = WebhookEvent.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(event_type__in=event_types)
    return (
        Q(is_active=True)
        & Q(Exists(apps.filter(id=OuterRef("app_id"))))
        & Q(Exists(webhook_events.filter(webhook_id=OuterRef("id"))))
    )


def get_webhooks_for_event(
    event_type: str,
    webhooks: Optional["QuerySet[Webhook]"] = None,
    apps_ids: Optional["list[int]"] = None,
    apps_identifier: Optional[list[str]] = None,
) -> "QuerySet[Webhook]":
    """Get active webhooks from the database for an event."""

    if webhooks is None:
        # For this QS replica usage is applied later, as this QS could be also passed
        # as parameter.
        webhooks = Webhook.objects.all()

    filters = get_filter_for_single_webhook_event(
        event_type=event_type, apps_ids=apps_ids, apps_identifier=apps_identifier
    )

    return (
        webhooks.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(filters)
        .select_related("app")
        .prefetch_related("app__permissions__content_type")
    )


def get_webhooks_for_multiple_events(
    event_types: Iterable[str],
) -> dict[str, set[Webhook]]:
    set_event_types = set(event_types)
    if set_event_types.intersection(WebhookEventAsyncType.ALL):
        set_event_types.add(WebhookEventAsyncType.ANY)

    webhook_id_to_event_type = (
        WebhookEvent.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(event_type__in=set_event_types)
        .values_list("webhook_id", "event_type")
    )
    webhook_id_to_event_types_map = defaultdict(set)
    for webhook_id, event_type in webhook_id_to_event_type:
        webhook_id_to_event_types_map[webhook_id].add(event_type)

    webhooks = Webhook.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).filter(
        id__in={webhook_id for webhook_id, _ in webhook_id_to_event_type},
        is_active=True,
    )
    app_ids = {webhook.app_id for webhook in webhooks}

    apps = (
        App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(id__in=app_ids, is_active=True, removed_at__isnull=True)
        .prefetch_related("permissions__content_type")
        .in_bulk()
    )

    app_perm_map = {}
    for app in apps.values():
        app_perms = app.permissions.all()
        app_permission_codenames = [
            (permission.content_type.app_label, permission.codename)
            for permission in app_perms
        ]
        app_perm_map[app.id] = app_permission_codenames
    active_event_map = defaultdict(set)
    for webhook in webhooks:
        if webhook.app_id not in apps:
            continue
        app = apps[webhook.app_id]
        webhook.app = app
        app_permissions = app_perm_map.get(webhook.app_id, [])
        events = webhook_id_to_event_types_map.get(webhook.id, set())
        for event in events:
            required_permission = WebhookEventAsyncType.PERMISSIONS.get(
                event, WebhookEventSyncType.PERMISSIONS.get(event)
            )
            if not required_permission:
                active_event_map[event].add(webhook)
            else:
                app_label, codename = required_permission.value.split(".")
                if (app_label, codename) in app_permissions:
                    active_event_map[event].add(webhook)
    # always add events that don't have any active webhooks. This is needed for
    # future validation when calling events.
    for event in set_event_types:
        if event not in active_event_map:
            active_event_map[event] = set()
    return active_event_map

from django.conf import settings
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef

from ..permission.enums import CheckoutPermissions
from ..permission.models import Permission
from ..webhook.event_types import WebhookEventSyncType
from ..webhook.models import Webhook, WebhookEvent
from .models import App


def get_active_tax_apps():
    _, codename = CheckoutPermissions.HANDLE_TAXES.value.split(".")

    permissions = Permission.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(codename=codename, app=OuterRef("pk"))

    order_taxes_event = WebhookEvent.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(
        event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES, webhook_id=OuterRef("pk")
    )

    checkout_taxes_event = WebhookEvent.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        webhook_id=OuterRef("pk"),
    )

    webhook_order_taxes_event = Webhook.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(Q(app_id=OuterRef("pk")) & Q(Exists(order_taxes_event)))

    webhook_checkout_taxes_event = Webhook.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(Q(app_id=OuterRef("pk")) & Q(Exists(checkout_taxes_event)))

    return App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).filter(
        Q(is_active=True)
        & Q(Exists(webhook_order_taxes_event))
        & Q(Exists(webhook_checkout_taxes_event))
        & Q(Exists(permissions))
    )

from django.db.models import Exists, OuterRef

from .. import settings
from ..app.models import App
from ..celeryconf import app
from ..core import EventDeliveryStatus
from ..core.models import EventDelivery
from .models import Webhook
from .transport.asynchronous.transport import send_webhooks_async_for_app


@app.task
def process_async_webhooks_task():
    app_ids = get_app_ids_with_pending_deliveries()
    for app_id in app_ids:
        send_webhooks_async_for_app.apply_async(
            kwargs={"app_id": app_id},
            bind=True,
        )


def get_app_ids_with_pending_deliveries() -> list[int]:
    app_ids = (
        Webhook.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(
            Exists(
                EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).filter(
                    webhook_id=OuterRef("pk")
                )
            )
        )
        .filter(
            Exists(App.objects.filter(is_active=True).filter(id=OuterRef("app_id")))
        )
        .values_list("app_id", flat=True)
        .distinct()
    )
    return list(app_ids)

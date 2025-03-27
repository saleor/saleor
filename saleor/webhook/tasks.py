from .. import settings
from ..celeryconf import app
from ..core import EventDeliveryStatus
from ..core.models import EventDelivery
from .transport.asynchronous.transport import send_webhooks_async_for_app


@app.task
def process_async_webhooks_task():
    app_ids = get_app_ids_with_pending_deliveries()
    for app_id in app_ids:
        send_webhooks_async_for_app(app_id=app_id)


def get_app_ids_with_pending_deliveries() -> list[int]:
    app_ids = (
        EventDelivery.objects.select_related("webhook")
        .using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(status=EventDeliveryStatus.PENDING)
        .values_list("webhook__app_id", flat=True)
        .distinct()
    )
    return list(app_ids)

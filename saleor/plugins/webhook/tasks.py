import logging

from celery.utils.log import get_task_logger
from django.conf import settings

from ...celeryconf import app

logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)


# all tasks to be removed in 3.18.
# tasks moved to different direction.


@app.task(
    queue=settings.WEBHOOK_CELERY_QUEUE_NAME,
    bind=True,
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
)
def send_webhook_request_async(self, event_delivery_id):
    from ...webhook.transport.asynchronous.transport import send_webhook_request_async

    send_webhook_request_async(self, event_delivery_id)


@app.task
def observability_send_events():
    from ...webhook.transport.asynchronous.transport import observability_send_events

    observability_send_events()


@app.task
def observability_reporter_task():
    from ...webhook.transport.asynchronous.transport import observability_reporter_task

    observability_reporter_task()


@app.task(
    bind=True,
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
)
def handle_transaction_request_task(self, delivery_id, request_event_id):
    from ...webhook.transport.synchronous.transport import (
        handle_transaction_request_task,
    )

    handle_transaction_request_task(self, delivery_id, request_event_id)

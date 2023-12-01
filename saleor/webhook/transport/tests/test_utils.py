import datetime

import pytest
from celery import Task
from celery.exceptions import Retry
from celery.utils.threads import LocalStack

from ....core import EventDeliveryStatus
from ....core.models import EventDeliveryAttempt
from ..utils import WebhookResponse, handle_webhook_retry


class DummyTask(Task):
    retry_backoff = 10
    retry_kwargs = {"max_retries": 2}
    request_stack = LocalStack()


def test_webhook_retry(webhook, event_delivery):
    # given
    attempt = EventDeliveryAttempt(
        id=1,
        created_at=datetime.datetime.utcnow(),
        delivery=event_delivery,
        request_headers="",
        task_id="123",
    )
    task = DummyTask()
    # when
    task.push_request(retries=1)
    response = WebhookResponse(
        content="Error!", response_status_code=500, status=EventDeliveryStatus.FAILED
    )
    # then
    with pytest.raises(Retry):
        handle_webhook_retry(task, webhook, response, event_delivery, attempt)


def test_webhook_retry_404(webhook, event_delivery):
    # given
    attempt = EventDeliveryAttempt(
        id=1,
        created_at=datetime.datetime.utcnow(),
        delivery=event_delivery,
        request_headers="",
        task_id="123",
    )
    task = DummyTask()
    # when
    task.push_request(retries=1)
    response = WebhookResponse(
        content="Error!", response_status_code=404, status=EventDeliveryStatus.FAILED
    )
    # then
    retry = handle_webhook_retry(task, webhook, response, event_delivery, attempt)
    assert retry is False


def test_webhook_retry_redirect(webhook, event_delivery):
    # given
    attempt = EventDeliveryAttempt(
        id=1,
        created_at=datetime.datetime.utcnow(),
        delivery=event_delivery,
        request_headers="",
        task_id="123",
    )
    task = DummyTask()
    # when
    task.push_request(retries=1)
    response = WebhookResponse(
        content="Error!", response_status_code=302, status=EventDeliveryStatus.FAILED
    )
    # then
    retry = handle_webhook_retry(task, webhook, response, event_delivery, attempt)
    assert retry is False

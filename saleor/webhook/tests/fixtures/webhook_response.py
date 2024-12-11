import pytest

from ....core import EventDeliveryStatus
from ....webhook.transport.utils import WebhookResponse


@pytest.fixture
def webhook_response():
    return WebhookResponse(
        content="test_content",
        request_headers={"headers": "test_request"},
        response_headers={"headers": "test_response"},
        response_status_code=200,
        duration=2.0,
        status=EventDeliveryStatus.SUCCESS,
    )


@pytest.fixture
def webhook_response_failed():
    return WebhookResponse(
        content="example_content_response",
        request_headers={"headers": "test_request"},
        response_headers={"headers": "test_response"},
        response_status_code=500,
        duration=2.0,
        status=EventDeliveryStatus.FAILED,
    )

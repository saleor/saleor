import functools

from .buffers import get_buffer
from .exceptions import ObservabilityError
from .payloads import dump_payload
from .utils import (
    WebhookData,
    get_buffer_name,
    get_observability_webhooks,
    report_api_call,
    report_gql_operation,
    report_webhook_event_delivery,
    task_next_retry_date,
)

__all__ = [
    "get_buffer",
    "ObservabilityError",
    "dump_payload",
    "WebhookData",
    "get_buffer_name",
    "get_observability_webhooks",
    "report_api_call",
    "report_gql_operation",
    "report_webhook_event_delivery",
    "task_next_retry_date",
]


def dispatch_decorator(method):
    @functools.wraps(method)
    def wrapper(self, request, *args, **kwargs):
        with report_api_call(request) as api_call:
            response = method(self, request, *args, **kwargs)
            api_call.response = response
            return response

    return wrapper

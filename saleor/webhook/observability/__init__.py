import functools

from .buffers import get_buffer
from .utils import get_observability_webhooks, report_api_call, report_gql_operation

__all__ = [
    "report_api_call",
    "report_gql_operation",
    "dispatch_decorator",
    "get_buffer",
    "get_observability_webhooks",
]


def dispatch_decorator(method):
    @functools.wraps(method)
    def wrapper(self, request, *args, **kwargs):
        with report_api_call(request) as api_call:
            response = method(self, request, *args, **kwargs)
            api_call.response = response
            return response

    return wrapper

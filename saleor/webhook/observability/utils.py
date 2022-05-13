import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    TypedDict,
)

import opentracing
import opentracing.tags
from asgiref.local import Local
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.utils import timezone
from graphql import GraphQLDocument
from pytimeparse import parse

from ..event_types import WebhookEventAsyncType
from ..utils import get_webhooks_for_event
from .buffers import get_buffer
from .exceptions import ObservabilityError
from .payloads import generate_api_call_payload, generate_event_delivery_attempt_payload

if TYPE_CHECKING:

    from celery.exceptions import Retry
    from django.http import HttpRequest, HttpResponse

    from ...core.models import EventDeliveryAttempt

logger = logging.getLogger(__name__)
OBSERVABILITY_EVENT_TYPE = WebhookEventAsyncType.OBSERVABILITY
WEBHOOKS_CACHE_TIMEOUT = parse("5 minutes")
BUFFER_KEY = "observability_buffer"
WEBHOOKS_KEY = "observability_webhooks"
_IS_ACTIVE_CACHE: Dict[str, Tuple[bool, float]] = {}
_context = Local()


class WebhookData(TypedDict):
    saleor_domain: str
    target_url: str
    secret_key: Optional[str]


def get_buffer_name() -> str:
    return cache.make_key(BUFFER_KEY)


def get_observability_webhooks() -> List[WebhookData]:
    webhooks_data = cache.get(WEBHOOKS_KEY)
    if webhooks_data is None:
        webhooks_data = []
        if webhooks := get_webhooks_for_event(OBSERVABILITY_EVENT_TYPE):
            domain = Site.objects.get_current().domain
            for webhook in webhooks:
                webhooks_data.append(
                    WebhookData(
                        saleor_domain=domain,
                        target_url=webhook.target_url,
                        secret_key=webhook.secret_key,
                    )
                )
        cache.set(WEBHOOKS_KEY, webhooks_data, timeout=WEBHOOKS_CACHE_TIMEOUT)
    return webhooks_data


def is_observability_active(timeout=WEBHOOKS_CACHE_TIMEOUT) -> bool:
    key = get_buffer_name()
    if (cached := _IS_ACTIVE_CACHE.get(key, None)) is not None:
        is_active, check_time = cached
        if time.monotonic() - check_time <= timeout:
            return is_active
    is_active = bool(get_observability_webhooks())
    _IS_ACTIVE_CACHE[key] = (is_active, time.monotonic())
    return is_active


def task_next_retry_date(retry_error: "Retry") -> Optional[datetime]:
    if isinstance(retry_error.when, (int, float)):
        return timezone.now() + timedelta(seconds=retry_error.when)
    if isinstance(retry_error.when, datetime):
        return retry_error.when
    return None


def put_to_buffer(event_payload: Callable[[], str], sync=True):
    if not sync:
        raise NotImplementedError(
            "[Observability] Async upload to buffer not implemented"
        )
    try:
        payload = event_payload()
        get_buffer().put_event(get_buffer_name(), payload)
    except ObservabilityError:
        logger.error("[Observability] Event dropped", exc_info=True)


@dataclass
class GraphQLOperationResponse:
    name: Optional[str] = None
    query: Optional[GraphQLDocument] = None
    variables: Optional[Dict] = None
    result: Optional[Dict] = None
    result_invalid: bool = False


class ApiCallContext:
    def __init__(self, request: "HttpRequest"):
        self.gql_operations: List[GraphQLOperationResponse] = []
        self.response: Optional["HttpResponse"] = None
        self._reported = False
        self.request = request

    def report(self):
        if (
            self._reported
            or not settings.OBSERVABILITY_ACTIVE
            or (
                not getattr(self.request, "app", None)
                and not settings.OBSERVABILITY_REPORT_ALL_API_CALLS
            )
        ):
            return
        self._reported = True
        tracer = opentracing.global_tracer()
        with tracer.start_active_span("observability_report_api_call") as scope:
            scope.span.set_tag(opentracing.tags.COMPONENT, "observability")
            if self.response is None:
                logger.error("[Observability] HttpResponse not provided, event dropped")
                return
            if is_observability_active():
                put_to_buffer(
                    partial(
                        generate_api_call_payload,
                        self.request,
                        self.response,
                        self.gql_operations,
                        settings.OBSERVABILITY_MAX_PAYLOAD_SIZE,
                    )
                )


@contextmanager
def report_api_call(request: "HttpRequest") -> Generator[ApiCallContext, None, None]:
    root = False
    if not hasattr(_context, "api_call"):
        _context.api_call, root = ApiCallContext(request), True
    yield _context.api_call
    if root:
        _context.api_call.report()
        del _context.api_call


@contextmanager
def report_gql_operation() -> Generator[GraphQLOperationResponse, None, None]:
    root = False
    if not hasattr(_context, "gql_operation"):
        _context.gql_operation, root = GraphQLOperationResponse(), True
    yield _context.gql_operation
    if root:
        if hasattr(_context, "api_call"):
            _context.api_call.gql_operations.append(_context.gql_operation)
        del _context.gql_operation


def report_webhook_event_delivery(
    attempt: "EventDeliveryAttempt", next_retry: Optional["datetime"] = None
):
    if not settings.OBSERVABILITY_ACTIVE:
        return
    tracer = opentracing.global_tracer()
    with tracer.start_active_span(
        "observability_report_event_delivery_attempt"
    ) as scope:
        scope.span.set_tag(opentracing.tags.COMPONENT, "observability")
        if is_observability_active():
            if attempt.delivery is None:
                logger.error(
                    "[Observability] Event delivery not assigned to attempt: %r. "
                    "Event dropped",
                    attempt,
                )
                return
            put_to_buffer(
                partial(
                    generate_event_delivery_attempt_payload,
                    attempt,
                    next_retry,
                    settings.OBSERVABILITY_MAX_PAYLOAD_SIZE,
                )
            )

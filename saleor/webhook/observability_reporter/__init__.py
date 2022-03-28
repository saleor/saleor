import logging
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Generator, List, Optional

import opentracing
import opentracing.tags
from django.conf import settings
from graphql import GraphQLDocument

from ...webhook.event_types import WebhookEventAsyncType
from .buffer import put_event
from .exceptions import ObservabilityError
from .payloads import generate_api_call_payload, generate_event_delivery_attempt_payload
from .utils import webhooks_for_event_exists

if TYPE_CHECKING:
    from datetime import datetime

    from django.http import HttpRequest, HttpResponse

    from ...core.models import EventDeliveryAttempt

logger = logging.getLogger(__name__)


@dataclass
class GraphQLOperationResponse:
    name: Optional[str] = None
    query: Optional[GraphQLDocument] = None
    variables: Optional[Dict] = None
    result: Optional[Dict] = None
    status_code: int = 200


class ApiCallResponse:
    def __init__(self, request: "HttpRequest"):
        self.request = request
        self.gql_operations: List[GraphQLOperationResponse] = []
        self.response: Optional["HttpResponse"] = None
        self._reported = False

    def report(self) -> bool:
        if self._reported or not settings.OBSERVABILITY_ACTIVE:
            return False
        self._reported = True
        if (
            not getattr(self.request, "app", None)
            and not settings.OBSERVABILITY_REPORT_ALL_API_CALLS
        ):
            return False
        tracer = opentracing.global_tracer()
        with tracer.start_active_span("observability_report_api_call") as scope:
            scope.span.set_tag(opentracing.tags.COMPONENT, "observability")
            if self.response is None:
                logger.info("[Observability] HttpResponse not provided")
                return False
            event_type = WebhookEventAsyncType.OBSERVABILITY
            if webhooks_for_event_exists(event_type):
                try:
                    event = generate_api_call_payload(
                        self.request,
                        self.response,
                        self.gql_operations,
                        settings.OBSERVABILITY_MAX_PAYLOAD_SIZE,
                    )
                    put_event(event)
                except (ValueError, ObservabilityError):
                    logger.info("[Observability] Api call event skipped", exc_info=True)
                    return False
                except Exception:  # pylint: disable=broad-except
                    logger.warning(
                        "[Observability] Api call event skipped", exc_info=True
                    )
                    return False
        return True


def report_event_delivery_attempt(
    attempt: "EventDeliveryAttempt", next_retry: Optional["datetime"] = None
) -> bool:
    if attempt.delivery is None:
        logger.error("Event delivery not assigned to attempt: %r", attempt)
        return False
    tracer = opentracing.global_tracer()
    with tracer.start_active_span(
        "observability_report_event_delivery_attempt"
    ) as scope:
        scope.span.set_tag(opentracing.tags.COMPONENT, "observability")
        event_type = WebhookEventAsyncType.OBSERVABILITY
        if webhooks_for_event_exists(event_type):
            try:
                event = generate_event_delivery_attempt_payload(
                    attempt, next_retry, settings.OBSERVABILITY_MAX_PAYLOAD_SIZE
                )
                put_event(event)
            except (ValueError, ObservabilityError):
                msg = "[Observability] Event delivery attempt skipped"
                logger.info(msg, exc_info=True)
                return False
            except Exception:  # pylint: disable=broad-except
                msg = "[Observability] Event delivery attempt skipped"
                logger.warning(msg, exc_info=True)
                return False
    return True


_API_CALL_CONTEXT: ContextVar[Optional[ApiCallResponse]] = ContextVar(
    "api_call_context", default=None
)
_GQL_OPERATION_CONTEXT: ContextVar[Optional[GraphQLOperationResponse]] = ContextVar(
    "gql_operation_context", default=None
)


@contextmanager
def api_call_context(request: "HttpRequest") -> Generator[ApiCallResponse, None, None]:
    context, root = _API_CALL_CONTEXT.get(), False
    if context is None:
        context, root = ApiCallResponse(request=request), True
        _API_CALL_CONTEXT.set(context)
    yield context
    if root:
        _API_CALL_CONTEXT.set(None)
        context.report()


@contextmanager
def gql_operation_context() -> Generator[GraphQLOperationResponse, None, None]:
    context, root = _GQL_OPERATION_CONTEXT.get(), False
    if context is None:
        context, root = GraphQLOperationResponse(), True
        _GQL_OPERATION_CONTEXT.set(context)
    yield context
    if root:
        _GQL_OPERATION_CONTEXT.set(None)
        if api_call := _API_CALL_CONTEXT.get():
            api_call.gql_operations.append(context)

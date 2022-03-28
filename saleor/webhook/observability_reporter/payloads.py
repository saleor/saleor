import json
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, TypedDict, cast

import graphene
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from graphql import get_operation_ast

from .. import traced_payload_generator
from .utils import CustomJsonEncoder, JsonTruncText, hide_sensitive_headers

if TYPE_CHECKING:
    from ...core.models import EventDeliveryAttempt
    from . import GraphQLOperationResponse


class ObservabilityEventTypes(str, Enum):
    ApiCall = "observability_api_call"
    EventDeliveryAttempt = "observability_event_delivery_attempt"


class ObservabilityEventPayload(TypedDict):
    eventType: ObservabilityEventTypes


class GraphQLOperationPayload(TypedDict):
    name: Optional[JsonTruncText]
    operationType: Optional[str]
    query: Optional[JsonTruncText]
    result: Optional[JsonTruncText]


class RequestPayload(TypedDict):
    id: str
    method: str
    url: str
    time: float
    headers: Dict[str, str]
    contentLength: int


class ResponsePayload(TypedDict):
    headers: Dict[str, str]
    statusCode: int
    reasonPhrase: str
    contentLength: int


class AppPayload(TypedDict):
    id: str
    name: str


class GraphQLOperationsPayload(TypedDict):
    count: int
    operations: List[GraphQLOperationPayload]


class ApiCallPayload(ObservabilityEventPayload):
    request: RequestPayload
    response: ResponsePayload
    app: Optional[AppPayload]
    gql_operations: GraphQLOperationsPayload


class EventDeliveryDataPayload(TypedDict):
    contentLength: int
    body: JsonTruncText


class EventDeliveryPayload(TypedDict):
    id: str
    status: str
    eventType: str
    payload: EventDeliveryDataPayload


class WebhookPayload(TypedDict):
    id: str
    name: str
    targetUrl: str


class AttemptPayload(TypedDict):
    id: str
    time: datetime
    duration: Optional[float]
    status: str
    nextRetry: Optional[datetime]


class RequestHeadersPayload(TypedDict):
    headers: Dict[str, str]


class ResponseWithBodyPayload(ResponsePayload):
    body: JsonTruncText


class EventDeliveryAttemptPayload(ObservabilityEventPayload):
    eventDeliveryAttempt: AttemptPayload
    request: RequestHeadersPayload
    response: ResponseWithBodyPayload
    eventDelivery: Optional[EventDeliveryPayload]
    webhook: Optional[WebhookPayload]
    app: Optional[AppPayload]


def _json_serialize(obj: Any, pretty=False):
    if pretty:
        return json.dumps(obj, indent=2, ensure_ascii=True, cls=CustomJsonEncoder)
    return json.dumps(obj, ensure_ascii=True, cls=CustomJsonEncoder)


TRUNC_PLACEHOLDER = JsonTruncText(truncated=False)
EMPTY_TRUNC = JsonTruncText(truncated=True)


GQL_OPERATION_PLACEHOLDER = GraphQLOperationPayload(
    name=TRUNC_PLACEHOLDER,
    operationType="subscription",
    query=TRUNC_PLACEHOLDER,
    result=TRUNC_PLACEHOLDER,
)
GQL_OPERATION_PLACEHOLDER_SIZE = len(_json_serialize(GQL_OPERATION_PLACEHOLDER))


def serialize_gql_operation_result(
    operation: "GraphQLOperationResponse", bytes_limit: int
) -> Tuple[GraphQLOperationPayload, int]:
    bytes_limit -= GQL_OPERATION_PLACEHOLDER_SIZE
    if bytes_limit < 0:
        raise ValueError()
    name: Optional[JsonTruncText] = None
    operation_type: Optional[str] = None
    query: Optional[JsonTruncText] = None
    result: Optional[JsonTruncText] = None
    if operation.name:
        name = JsonTruncText.truncate(operation.name, bytes_limit // 3)
        bytes_limit -= cast(JsonTruncText, name).byte_size
    if operation.query:
        query = JsonTruncText.truncate(
            operation.query.document_string, bytes_limit // 2
        )
        bytes_limit -= cast(JsonTruncText, query).byte_size
        if definition := get_operation_ast(
            operation.query.document_ast, operation.name
        ):
            operation_type = definition.operation
    if operation.result:
        result = JsonTruncText.truncate(
            _json_serialize(operation.result, pretty=True), bytes_limit
        )
        bytes_limit -= cast(JsonTruncText, result).byte_size
    bytes_limit = max(0, bytes_limit)
    return (
        GraphQLOperationPayload(
            name=name,
            operationType=operation_type,
            query=query,
            result=result,
        ),
        bytes_limit,
    )


def serialize_gql_operation_results(
    operations: List["GraphQLOperationResponse"], bytes_limit: int
) -> List[GraphQLOperationPayload]:
    if bytes_limit - len(operations) * GQL_OPERATION_PLACEHOLDER_SIZE < 0:
        raise ValueError()
    payloads: List[GraphQLOperationPayload] = []
    for i, operation in enumerate(operations):
        payload_limit = bytes_limit // (len(operations) - i)
        payload, left_bytes = serialize_gql_operation_result(operation, payload_limit)
        payloads.append(payload)
        bytes_limit -= payload_limit - left_bytes
    return payloads


@traced_payload_generator
def generate_api_call_payload(
    request: HttpRequest,
    response: HttpResponse,
    gql_operations: List["GraphQLOperationResponse"],
    bytes_limit: int,
) -> str:
    request_payload = RequestPayload(
        id=str(uuid.uuid4()),
        method=request.method or "",
        url=request.build_absolute_uri(request.get_full_path()),
        time=getattr(request, "request_time", timezone.now()).timestamp(),
        headers=hide_sensitive_headers(dict(request.headers)),
        contentLength=int(request.headers.get("Content-Length") or 0),
    )
    response_payload = ResponsePayload(
        headers=hide_sensitive_headers(dict(response.headers)),
        statusCode=response.status_code,
        reasonPhrase=response.reason_phrase,
        contentLength=len(response.content),
    )
    app_payload: Optional[AppPayload] = None
    if app := getattr(request, "app", None):
        app_payload = AppPayload(
            id=graphene.Node.to_global_id("App", app.id), name=app.name
        )
    operations_payload = GraphQLOperationsPayload(
        count=len(gql_operations), operations=[]
    )
    payload = ApiCallPayload(
        eventType=ObservabilityEventTypes.ApiCall,
        request=request_payload,
        response=response_payload,
        app=app_payload,
        gql_operations=operations_payload,
    )
    base_dump = _json_serialize(payload)
    remaining_bytes = bytes_limit - len(base_dump)
    if remaining_bytes < 0:
        raise ValueError(f"Payload too big. Can't truncate to {bytes_limit}")
    try:
        operations_payload["operations"] = serialize_gql_operation_results(
            gql_operations, remaining_bytes
        )
    except ValueError:
        pass
    return _json_serialize(payload)


@traced_payload_generator
def generate_event_delivery_attempt_payload(
    attempt: "EventDeliveryAttempt",
    next_retry: Optional["datetime"],
    bytes_limit: int,
) -> str:
    delivery_data: Optional[EventDeliveryPayload] = None
    webhook_data: Optional[WebhookPayload] = None
    app_data: Optional[AppPayload] = None
    payload = None
    if delivery := attempt.delivery:
        if delivery.payload:
            payload = delivery.payload.payload
        delivery_data = EventDeliveryPayload(
            id=graphene.Node.to_global_id("EventDelivery", delivery.pk),
            status=delivery.status,
            eventType=delivery.event_type,
            payload=EventDeliveryDataPayload(
                contentLength=len(payload or ""), body=TRUNC_PLACEHOLDER
            ),
        )
        if webhook := delivery.webhook:
            app_data = AppPayload(
                id=graphene.Node.to_global_id("App", webhook.app.pk),
                name=webhook.app.name,
            )
            webhook_data = WebhookPayload(
                id=graphene.Node.to_global_id("Webhook", webhook.pk),
                name=webhook.name or "",
                targetUrl=webhook.target_url,
            )
    response_body = attempt.response or ""
    data = EventDeliveryAttemptPayload(
        eventType=ObservabilityEventTypes.EventDeliveryAttempt,
        eventDeliveryAttempt=AttemptPayload(
            id=graphene.Node.to_global_id("EventDeliveryAttempt", attempt.pk),
            time=attempt.created_at,
            duration=attempt.duration,
            status=attempt.status,
            nextRetry=next_retry,
        ),
        request=RequestHeadersPayload(
            headers=json.loads(attempt.request_headers or "{}")
        ),
        response=ResponseWithBodyPayload(
            headers=json.loads(attempt.response_headers or "{}"),
            contentLength=len(response_body.encode("utf-8")),
            body=TRUNC_PLACEHOLDER,
            statusCode=200,
            reasonPhrase="OK",
        ),
        eventDelivery=delivery_data,
        webhook=webhook_data,
        app=app_data,
    )
    initial_dump = _json_serialize(data)
    remaining_bytes = bytes_limit - len(initial_dump)
    if remaining_bytes < 0:
        raise ValueError(f"Payload too big. Can't truncate to {bytes_limit}")
    trunc_resp_body = JsonTruncText.truncate(response_body, remaining_bytes // 2)
    data["response"]["body"] = trunc_resp_body
    if delivery_data and payload:
        delivery_data["payload"]["body"] = JsonTruncText.truncate(
            payload, remaining_bytes - trunc_resp_body.byte_size
        )
    return _json_serialize(data)

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
from .obfuscation import (
    anonymize_event_payload,
    anonymize_gql_operation_response,
    hide_sensitive_headers,
)
from .sensitive_data import SENSITIVE_GQL_FIELDS
from .utils import CustomJsonEncoder, JsonTruncText

if TYPE_CHECKING:
    from ...core.models import EventDeliveryAttempt
    from . import GraphQLOperationResponse


class ObservabilityEventTypes(str, Enum):
    API_CALL = "observability_api_call"
    EVENT_DELIVERY_ATTEMPT = "observability_event_delivery_attempt"


class ObservabilityEventPayload(TypedDict):
    event_type: ObservabilityEventTypes


class GraphQLOperationPayload(TypedDict):
    name: Optional[JsonTruncText]
    operation_type: Optional[str]
    query: Optional[JsonTruncText]
    result: Optional[JsonTruncText]


class RequestPayload(TypedDict):
    id: str
    method: str
    url: str
    time: float
    headers: Dict[str, str]
    content_length: int


class ResponsePayload(TypedDict):
    headers: Dict[str, str]
    status_code: Optional[int]
    content_length: int


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
    content_length: int
    body: JsonTruncText


class EventDeliveryPayload(TypedDict):
    id: str
    status: str
    event_type: str
    payload: EventDeliveryDataPayload


class WebhookPayload(TypedDict):
    id: str
    name: str
    target_url: str
    subscription_query: Optional[JsonTruncText]


class AttemptPayload(TypedDict):
    id: str
    time: datetime
    duration: Optional[float]
    status: str
    next_retry: Optional[datetime]


class RequestHeadersPayload(TypedDict):
    headers: Dict[str, str]


class ResponseWithBodyPayload(ResponsePayload):
    body: JsonTruncText


class EventDeliveryAttemptPayload(ObservabilityEventPayload):
    event_delivery_attempt: AttemptPayload
    request: RequestHeadersPayload
    response: ResponseWithBodyPayload
    event_delivery: EventDeliveryPayload
    webhook: WebhookPayload
    app: AppPayload


def _json_serialize(obj: Any, pretty=False):
    if pretty:
        return json.dumps(obj, indent=2, ensure_ascii=True, cls=CustomJsonEncoder)
    return json.dumps(obj, ensure_ascii=True, cls=CustomJsonEncoder)


TRUNC_PLACEHOLDER = JsonTruncText(truncated=False)
EMPTY_TRUNC = JsonTruncText(truncated=True)


GQL_OPERATION_PLACEHOLDER = GraphQLOperationPayload(
    name=TRUNC_PLACEHOLDER,
    operation_type="subscription",
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
    anonymize_gql_operation_response(operation, SENSITIVE_GQL_FIELDS)
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
            operation_type=operation_type,
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
    payload = ApiCallPayload(
        event_type=ObservabilityEventTypes.API_CALL,
        request=RequestPayload(
            id=str(uuid.uuid4()),
            method=request.method or "",
            url=request.build_absolute_uri(request.get_full_path()),
            time=getattr(request, "request_time", timezone.now()).timestamp(),
            headers=hide_sensitive_headers(dict(request.headers)),
            content_length=int(request.headers.get("Content-Length") or 0),
        ),
        response=ResponsePayload(
            headers=hide_sensitive_headers(dict(response.headers)),
            status_code=response.status_code,
            content_length=len(response.content),
        ),
        app=None,
        gql_operations=GraphQLOperationsPayload(
            count=len(gql_operations), operations=[]
        ),
    )
    if app := getattr(request, "app", None):
        payload["app"] = AppPayload(
            id=graphene.Node.to_global_id("App", app.id),
            name=app.name,
        )
    initial_dump = _json_serialize(payload)
    remaining_bytes = bytes_limit - len(initial_dump)
    if remaining_bytes < 0:
        raise ValueError(f"Payload too big. Can't truncate to {bytes_limit}")
    try:
        payload["gql_operations"]["operations"] = serialize_gql_operation_results(
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
    if not attempt.delivery:
        raise ValueError(
            f"EventDeliveryAttempt {attempt.id} is not assigned to delivery."
            "Can't generate payload."
        )
    if not attempt.delivery.payload or not attempt.delivery.webhook:
        raise ValueError(
            f"EventDelivery {attempt.delivery.id} do not have "
            "payload or webhook set. Can't generate payload."
        )
    response_body = attempt.response or ""
    data = EventDeliveryAttemptPayload(
        event_type=ObservabilityEventTypes.EVENT_DELIVERY_ATTEMPT,
        event_delivery_attempt=AttemptPayload(
            id=graphene.Node.to_global_id("EventDeliveryAttempt", attempt.pk),
            time=attempt.created_at,
            duration=attempt.duration,
            status=attempt.status,
            next_retry=next_retry,
        ),
        request=RequestHeadersPayload(
            headers=json.loads(attempt.request_headers or "{}")
        ),
        response=ResponseWithBodyPayload(
            headers=json.loads(attempt.response_headers or "{}"),
            content_length=len(response_body.encode("utf-8")),
            body=TRUNC_PLACEHOLDER,
            status_code=attempt.response_status_code,
        ),
        event_delivery=EventDeliveryPayload(
            id=graphene.Node.to_global_id("EventDelivery", attempt.delivery.pk),
            status=attempt.delivery.status,
            event_type=attempt.delivery.event_type,
            payload=EventDeliveryDataPayload(
                content_length=len(attempt.delivery.payload.payload),
                body=TRUNC_PLACEHOLDER,
            ),
        ),
        webhook=WebhookPayload(
            id=graphene.Node.to_global_id("Webhook", attempt.delivery.webhook.pk),
            name=attempt.delivery.webhook.name or "",
            target_url=attempt.delivery.webhook.target_url,
            subscription_query=TRUNC_PLACEHOLDER,
        ),
        app=AppPayload(
            id=graphene.Node.to_global_id("App", attempt.delivery.webhook.app.pk),
            name=attempt.delivery.webhook.app.name,
        ),
    )
    initial_dump = _json_serialize(data)
    remaining_bytes = bytes_limit - len(initial_dump)
    if remaining_bytes < 0:
        raise ValueError(f"Payload too big. Can't truncate to {bytes_limit}")
    trunc_resp_body = JsonTruncText.truncate(response_body, remaining_bytes // 3)
    remaining_bytes -= trunc_resp_body.byte_size
    data["response"]["body"] = trunc_resp_body

    subscription_query = attempt.delivery.webhook.subscription_query
    data["webhook"]["subscription_query"] = None
    if subscription_query:
        trunc_subscription_query = JsonTruncText.truncate(
            subscription_query, remaining_bytes // 2
        )
        remaining_bytes -= trunc_subscription_query.byte_size
        data["webhook"]["subscription_query"] = trunc_subscription_query

    payload = anonymize_event_payload(
        subscription_query,
        attempt.delivery.event_type,
        cast(List, json.loads(attempt.delivery.payload.payload)),
        SENSITIVE_GQL_FIELDS,
    )
    trunc_payload = JsonTruncText.truncate(
        _json_serialize(payload, True), remaining_bytes
    )
    data["event_delivery"]["payload"]["body"] = trunc_payload
    return _json_serialize(data)

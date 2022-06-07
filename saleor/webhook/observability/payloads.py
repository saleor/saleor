import json
import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import graphene
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from graphene.utils.str_converters import to_camel_case as str_to_camel_case
from graphql import get_operation_ast

from .. import traced_payload_generator
from ..event_types import WebhookEventSyncType
from .exceptions import TruncationError
from .obfuscation import (
    anonymize_event_payload,
    anonymize_gql_operation_response,
    hide_sensitive_headers,
)
from .payload_schema import (
    ApiCallPayload,
    ApiCallRequest,
    ApiCallResponse,
    App,
    EventDelivery,
    EventDeliveryAttemptPayload,
    EventDeliveryAttemptRequest,
    EventDeliveryAttemptResponse,
    EventDeliveryPayload,
    GraphQLOperation,
    HttpHeaders,
    JsonTruncText,
    ObservabilityEventTypes,
    Webhook,
)
from .sensitive_data import SENSITIVE_GQL_FIELDS

if TYPE_CHECKING:
    from ...core.models import EventDeliveryAttempt
    from .utils import GraphQLOperationResponse


class CustomJsonEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, JsonTruncText):
            return {"text": o.text, "truncated": o.truncated}
        return super().default(o)


def to_camel_case(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        data = {}
        for k, v in obj.items():
            data[str_to_camel_case(k)] = to_camel_case(v)
        return data
    if isinstance(obj, list):
        return [to_camel_case(i) for i in obj]
    return obj


def pretty_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True)


def dump_payload(payload: Any) -> str:
    return json.dumps(to_camel_case(payload), ensure_ascii=True, cls=CustomJsonEncoder)


TRUNC_PLACEHOLDER = JsonTruncText(truncated=False)
EMPTY_TRUNC = JsonTruncText(truncated=True)
GQL_OPERATION_PLACEHOLDER = GraphQLOperation(
    name=TRUNC_PLACEHOLDER,
    operation_type="subscription",
    query=TRUNC_PLACEHOLDER,
    result=TRUNC_PLACEHOLDER,
    result_invalid=False,
)
GQL_OPERATION_PLACEHOLDER_SIZE = len(dump_payload(GQL_OPERATION_PLACEHOLDER))


def serialize_headers(headers: Dict[str, str]) -> HttpHeaders:
    return [(k, v) for k, v in hide_sensitive_headers(headers).items()]


def serialize_gql_operation_result(
    operation: "GraphQLOperationResponse", bytes_limit: int
) -> Tuple[GraphQLOperation, int]:
    bytes_limit -= GQL_OPERATION_PLACEHOLDER_SIZE
    if bytes_limit < 0:
        raise TruncationError()
    anonymize_gql_operation_response(operation, SENSITIVE_GQL_FIELDS)
    payload = GraphQLOperation(
        name=None,
        operation_type=None,
        query=None,
        result=None,
        result_invalid=operation.result_invalid,
    )
    if operation.name:
        name = JsonTruncText.truncate(operation.name, bytes_limit)
        bytes_limit -= name.byte_size
        payload["name"] = name
    if operation.query:
        query = JsonTruncText.truncate(
            operation.query.document_string, bytes_limit // 2
        )
        bytes_limit -= query.byte_size
        payload["query"] = query
        if definition := get_operation_ast(
            operation.query.document_ast, operation.name
        ):
            payload["operation_type"] = definition.operation
    if operation.result:
        result = JsonTruncText.truncate(pretty_json(operation.result), bytes_limit)
        bytes_limit -= result.byte_size
        payload["result"] = result
    return payload, max(0, bytes_limit)


def serialize_gql_operation_results(
    operations: List["GraphQLOperationResponse"], bytes_limit: int
) -> List[GraphQLOperation]:
    if bytes_limit - len(operations) * GQL_OPERATION_PLACEHOLDER_SIZE < 0:
        raise TruncationError()
    payloads: List[GraphQLOperation] = []
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
) -> ApiCallPayload:
    payload = ApiCallPayload(
        event_type=ObservabilityEventTypes.API_CALL,
        request=ApiCallRequest(
            id=str(uuid.uuid4()),
            method=request.method or "",
            url=request.build_absolute_uri(request.get_full_path()),
            time=getattr(request, "request_time", timezone.now()).timestamp(),
            headers=serialize_headers(dict(request.headers)),
            content_length=int(request.headers.get("Content-Length") or 0),
        ),
        response=ApiCallResponse(
            headers=serialize_headers(dict(response.headers)),
            status_code=response.status_code,
            content_length=len(response.content),
        ),
        app=None,
        gql_operations=[],
    )
    if app := getattr(request, "app", None):
        payload["app"] = App(
            id=graphene.Node.to_global_id("App", app.id),
            name=app.name,
        )
    remaining_bytes = bytes_limit - len(dump_payload(payload))
    if remaining_bytes < 0:
        raise TruncationError()
    payload["gql_operations"] = serialize_gql_operation_results(
        gql_operations, remaining_bytes
    )
    return payload


@traced_payload_generator
def generate_event_delivery_attempt_payload(
    attempt: "EventDeliveryAttempt",
    next_retry: Optional["datetime"],
    bytes_limit: int,
) -> EventDeliveryAttemptPayload:
    if not attempt.delivery:
        raise ValueError(
            f"EventDeliveryAttempt {attempt.id} is not assigned to delivery."
            "Can't generate payload."
        )
    if not attempt.delivery.payload:
        raise ValueError(
            f"EventDelivery {attempt.delivery.id} do not have "
            "payload set. Can't generate payload."
        )
    response_body = attempt.response or ""
    payload = EventDeliveryAttemptPayload(
        id=graphene.Node.to_global_id("EventDeliveryAttempt", attempt.pk),
        event_type=ObservabilityEventTypes.EVENT_DELIVERY_ATTEMPT,
        time=attempt.created_at,
        duration=attempt.duration,
        status=attempt.status,
        next_retry=next_retry,
        request=EventDeliveryAttemptRequest(
            headers=serialize_headers(json.loads(attempt.request_headers or "{}")),
        ),
        response=EventDeliveryAttemptResponse(
            headers=serialize_headers(json.loads(attempt.response_headers or "{}")),
            content_length=len(response_body.encode("utf-8")),
            body=TRUNC_PLACEHOLDER,
            status_code=attempt.response_status_code,
        ),
        event_delivery=EventDelivery(
            id=graphene.Node.to_global_id("EventDelivery", attempt.delivery.pk),
            status=attempt.delivery.status,
            event_type=attempt.delivery.event_type,
            event_sync=attempt.delivery.event_type in WebhookEventSyncType.ALL,
            payload=EventDeliveryPayload(
                content_length=len(attempt.delivery.payload.payload.encode("utf-8")),
                body=TRUNC_PLACEHOLDER,
            ),
        ),
        webhook=Webhook(
            id=graphene.Node.to_global_id("Webhook", attempt.delivery.webhook.pk),
            name=attempt.delivery.webhook.name or "",
            target_url=attempt.delivery.webhook.target_url,
            subscription_query=TRUNC_PLACEHOLDER,
        ),
        app=App(
            id=graphene.Node.to_global_id("App", attempt.delivery.webhook.app.pk),
            name=attempt.delivery.webhook.app.name,
        ),
    )
    if (remaining := bytes_limit - len(dump_payload(payload))) < 0:
        raise TruncationError()

    subscription_query = attempt.delivery.webhook.subscription_query
    if subscription_query:
        trunc_sub_query = JsonTruncText.truncate(subscription_query, remaining // 4)
        remaining -= trunc_sub_query.byte_size
        payload["webhook"]["subscription_query"] = trunc_sub_query
    else:
        payload["webhook"]["subscription_query"] = None

    payload["response"]["body"] = JsonTruncText.truncate(response_body, remaining // 2)
    remaining -= payload["response"]["body"].byte_size

    event_delivery_payload = json.loads(attempt.delivery.payload.payload)
    event_delivery_payload = anonymize_event_payload(
        subscription_query,
        attempt.delivery.event_type,
        event_delivery_payload,
        SENSITIVE_GQL_FIELDS,
    )
    payload["event_delivery"]["payload"]["body"] = JsonTruncText.truncate(
        pretty_json(event_delivery_payload), remaining
    )
    return payload

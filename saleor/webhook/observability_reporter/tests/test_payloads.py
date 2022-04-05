import json
from datetime import datetime
from uuid import UUID

import graphene
import pytest
from django.http import JsonResponse
from django.utils import timezone

from ....core import EventDeliveryStatus
from ....webhook.event_types import WebhookEventAsyncType
from .. import GraphQLOperationResponse
from ..payloads import (
    GQL_OPERATION_PLACEHOLDER_SIZE,
    _json_serialize,
    generate_api_call_payload,
    generate_event_delivery_attempt_payload,
    serialize_gql_operation_result,
    serialize_gql_operation_results,
)
from ..utils import JsonTruncText


def test_serialize_gql_operation_result(gql_operation_factory):
    query = "query FirstQuery { shop { name } }"
    result = {"data": "result"}
    operation_result = gql_operation_factory(query, "FirstQuery", None, result)
    payload, _ = serialize_gql_operation_result(operation_result, 1024)
    assert payload == {
        "name": JsonTruncText("FirstQuery", False),
        "operation_type": "query",
        "query": JsonTruncText(query, False),
        "result": JsonTruncText(_json_serialize(result, pretty=True), False),
    }


def test_serialize_gql_operation_result_when_no_operation_data():
    result = GraphQLOperationResponse()
    payload, _ = serialize_gql_operation_result(result, 1024)
    assert payload == {
        "name": None,
        "operation_type": None,
        "query": None,
        "result": None,
    }


def test_serialize_gql_operation_result_when_too_low_bytes_limit():
    result = GraphQLOperationResponse()
    with pytest.raises(ValueError):
        serialize_gql_operation_result(result, GQL_OPERATION_PLACEHOLDER_SIZE - 1)


def test_serialize_gql_operation_result_when_minimal_bytes_limit(gql_operation_factory):
    query = "query FirstQuery { shop { name } }"
    operation_result = gql_operation_factory(
        query, "FirstQuery", None, {"data": "result"}
    )
    payload, left_bytes = serialize_gql_operation_result(
        operation_result, GQL_OPERATION_PLACEHOLDER_SIZE
    )
    serialized = _json_serialize(payload)
    assert payload == {
        "name": JsonTruncText("", True),
        "operation_type": "query",
        "query": JsonTruncText("", True),
        "result": JsonTruncText("", True),
    }
    assert left_bytes == 0
    assert len(serialized) <= GQL_OPERATION_PLACEHOLDER_SIZE


def test_serialize_gql_operation_result_when_truncated(gql_operation_factory):
    query = "query FirstQuery { shop { name } }"
    operation_result = gql_operation_factory(
        query, "FirstQuery", None, {"data": "result"}
    )
    bytes_limit = 200
    payload, left_bytes = serialize_gql_operation_result(operation_result, bytes_limit)
    serialized = _json_serialize(payload)
    assert payload == {
        "name": JsonTruncText("FirstQuery", False),
        "operation_type": "query",
        "query": JsonTruncText("query FirstQu", True),
        "result": JsonTruncText('{\n  "data": ', True),
    }
    assert left_bytes == 0
    assert len(serialized) <= bytes_limit


def test_serialize_gql_operation_results(gql_operation_factory):
    query = "query FirstQuery { shop { name } } query SecondQuery { shop { name } }"
    result = {"data": "result"}
    first_result = gql_operation_factory(query, "FirstQuery", None, result)
    second_result = gql_operation_factory(query, "SecondQuery", None, result)
    payloads = serialize_gql_operation_results([first_result, second_result], 1024)
    assert payloads == [
        {
            "name": JsonTruncText("FirstQuery", False),
            "operation_type": "query",
            "query": JsonTruncText(query, False),
            "result": JsonTruncText(_json_serialize(result, pretty=True), False),
        },
        {
            "name": JsonTruncText("SecondQuery", False),
            "operation_type": "query",
            "query": JsonTruncText(query, False),
            "result": JsonTruncText(_json_serialize(result, pretty=True), False),
        },
    ]


def test_serialize_gql_operation_results_when_minimal_bytes_limit(
    gql_operation_factory,
):
    query = "query FirstQuery { shop { name } } query SecondQuery { shop { name } }"
    result = {"data": "result"}
    first_result = gql_operation_factory(query, "FirstQuery", None, result)
    second_result = gql_operation_factory(query, "SecondQuery", None, result)
    payloads = serialize_gql_operation_results(
        [first_result, second_result], 2 * GQL_OPERATION_PLACEHOLDER_SIZE
    )
    serialized = _json_serialize(payloads)
    assert payloads == [
        {
            "name": JsonTruncText("", True),
            "operation_type": "query",
            "query": JsonTruncText("", True),
            "result": JsonTruncText("", True),
        },
        {
            "name": JsonTruncText("", True),
            "operation_type": "query",
            "query": JsonTruncText("", True),
            "result": JsonTruncText("", True),
        },
    ]
    assert len(serialized) <= 2 * GQL_OPERATION_PLACEHOLDER_SIZE


def test_serialize_gql_operation_results_when_too_low_bytes_limit(
    gql_operation_factory,
):
    query = "query FirstQuery { shop { name } } query SecondQuery { shop { name } }"
    result = {"data": "result"}
    first_result = gql_operation_factory(query, "FirstQuery", None, result)
    second_result = gql_operation_factory(query, "SecondQuery", None, result)
    with pytest.raises(ValueError):
        serialize_gql_operation_results(
            [first_result, second_result], 2 * GQL_OPERATION_PLACEHOLDER_SIZE - 1
        )


def test_generate_api_call_payload(app, rf, gql_operation_factory):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.request_time = datetime(1914, 6, 28, 10, 50, tzinfo=timezone.utc)
    request.app = app
    response = JsonResponse({"response": "data"})
    query_a = "query FirstQuery { shop { name } }"
    query_b = "query SecondQuery { shop { name } }"
    result_a = {"data": "result A"}
    result_b = {"data": "result B"}
    first_result = gql_operation_factory(query_a, "FirstQuery", None, result_a)
    second_result = gql_operation_factory(query_b, "SecondQuery", None, result_b)

    payload = json.loads(
        generate_api_call_payload(
            request, response, [first_result, second_result], 2048
        )
    )

    assert UUID(payload["request"].pop("id"), version=4)
    assert payload == {
        "event_type": "observability_api_call",
        "request": {
            "method": "POST",
            "url": "http://testserver/graphql",
            "time": request.request_time.timestamp(),
            "headers": {
                "Content-Length": "19",
                "Content-Type": "application/json",
                "Cookie": "",
            },
            "content_length": 19,
        },
        "response": {
            "headers": {"Content-Type": "application/json"},
            "content_length": 20,
            "status_code": 200,
        },
        "app": {
            "id": graphene.Node.to_global_id("App", app.pk),
            "name": "Sample app objects",
        },
        "gql_operations": {
            "count": 2,
            "operations": [
                {
                    "name": {"text": "FirstQuery", "truncated": False},
                    "operation_type": "query",
                    "query": {"text": query_a, "truncated": False},
                    "result": {
                        "text": _json_serialize(result_a, pretty=True),
                        "truncated": False,
                    },
                },
                {
                    "name": {"text": "SecondQuery", "truncated": False},
                    "operation_type": "query",
                    "query": {"text": query_b, "truncated": False},
                    "result": {
                        "text": _json_serialize(result_b, pretty=True),
                        "truncated": False,
                    },
                },
            ],
        },
    }


def test_generate_api_call_payload_request_not_from_app(rf):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.app = None
    response = JsonResponse({"response": "data"})
    payload_without_operations = generate_api_call_payload(request, response, [], 1024)

    payload = json.loads(payload_without_operations)

    assert payload["app"] is None


def test_generate_api_call_payload_skip_operations_when_size_limit_too_low(
    app, rf, gql_operation_factory
):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.request_time = datetime(1914, 6, 28, 10, 50, tzinfo=timezone.utc)
    request.app = app
    response = JsonResponse({"response": "data"})
    query = "query FirstQuery { shop { name } } query SecondQuery { shop { name } }"
    result = {"data": "result A"}
    first_result = gql_operation_factory(query, "FirstQuery", None, result)
    second_result = gql_operation_factory(query, "SecondQuery", None, result)
    payload_without_operations = generate_api_call_payload(request, response, [], 1024)

    payload = json.loads(
        generate_api_call_payload(
            request,
            response,
            [first_result, second_result],
            len(payload_without_operations),
        )
    )

    assert payload["gql_operations"]["operations"] == []
    assert payload["gql_operations"]["count"] == 2


def test_generate_api_call_payload_when_too_low_bytes_limit(app, rf):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.request_time = datetime(1914, 6, 28, 10, 50, tzinfo=timezone.utc)
    request.app = app
    response = JsonResponse({"response": "data"})
    payload = generate_api_call_payload(request, response, [], 1024)

    with pytest.raises(ValueError):
        generate_api_call_payload(request, response, [], len(payload) - 1)


def test_generate_event_delivery_attempt_payload(event_attempt):
    event_attempt.created_at = datetime(1914, 6, 28, 10, 50, tzinfo=timezone.utc)
    delivery = event_attempt.delivery
    webhook = delivery.webhook
    app = webhook.app

    payload = json.loads(
        generate_event_delivery_attempt_payload(event_attempt, None, 1024)
    )

    assert payload == {
        "event_type": "observability_event_delivery_attempt",
        "event_delivery_attempt": {
            "id": graphene.Node.to_global_id("EventDeliveryAttempt", event_attempt.pk),
            "time": "1914-06-28T10:50:00Z",
            "duration": None,
            "status": EventDeliveryStatus.PENDING,
            "next_retry": None,
        },
        "request": {"headers": {}},
        "response": {
            "headers": {},
            "content_length": 16,
            "status_code": None,
            "body": {"text": "example_response", "truncated": False},
        },
        "event_delivery": {
            "id": graphene.Node.to_global_id("EventDelivery", delivery.pk),
            "payload": {
                "body": {
                    "text": '{"payload_key": "payload_value"}',
                    "truncated": False,
                },
                "content_length": 32,
            },
            "status": EventDeliveryStatus.PENDING,
            "event_type": WebhookEventAsyncType.ANY,
        },
        "webhook": {
            "id": graphene.Node.to_global_id("Webhook", webhook.pk),
            "name": "Simple webhook",
            "target_url": "http://www.example.com/test",
        },
        "app": {
            "id": graphene.Node.to_global_id("App", app.pk),
            "name": "Sample app objects",
        },
    }


def test_generate_event_delivery_attempt_payload_failed(event_attempt):
    TOO_SMALL_BYTES_LIMIT = 10
    with pytest.raises(ValueError):
        generate_event_delivery_attempt_payload(
            event_attempt, None, TOO_SMALL_BYTES_LIMIT
        )


def test_generate_event_delivery_attempt_payload_with_next_retry_date(
    event_attempt,
):
    next_retry_date = datetime(1914, 6, 28, 10, 50, tzinfo=timezone.utc)
    payload = json.loads(
        generate_event_delivery_attempt_payload(event_attempt, next_retry_date, 1024)
    )
    assert payload["event_delivery_attempt"]["next_retry"] == "1914-06-28T10:50:00Z"


def test_generate_event_delivery_attempt_payload_with_empty_headers(
    event_attempt,
):
    headers = {"Content-Length": "19", "Content-Type": "application/json"}
    event_attempt.request_headers = json.dumps(headers)
    event_attempt.response_headers = json.dumps(headers)

    payload = json.loads(
        generate_event_delivery_attempt_payload(event_attempt, None, 1024)
    )

    assert payload["request"]["headers"] == headers
    assert payload["response"]["headers"] == headers

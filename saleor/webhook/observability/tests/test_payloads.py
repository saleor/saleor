import json
from datetime import datetime
from unittest.mock import patch
from uuid import UUID

import graphene
import pytest
from django.http import JsonResponse
from django.utils import timezone

from ....core import EventDeliveryStatus
from ....tests.consts import TEST_SERVER_DOMAIN
from ....webhook.event_types import WebhookEventAsyncType
from ..exceptions import TruncationError
from ..obfuscation import MASK
from ..payload_schema import (
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
    ObservabilityEventTypes,
    Webhook,
)
from ..payloads import (
    GQL_OPERATION_PLACEHOLDER_SIZE,
    JsonTruncText,
    dump_payload,
    generate_api_call_payload,
    generate_event_delivery_attempt_payload,
    pretty_json,
    serialize_gql_operation_result,
    serialize_gql_operation_results,
    serialize_headers,
    to_camel_case,
)
from ..utils import GraphQLOperationResponse


@pytest.mark.parametrize(
    "snake_payload,expected_camel",
    [
        (
            ApiCallRequest(
                id="id",
                method="GET",
                url="http://example.com",
                time=123456.2,
                headers=[("snake_header_1", "val"), ("snake_header_2", "val")],
                content_length=1024,
            ),
            {
                "id": "id",
                "method": "GET",
                "url": "http://example.com",
                "time": 123456.2,
                "headers": [("snake_header_1", "val"), ("snake_header_2", "val")],
                "contentLength": 1024,
            },
        ),
        (
            {
                "key_a": {"sub_key_a": "val", "sub_key_b": "val"},
                "key_b": [{"list_key_a": "val"}, {"list_key_b": "val"}],
            },
            {
                "keyA": {"subKeyA": "val", "subKeyB": "val"},
                "keyB": [{"listKeyA": "val"}, {"listKeyB": "val"}],
            },
        ),
    ],
)
def test_to_camel_case(snake_payload, expected_camel):
    assert to_camel_case(snake_payload) == expected_camel


def test_serialize_gql_operation_result(gql_operation_factory):
    bytes_limit = 1024
    query = "query FirstQuery { shop { name } }"
    result = {"data": "result"}
    operation_result = gql_operation_factory(query, "FirstQuery", None, result)
    payload, _ = serialize_gql_operation_result(operation_result, bytes_limit)
    assert payload == GraphQLOperation(
        name=JsonTruncText("FirstQuery", False),
        operation_type="query",
        query=JsonTruncText(query, False),
        result=JsonTruncText(pretty_json(result), False),
        result_invalid=False,
    )
    assert len(dump_payload(payload)) <= bytes_limit


def test_serialize_gql_operation_result_when_no_operation_data():
    bytes_limit = 1024
    result = GraphQLOperationResponse()
    payload, _ = serialize_gql_operation_result(result, bytes_limit)
    assert payload == GraphQLOperation(
        name=None, operation_type=None, query=None, result=None, result_invalid=False
    )
    assert len(dump_payload(payload)) <= bytes_limit


def test_serialize_gql_operation_result_when_too_low_bytes_limit():
    result = GraphQLOperationResponse()
    with pytest.raises(TruncationError):
        serialize_gql_operation_result(result, GQL_OPERATION_PLACEHOLDER_SIZE - 1)


def test_serialize_gql_operation_result_when_minimal_bytes_limit(gql_operation_factory):
    query = "query FirstQuery { shop { name } }"
    operation_result = gql_operation_factory(
        query, "FirstQuery", None, {"data": "result"}
    )
    payload, left_bytes = serialize_gql_operation_result(
        operation_result, GQL_OPERATION_PLACEHOLDER_SIZE
    )
    assert payload == GraphQLOperation(
        name=JsonTruncText("", True),
        operation_type="query",
        query=JsonTruncText("", True),
        result=JsonTruncText("", True),
        result_invalid=False,
    )
    assert left_bytes == 0
    assert len(dump_payload(payload)) <= GQL_OPERATION_PLACEHOLDER_SIZE


def test_serialize_gql_operation_result_when_truncated(gql_operation_factory):
    query = "query FirstQuery { shop { name } }"
    operation_result = gql_operation_factory(
        query, "FirstQuery", None, {"data": "result"}
    )
    bytes_limit = 225
    payload, left_bytes = serialize_gql_operation_result(operation_result, bytes_limit)
    assert payload == GraphQLOperation(
        name=JsonTruncText("FirstQuery", False),
        operation_type="query",
        query=JsonTruncText("query FirstQue", True),
        result=JsonTruncText('{\n  "data": ', True),
        result_invalid=False,
    )
    assert left_bytes == 0
    assert len(dump_payload(payload)) <= bytes_limit


def test_serialize_gql_operation_results(gql_operation_factory):
    query = "query FirstQuery { shop { name } } query SecondQuery { shop { name } }"
    result = {"data": "result"}
    first_result = gql_operation_factory(query, "FirstQuery", None, result)
    second_result = gql_operation_factory(query, "SecondQuery", None, result)
    payloads = serialize_gql_operation_results([first_result, second_result], 1024)
    assert payloads == [
        GraphQLOperation(
            name=JsonTruncText("FirstQuery", False),
            operation_type="query",
            query=JsonTruncText(query, False),
            result=JsonTruncText(pretty_json(result), False),
            result_invalid=False,
        ),
        GraphQLOperation(
            name=JsonTruncText("SecondQuery", False),
            operation_type="query",
            query=JsonTruncText(query, False),
            result=JsonTruncText(pretty_json(result), False),
            result_invalid=False,
        ),
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
    assert payloads == [
        GraphQLOperation(
            name=JsonTruncText("", True),
            operation_type="query",
            query=JsonTruncText("", True),
            result=JsonTruncText("", True),
            result_invalid=False,
        ),
        GraphQLOperation(
            name=JsonTruncText("", True),
            operation_type="query",
            query=JsonTruncText("", True),
            result=JsonTruncText("", True),
            result_invalid=False,
        ),
    ]
    assert len(dump_payload(payloads)) <= 2 * GQL_OPERATION_PLACEHOLDER_SIZE


def test_serialize_gql_operation_results_when_too_low_bytes_limit(
    gql_operation_factory,
):
    query = "query FirstQuery { shop { name } } query SecondQuery { shop { name } }"
    result = {"data": "result"}
    first_result = gql_operation_factory(query, "FirstQuery", None, result)
    second_result = gql_operation_factory(query, "SecondQuery", None, result)
    with pytest.raises(TruncationError):
        serialize_gql_operation_results(
            [first_result, second_result], 2 * GQL_OPERATION_PLACEHOLDER_SIZE - 1
        )


@pytest.mark.parametrize(
    "headers,expected",
    [
        ({}, []),
        (None, []),
        (
            {"Content-Length": "19", "Content-Type": "application/json"},
            [("Content-Length", "19"), ("Content-Type", "application/json")],
        ),
    ],
)
def test_serialize_headers(headers, expected):
    assert serialize_headers(headers) == expected


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

    payload = generate_api_call_payload(
        request, response, [first_result, second_result], 2048
    )
    request_id = payload["request"]["id"]

    assert UUID(request_id, version=4)
    assert payload == ApiCallPayload(
        event_type=ObservabilityEventTypes.API_CALL,
        request=ApiCallRequest(
            id=request_id,
            method="POST",
            url=f"http://{TEST_SERVER_DOMAIN}/graphql",
            time=request.request_time.timestamp(),
            content_length=19,
            headers=[
                ("Cookie", "***"),
                ("Content-Length", "19"),
                ("Content-Type", "application/json"),
            ],
        ),
        app=App(
            id=graphene.Node.to_global_id("App", app.pk), name="Sample app objects"
        ),
        response=ApiCallResponse(
            headers=[
                ("Content-Type", "application/json"),
            ],
            status_code=200,
            content_length=20,
        ),
        gql_operations=[
            GraphQLOperation(
                name=JsonTruncText("FirstQuery", False),
                operation_type="query",
                query=JsonTruncText(query_a, False),
                result=JsonTruncText(pretty_json(result_a), False),
                result_invalid=False,
            ),
            GraphQLOperation(
                name=JsonTruncText("SecondQuery", False),
                operation_type="query",
                query=JsonTruncText(query_b, False),
                result=JsonTruncText(pretty_json(result_b), False),
                result_invalid=False,
            ),
        ],
    )


def test_generate_api_call_payload_request_not_from_app(rf):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.app = None
    response = JsonResponse({"response": "data"})
    payload = generate_api_call_payload(request, response, [], 1024)

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
    bytes_limit = (
        len(dump_payload(payload_without_operations))
        + GQL_OPERATION_PLACEHOLDER_SIZE * 2
    )
    operation_trunc_payload = GraphQLOperation(
        name=JsonTruncText("", True),
        operation_type="query",
        query=JsonTruncText("", True),
        result=JsonTruncText("", True),
        result_invalid=False,
    )

    payload = generate_api_call_payload(
        request, response, [first_result, second_result], bytes_limit
    )

    assert payload["gql_operations"] == [operation_trunc_payload] * 2


def test_generate_api_call_payload_when_too_low_bytes_limit(app, rf):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.request_time = datetime(1914, 6, 28, 10, 50, tzinfo=timezone.utc)
    request.app = app
    response = JsonResponse({"response": "data"})
    payload = generate_api_call_payload(request, response, [], 1024)

    with pytest.raises(TruncationError):
        generate_api_call_payload(request, response, [], len(payload) - 1)


def test_generate_event_delivery_attempt_payload(event_attempt):
    created_at = datetime(1914, 6, 28, 10, 50, tzinfo=timezone.utc)
    event_attempt.created_at = created_at
    delivery = event_attempt.delivery
    webhook = delivery.webhook
    app = webhook.app

    payload = generate_event_delivery_attempt_payload(event_attempt, None, 1024)

    assert payload == EventDeliveryAttemptPayload(
        id=graphene.Node.to_global_id("EventDeliveryAttempt", event_attempt.pk),
        time=created_at,
        duration=None,
        status=EventDeliveryStatus.PENDING,
        next_retry=None,
        event_type=ObservabilityEventTypes.EVENT_DELIVERY_ATTEMPT,
        request=EventDeliveryAttemptRequest(
            headers=[],
        ),
        response=EventDeliveryAttemptResponse(
            headers=[],
            content_length=16,
            status_code=None,
            body=JsonTruncText("example_response", False),
        ),
        event_delivery=EventDelivery(
            id=graphene.Node.to_global_id("EventDelivery", delivery.pk),
            status=EventDeliveryStatus.PENDING,
            event_type=WebhookEventAsyncType.ANY,
            event_sync=False,
            payload=EventDeliveryPayload(
                content_length=32,
                body=JsonTruncText(
                    pretty_json(json.loads(delivery.payload.payload)), False
                ),
            ),
        ),
        webhook=Webhook(
            id=graphene.Node.to_global_id("Webhook", webhook.pk),
            name="Simple webhook",
            target_url="http://www.example.com/test",
            subscription_query=None,
        ),
        app=App(
            id=graphene.Node.to_global_id("App", app.pk), name="Sample app objects"
        ),
    )


def test_generate_event_delivery_attempt_payload_raises_truncation_error(event_attempt):
    too_small_bytes_limit = 10
    with pytest.raises(TruncationError):
        generate_event_delivery_attempt_payload(
            event_attempt, None, too_small_bytes_limit
        )


def test_generate_event_delivery_attempt_payload_raises_error_when_no_delivery(
    event_attempt,
):
    event_attempt.delivery = None
    with pytest.raises(ValueError):
        generate_event_delivery_attempt_payload(event_attempt, None, 1024)


def test_generate_event_delivery_attempt_payload_raises_error_when_no_payload(
    event_attempt,
):
    event_attempt.delivery.payload = None
    with pytest.raises(ValueError):
        generate_event_delivery_attempt_payload(event_attempt, None, 1024)


def test_generate_event_delivery_attempt_payload_with_next_retry_date(
    event_attempt,
):
    next_retry_date = datetime(1914, 6, 28, 10, 50, tzinfo=timezone.utc)
    payload = generate_event_delivery_attempt_payload(
        event_attempt, next_retry_date, 1024
    )

    assert payload["next_retry"] == next_retry_date


def test_generate_event_delivery_attempt_payload_with_non_empty_headers(
    event_attempt,
):
    headers = {"Content-Length": "19", "Content-Type": "application/json"}
    headers_list = [("Content-Length", "19"), ("Content-Type", "application/json")]
    event_attempt.request_headers = json.dumps(headers)
    event_attempt.response_headers = json.dumps(headers)

    payload = generate_event_delivery_attempt_payload(event_attempt, None, 1024)

    assert payload["request"]["headers"] == headers_list
    assert payload["response"]["headers"] == headers_list


@patch(
    "saleor.webhook.observability.payloads.SENSITIVE_GQL_FIELDS", {"Product": {"name"}}
)
def test_generate_event_delivery_attempt_payload_with_subscription_query(
    webhook,
    event_attempt,
):
    query = "subscription { event { ...on ProductUpdated { product { name } } } }"
    webhook.subscription_query = query

    payload = generate_event_delivery_attempt_payload(event_attempt, None, 1024)

    assert payload["webhook"]["subscription_query"].text == query
    assert payload["event_delivery"]["payload"]["body"].text == pretty_json(MASK)

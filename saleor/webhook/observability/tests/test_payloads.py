import datetime
import json
from unittest.mock import patch
from uuid import UUID

import graphene
import pytest
from django.http import JsonResponse

from ....core import EventDeliveryStatus
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
    concatenate_json_events,
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
    ("snake_payload", "expected_camel"),
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


@pytest.mark.parametrize(
    "events", [[], [b'{"event": "data"}'], [b'{"event": "data"}' for _ in range(10)]]
)
def test_concatenate_json_events_with_one_event(events):
    payload = json.loads(concatenate_json_events(events))
    assert isinstance(payload, list)
    assert len(payload) == len(events)


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
    ("headers", "expected"),
    [
        ({}, []),
        (None, []),
        (
            {
                "Authorization": "secret",
                "Content-Length": "19",
                "Content-Type": "application/json",
            },
            [
                ("Authorization", MASK),
                ("Content-Length", "19"),
                ("Content-Type", "application/json"),
            ],
        ),
    ],
)
def test_serialize_headers(headers, expected):
    assert serialize_headers(headers) == expected


def test_generate_api_call_payload(app, rf, gql_operation_factory, site_settings):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.request_time = datetime.datetime(1914, 6, 28, 10, 50, tzinfo=datetime.UTC)
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
    request_id = json.loads(payload)["request"]["id"]

    assert UUID(request_id, version=4)
    assert payload == dump_payload(
        ApiCallPayload(
            event_type=ObservabilityEventTypes.API_CALL,
            request=ApiCallRequest(
                id=request_id,
                method="POST",
                url=f"http://{site_settings.site.domain}/graphql",
                time=request.request_time.timestamp(),
                headers=[
                    ("Cookie", "***"),
                    ("Content-Length", "19"),
                    ("Content-Type", "application/json"),
                ],
                content_length=19,
            ),
            response=ApiCallResponse(
                headers=[
                    ("Content-Type", "application/json"),
                ],
                status_code=200,
                content_length=20,
            ),
            app=App(
                id=graphene.Node.to_global_id("App", app.pk), name="Sample app objects"
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
    )


def test_generate_api_call_payload_request_not_from_app(rf):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.app = None
    response = JsonResponse({"response": "data"})
    payload = generate_api_call_payload(request, response, [], 1024)

    assert json.loads(payload)["app"] is None


def test_generate_api_call_payload_skip_operations_when_size_limit_too_low(
    app, rf, gql_operation_factory
):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.request_time = datetime.datetime(1914, 6, 28, 10, 50, tzinfo=datetime.UTC)
    request.app = app
    response = JsonResponse({"response": "data"})
    query = "query FirstQuery { shop { name } } query SecondQuery { shop { name } }"
    result = {"data": "result A"}
    first_result = gql_operation_factory(query, "FirstQuery", None, result)
    second_result = gql_operation_factory(query, "SecondQuery", None, result)
    payload_without_operations = generate_api_call_payload(request, response, [], 1024)
    bytes_limit = len(payload_without_operations) + GQL_OPERATION_PLACEHOLDER_SIZE * 2
    operation_trunc_payload = {
        "name": {"text": "", "truncated": True},
        "operationType": "query",
        "query": {"text": "", "truncated": True},
        "result": {"text": "", "truncated": True},
        "resultInvalid": False,
    }

    payload = generate_api_call_payload(
        request, response, [first_result, second_result], bytes_limit
    )

    assert json.loads(payload)["gqlOperations"] == [operation_trunc_payload] * 2


def test_generate_api_call_payload_when_too_low_bytes_limit(app, rf):
    request = rf.post(
        "/graphql", data={"request": "data"}, content_type="application/json"
    )
    request.request_time = datetime.datetime(1914, 6, 28, 10, 50, tzinfo=datetime.UTC)
    request.app = app
    response = JsonResponse({"response": "data"})
    payload = generate_api_call_payload(request, response, [], 1024)

    with pytest.raises(TruncationError):
        generate_api_call_payload(request, response, [], len(payload) - 1)


def test_generate_event_delivery_attempt_payload(event_attempt):
    created_at = datetime.datetime(1914, 6, 28, 10, 50, tzinfo=datetime.UTC)
    event_attempt.created_at = created_at
    delivery = event_attempt.delivery
    webhook = delivery.webhook
    app = webhook.app

    payload = generate_event_delivery_attempt_payload(event_attempt, None, 1024)

    assert payload == dump_payload(
        EventDeliveryAttemptPayload(
            id=graphene.Node.to_global_id("EventDeliveryAttempt", event_attempt.pk),
            event_type=ObservabilityEventTypes.EVENT_DELIVERY_ATTEMPT,
            time=created_at,
            duration=None,
            status=EventDeliveryStatus.PENDING,
            next_retry=None,
            request=EventDeliveryAttemptRequest(
                headers=[],
            ),
            response=EventDeliveryAttemptResponse(
                headers=[],
                content_length=16,
                body=JsonTruncText("example_response", False),
                status_code=None,
            ),
            event_delivery=EventDelivery(
                id=graphene.Node.to_global_id("EventDelivery", delivery.pk),
                status=EventDeliveryStatus.PENDING,
                event_type=WebhookEventAsyncType.ANY,
                event_sync=False,
                payload=EventDeliveryPayload(
                    content_length=32,
                    body=JsonTruncText(
                        pretty_json(json.loads(delivery.payload.get_payload())), False
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
    with pytest.raises(ValueError, match="Can't generate payload."):
        generate_event_delivery_attempt_payload(event_attempt, None, 1024)


def test_generate_event_delivery_attempt_payload_raises_error_when_no_payload(
    event_attempt,
):
    event_attempt.delivery.payload = None
    with pytest.raises(ValueError, match="Can't generate payload."):
        generate_event_delivery_attempt_payload(event_attempt, None, 1024)


def test_generate_event_delivery_attempt_payload_with_next_retry_date(
    event_attempt,
):
    next_retry_date = datetime.datetime(2004, 5, 1, 0, 0, tzinfo=datetime.UTC)
    payload = generate_event_delivery_attempt_payload(
        event_attempt, next_retry_date, 1024
    )

    assert json.loads(payload)["nextRetry"] == "2004-05-01T00:00:00Z"


def test_generate_event_delivery_attempt_payload_with_non_empty_headers(event_attempt):
    headers = {"Content-Length": "19", "Content-Type": "application/json"}
    headers_list = [["Content-Length", "19"], ["Content-Type", "application/json"]]
    event_attempt.request_headers = json.dumps(headers)
    event_attempt.response_headers = json.dumps(headers)

    payload = generate_event_delivery_attempt_payload(event_attempt, None, 1024)
    payload = json.loads(payload)

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
    payload = json.loads(payload)

    assert payload["webhook"]["subscriptionQuery"]["text"] == query
    assert payload["eventDelivery"]["payload"]["body"]["text"] == pretty_json(MASK)


def test_generate_event_delivery_attempt_payload_target_url_obfuscated(
    webhook, event_attempt
):
    webhook.target_url = "http://user:password@example.com/webhooks"

    payload = generate_event_delivery_attempt_payload(event_attempt, None, 1024)
    payload = json.loads(payload)

    assert payload["webhook"]["targetUrl"] == "http://***:***@example.com/webhooks"

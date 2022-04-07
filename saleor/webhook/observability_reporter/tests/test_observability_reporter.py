from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse

from .. import (
    ApiCallResponse,
    ObservabilityError,
    api_call_context,
    gql_operation_context,
    report_event_delivery_attempt,
)
from ..payloads import generate_event_delivery_attempt_payload


@pytest.fixture
def test_request(rf):
    return rf.post("/graphql", data={"request": "data"})


@patch("saleor.webhook.observability_reporter.webhooks_for_event_exists")
@patch("saleor.webhook.observability_reporter.put_event")
def test_api_call_response_report(
    mock_webhooks_for_event_exists, mock_put_event, settings, app, test_request
):
    settings.OBSERVABILITY_ACTIVE = True
    test_request.app = app
    response = HttpResponse({"response": "data"})
    mock_webhooks_for_event_exists.return_value = True
    api_call = ApiCallResponse(request=test_request)
    api_call.response = response

    assert api_call.report() is True
    assert api_call.report() is False
    mock_put_event.assert_called_once()


@pytest.mark.count_queries(autouse=False)
@patch("saleor.webhook.observability_reporter.put_event")
def test_api_call_response_report_count_queries(
    _, settings, app, test_request, django_assert_max_num_queries, count_queries
):
    settings.OBSERVABILITY_ACTIVE = True
    test_request.app = app
    response = HttpResponse({"response": "data"})
    api_call = ApiCallResponse(request=test_request)
    api_call.response = response

    with django_assert_max_num_queries(1):
        api_call.report()


@patch("saleor.webhook.observability_reporter.put_event")
def test_api_call_response_report_when_observability_not_active(
    mock_put_event, settings, test_request
):
    settings.OBSERVABILITY_ACTIVE = False
    api_call = ApiCallResponse(request=test_request)

    assert api_call.report() is False
    mock_put_event.assert_not_called()


@patch("saleor.webhook.observability_reporter.put_event")
def test_api_call_response_report_when_request_not_from_app(
    mock_put_event, settings, test_request
):
    settings.OBSERVABILITY_ACTIVE = True
    api_call = ApiCallResponse(request=test_request)

    assert api_call.report() is False
    mock_put_event.assert_not_called()


@patch("saleor.webhook.observability_reporter.put_event")
def test_api_call_response_report_response_not_set(
    mock_put_event, settings, app, test_request
):
    settings.OBSERVABILITY_ACTIVE = True
    test_request.app = app
    api_call = ApiCallResponse(request=test_request)

    assert api_call.report() is False
    mock_put_event.assert_not_called()


@pytest.mark.parametrize("exception", [ValueError, ObservabilityError, Exception])
@patch("saleor.webhook.observability_reporter.webhooks_for_event_exists")
@patch("saleor.webhook.observability_reporter.put_event")
def test_api_call_response_catch_exception(
    mock_put_event,
    mock_webhooks_for_event_exists,
    settings,
    app,
    test_request,
    exception,
):
    settings.OBSERVABILITY_ACTIVE = True
    test_request.app = app
    response = HttpResponse({"response": "data"})
    mock_webhooks_for_event_exists.return_value = True
    api_call = ApiCallResponse(request=test_request)
    api_call.response = response
    mock_put_event.side_effect = exception

    assert api_call.report() is False


@patch("saleor.webhook.observability_reporter.put_event")
@patch(
    "saleor.webhook.observability_reporter.webhooks_for_event_exists", return_value=True
)
def test_report_event_delivery_attempt(_, mock_put_event, event_attempt):
    expected_event = generate_event_delivery_attempt_payload(event_attempt, None, 1024)

    assert report_event_delivery_attempt(event_attempt) is True
    mock_put_event.assert_called_once_with(expected_event)


@patch("saleor.webhook.observability_reporter.put_event")
def test_report_event_delivery_attempt_when_delivery_not_set(
    mock_put_event, event_attempt
):
    event_attempt.delivery = None

    assert (
        report_event_delivery_attempt(
            event_attempt,
        )
        is False
    )
    mock_put_event.assert_not_called()


@pytest.mark.parametrize("exception", [ValueError, ObservabilityError, Exception])
@patch("saleor.webhook.observability_reporter.put_event")
@patch(
    "saleor.webhook.observability_reporter.webhooks_for_event_exists", return_value=True
)
def test_report_event_delivery_attempt_catch_exception(
    _, mock_put_event, exception, event_attempt
):
    mock_put_event.side_effect = exception
    assert report_event_delivery_attempt(event_attempt) is False


def test_api_call_context(test_request):
    with api_call_context(test_request) as context_a_level_1:
        with api_call_context(test_request) as context_a_level_2:
            with api_call_context(test_request) as context_a_level_3:
                assert context_a_level_1 == context_a_level_2
                assert context_a_level_1 == context_a_level_3
                assert context_a_level_2 == context_a_level_3

    with api_call_context(test_request) as context_b_level_1:
        assert context_b_level_1 != context_a_level_1


def test_api_call_context_report_on_exit(test_request):
    context_report_mock = Mock()
    with api_call_context(test_request) as context_level_1:
        context_level_1.report = context_report_mock
        with api_call_context(test_request) as context_level_2:
            context_level_2.report()
        context_report_mock.assert_called_once()
        context_report_mock.reset_mock()
    context_report_mock.assert_called_once()


def test_gql_operation_context(test_request):
    with api_call_context(test_request) as context_level_1:
        with gql_operation_context() as operation_a_level_1:
            with gql_operation_context() as operation_a_level_2:
                assert operation_a_level_1 == operation_a_level_2
        assert context_level_1.gql_operations[0] == operation_a_level_1
        assert len(context_level_1.gql_operations) == 1


def test_gql_operation_context_multiple_operations(test_request):
    with api_call_context(test_request) as context_a_level_1:
        with gql_operation_context():
            with gql_operation_context():
                pass
        with gql_operation_context():
            with gql_operation_context():
                pass
    assert len(context_a_level_1.gql_operations) == 2

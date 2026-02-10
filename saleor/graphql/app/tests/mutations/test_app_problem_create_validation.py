import datetime

from django.utils import timezone

from .....app.error_codes import AppProblemCreateErrorCode
from .....app.models import AppProblem
from ....tests.utils import get_graphql_content

APP_PROBLEM_CREATE_MUTATION = """
    mutation AppProblemCreate($input: AppProblemCreateInput!) {
        appProblemCreate(input: $input) {
            appProblem {
                id
                message
                key
                count
                isCritical
                updatedAt
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_app_problem_create_negative_aggregation_period_fails(app_api_client, app):
    # given
    variables = {
        "input": {
            "message": "Something went wrong",
            "key": "error-1",
            "aggregationPeriod": -1,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)

    # then - Minute scalar rejects negative values at GraphQL level
    assert response.status_code == 400
    content = response.json()
    assert "errors" in content
    error_message = content["errors"][0]["message"]
    assert 'Expected type "Minute", found -1' in error_message
    assert AppProblem.objects.filter(app=app).count() == 0


def test_app_problem_create_zero_critical_threshold_fails(app_api_client, app):
    # given
    variables = {
        "input": {
            "message": "Something went wrong",
            "key": "error-1",
            "criticalThreshold": 0,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)

    # then - PositiveInt scalar rejects 0 at GraphQL level
    assert response.status_code == 400
    content = response.json()
    assert "errors" in content
    assert "PositiveInt" in content["errors"][0]["message"]
    assert AppProblem.objects.filter(app=app).count() == 0


def test_app_problem_create_negative_critical_threshold_fails(app_api_client, app):
    # given
    variables = {
        "input": {
            "message": "Something went wrong",
            "key": "error-1",
            "criticalThreshold": -5,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)

    # then - PositiveInt scalar rejects negative values at GraphQL level
    assert response.status_code == 400
    content = response.json()
    assert "errors" in content
    assert "PositiveInt" in content["errors"][0]["message"]
    assert AppProblem.objects.filter(app=app).count() == 0


def test_app_problem_create_null_aggregation_period_defaults_to_60(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="Recent problem",
        key="null-agg-key",
        count=1,
        updated_at=now - datetime.timedelta(minutes=30),
    )
    # Explicitly pass null for aggregationPeriod
    variables = {
        "input": {
            "message": "Should aggregate with default period",
            "key": "null-agg-key",
            "aggregationPeriod": None,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then - null should default to 60 minutes, so it aggregates with the existing problem
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 1
    problem = AppProblem.objects.get(app=app)
    assert problem.count == 2
    assert problem.message == "Should aggregate with default period"


def test_app_problem_create_message_too_short_fails(app_api_client, app):
    # given
    variables = {
        "input": {
            "message": "ab",  # min_length=3
            "key": "error-1",
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "message"
    assert data["errors"][0]["code"] == AppProblemCreateErrorCode.INVALID.name
    assert data["errors"][0]["message"] == "String should have at least 3 characters"
    assert AppProblem.objects.filter(app=app).count() == 0


def test_app_problem_create_message_too_long_is_truncated(app_api_client, app):
    # given
    long_message = "a" * 3000
    variables = {
        "input": {
            "message": long_message,
            "key": "error-1",
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem = AppProblem.objects.get(app=app)
    assert len(problem.message) == 2048
    assert problem.message == "a" * 2045 + "..."


def test_app_problem_create_key_too_short_fails(app_api_client, app):
    # given
    variables = {
        "input": {
            "message": "Something went wrong",
            "key": "ab",  # min_length=3
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "key"
    assert data["errors"][0]["code"] == AppProblemCreateErrorCode.INVALID.name
    assert data["errors"][0]["message"] == "String should have at least 3 characters"
    assert AppProblem.objects.filter(app=app).count() == 0


def test_app_problem_create_key_too_long_fails(app_api_client, app):
    # given
    variables = {
        "input": {
            "message": "Something went wrong",
            "key": "a" * 129,  # max_length=128
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "key"
    assert data["errors"][0]["code"] == AppProblemCreateErrorCode.INVALID.name
    assert data["errors"][0]["message"] == "String should have at most 128 characters"
    assert AppProblem.objects.filter(app=app).count() == 0


def test_app_problem_create_message_at_2048_chars_is_not_truncated(app_api_client, app):
    # given
    message = "a" * 2048
    variables = {
        "input": {
            "message": message,
            "key": "error-1",
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem = AppProblem.objects.get(app=app)
    assert problem.message == message
    assert len(problem.message) == 2048


def test_app_problem_create_key_at_max_length_succeeds(app_api_client, app):
    # given
    variables = {
        "input": {
            "message": "Something went wrong",
            "key": "a" * 128,  # exactly at max_length
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem = AppProblem.objects.get(app=app)
    assert len(problem.key) == 128

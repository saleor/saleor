import datetime

from django.utils import timezone

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
                app {
                    id
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_app_problem_create_critical_threshold_reached(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="Almost critical",
        key="crit-key",
        count=4,
        updated_at=now - datetime.timedelta(minutes=5),
    )
    variables = {
        "input": {
            "message": "Critical now",
            "key": "crit-key",
            "aggregationPeriod": 60,
            "criticalThreshold": 5,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem = AppProblem.objects.get(app=app)
    assert problem.count == 5
    assert problem.is_critical is True


def test_app_problem_create_critical_threshold_not_reached(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="Not critical yet",
        key="nc-key",
        count=2,
        updated_at=now - datetime.timedelta(minutes=5),
    )
    variables = {
        "input": {
            "message": "Still not critical",
            "key": "nc-key",
            "aggregationPeriod": 60,
            "criticalThreshold": 10,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem = AppProblem.objects.get(app=app)
    assert problem.count == 3
    assert problem.is_critical is False


def test_app_problem_create_critical_threshold_de_escalates(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="Problem",
        key="rolling-key",
        count=1,
        updated_at=now - datetime.timedelta(minutes=5),
    )

    # when - send 4 more problems with threshold=5, reaching count=5
    for i in range(4):
        variables = {
            "input": {
                "message": f"Problem {i + 2}",
                "key": "rolling-key",
                "aggregationPeriod": 60,
                "criticalThreshold": 5,
            }
        }
        response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
        get_graphql_content(response)

    # then - count=5 meets threshold=5, should be critical
    problem = AppProblem.objects.get(app=app)
    assert problem.count == 5
    assert problem.is_critical is True

    # when - send 6th problem with higher threshold=10
    variables = {
        "input": {
            "message": "Problem 6",
            "key": "rolling-key",
            "aggregationPeriod": 60,
            "criticalThreshold": 10,
        }
    }
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then - count=6 is below new threshold=10, should de-escalate
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem.refresh_from_db()
    assert problem.count == 6
    assert problem.is_critical is False


def test_app_problem_create_critical_threshold_not_reached_due_to_expired_aggregation(
    app_api_client, app, app_problem_generator
):
    # given - existing problem with count=4, threshold=5
    # but aggregation period expired, so a new problem is created instead
    now = timezone.now()
    existing = app_problem_generator(
        app,
        message="Almost critical",
        key="crit-key",
        count=4,
        updated_at=now - datetime.timedelta(minutes=120),
    )
    variables = {
        "input": {
            "message": "New occurrence",
            "key": "crit-key",
            "aggregationPeriod": 60,
            "criticalThreshold": 5,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then - a new problem is created instead of aggregating
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app, key="crit-key").count() == 2

    # old problem stays at count=4, not critical
    existing.refresh_from_db()
    assert existing.count == 4
    assert existing.is_critical is False

    # new problem starts at count=1, not critical
    new_problem = data["appProblem"]
    assert new_problem["count"] == 1
    assert new_problem["isCritical"] is False


def test_app_problem_create_critical_on_first_problem(app_api_client, app):
    # given
    variables = {
        "input": {
            "message": "Immediately critical",
            "key": "imm-crit",
            "criticalThreshold": 1,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem = AppProblem.objects.get(app=app)
    assert problem.is_critical is True
    assert problem.count == 1

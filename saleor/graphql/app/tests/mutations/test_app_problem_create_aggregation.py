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
                dismissed
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


def test_app_problem_create_aggregates_within_period(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="First occurrence",
        key="agg-key",
        count=1,
        updated_at=now - datetime.timedelta(minutes=30),
    )
    variables = {
        "input": {
            "message": "Second occurrence",
            "key": "agg-key",
            "aggregationPeriod": 60,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 1
    problem = AppProblem.objects.get(app=app)
    assert problem.count == 2
    assert problem.message == "Second occurrence"


def test_app_problem_create_new_when_period_expired(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="Old problem",
        key="exp-key",
        count=3,
        updated_at=now - datetime.timedelta(minutes=120),
    )
    variables = {
        "input": {
            "message": "New problem",
            "key": "exp-key",
            "aggregationPeriod": 60,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = AppProblem.objects.filter(app=app).order_by("created_at")
    assert problems.count() == 2
    assert problems[0].count == 3
    assert problems[0].message == "Old problem"
    assert problems[1].count == 1
    assert problems[1].message == "New problem"


def test_app_problem_create_zero_aggregation_period_always_creates_new(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="Existing",
        key="no-agg",
        count=1,
        updated_at=now - datetime.timedelta(minutes=1),
    )
    variables = {
        "input": {"message": "New one", "key": "no-agg", "aggregationPeriod": 0}
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 2


def test_app_problem_create_default_aggregation_period_aggregates(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="Recent",
        key="def-agg",
        count=1,
        updated_at=now - datetime.timedelta(minutes=30),
    )
    # No aggregationPeriod specified — defaults to 60 minutes
    variables = {"input": {"message": "Should aggregate", "key": "def-agg"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 1
    problem = AppProblem.objects.get(app=app)
    assert problem.count == 2
    assert problem.message == "Should aggregate"


def test_app_problem_create_dismissed_problem_not_aggregated(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="Dismissed one",
        key="dis-key",
        count=5,
        updated_at=now - datetime.timedelta(minutes=5),
        dismissed=True,
    )
    variables = {
        "input": {
            "message": "Fresh problem",
            "key": "dis-key",
            "aggregationPeriod": 60,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 2
    new_problem = AppProblem.objects.filter(app=app, dismissed=False).get()
    assert new_problem.count == 1
    assert new_problem.message == "Fresh problem"


def test_app_problem_create_message_updates_on_aggregation(
    app_api_client, app, app_problem_generator
):
    # given
    now = timezone.now()
    app_problem_generator(
        app,
        message="Original message",
        key="msg-key",
        count=1,
        updated_at=now - datetime.timedelta(minutes=5),
    )
    variables = {
        "input": {
            "message": "Updated message",
            "key": "msg-key",
            "aggregationPeriod": 60,
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem = AppProblem.objects.get(app=app)
    assert problem.message == "Updated message"
    assert problem.count == 2

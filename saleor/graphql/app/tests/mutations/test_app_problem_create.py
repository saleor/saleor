import datetime

from django.utils import timezone

from .....app.models import AppProblem
from ....tests.utils import assert_no_permission, get_graphql_content

APP_PROBLEM_CREATE_MUTATION = """
    mutation AppProblemCreate($input: AppProblemCreateInput!) {
        appProblemCreate(input: $input) {
            app {
                id
                problems {
                    id
                    message
                    key
                    count
                    isCritical
                    dismissed
                    updatedAt
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


def test_app_problem_create(app_api_client, app):
    # given
    variables = {"input": {"message": "Something went wrong", "key": "error-1"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["message"] == "Something went wrong"
    assert problems[0]["key"] == "error-1"
    assert problems[0]["count"] == 1
    assert problems[0]["isCritical"] is False
    assert problems[0]["dismissed"] is False

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.message == "Something went wrong"
    assert db_problem.key == "error-1"
    assert db_problem.count == 1


def test_app_problem_create_aggregates_within_period(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.create(
        app=app,
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


def test_app_problem_create_new_when_period_expired(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.create(
        app=app,
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
    assert AppProblem.objects.filter(app=app).count() == 2


def test_app_problem_create_critical_threshold_reached(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.create(
        app=app,
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


def test_app_problem_create_critical_threshold_not_reached(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.create(
        app=app,
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


def test_app_problem_create_zero_aggregation_period_always_creates_new(
    app_api_client, app
):
    # given
    now = timezone.now()
    AppProblem.objects.create(
        app=app,
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


def test_app_problem_create_default_aggregation_period_aggregates(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.create(
        app=app,
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


def test_app_problem_create_limit_eviction(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.bulk_create(
        [
            AppProblem(
                app=app,
                message=f"Problem {i}",
                key=f"key-{i}",
                updated_at=now,
            )
            for i in range(AppProblem.MAX_PROBLEMS_PER_APP)
        ]
    )
    oldest_id = AppProblem.objects.filter(app=app).order_by("created_at").first().id
    variables = {"input": {"message": "One more", "key": "new-key"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == AppProblem.MAX_PROBLEMS_PER_APP
    assert not AppProblem.objects.filter(id=oldest_id).exists()
    assert AppProblem.objects.filter(app=app, key="new-key").exists()


def test_app_problem_create_dismissed_problem_not_aggregated(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.create(
        app=app,
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


def test_app_problem_create_message_updates_on_aggregation(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.create(
        app=app,
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


def test_app_problem_create_by_staff_user_fails(
    staff_api_client, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"input": {"message": "Something went wrong", "key": "err"}}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_app_problem_create_critical_threshold_de_escalates(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.create(
        app=app,
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

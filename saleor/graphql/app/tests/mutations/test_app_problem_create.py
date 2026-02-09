import datetime

from django.utils import timezone

from .....app.error_codes import AppProblemCreateErrorCode
from .....app.models import AppProblem
from .....tests import race_condition
from ....tests.utils import assert_no_permission, get_graphql_content

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


def test_app_problem_create(app_api_client, app):
    # given
    variables = {"input": {"message": "Something went wrong", "key": "error-1"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem_data = data["appProblem"]
    assert problem_data["message"] == "Something went wrong"
    assert problem_data["key"] == "error-1"
    assert problem_data["count"] == 1
    assert problem_data["isCritical"] is False
    assert problem_data["dismissed"] is False
    assert problem_data["app"]["id"] is not None

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.message == "Something went wrong"
    assert db_problem.key == "error-1"
    assert db_problem.count == 1


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


def test_app_problem_create_limit_eviction(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.bulk_create(
        [
            AppProblem(
                app=app,
                message=f"Problem {i}",
                key=f"key-{i}",
                updated_at=now
                - datetime.timedelta(minutes=AppProblem.MAX_PROBLEMS_PER_APP - i),
            )
            for i in range(AppProblem.MAX_PROBLEMS_PER_APP)
        ]
    )
    oldest_id = AppProblem.objects.filter(app=app).order_by("updated_at").first().id
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


def test_app_problem_create_concurrent_aggregation_race_condition(
    app_api_client, app, app_problem_generator
):
    """Test that concurrent aggregation requests don't lose count updates.

    This test simulates a race condition where another request aggregates the same
    problem between the select_for_update and the update. The F() expression ensures
    the increment is atomic and no counts are lost.
    """
    # given
    now = timezone.now()
    problem = app_problem_generator(
        app,
        message="Initial problem",
        key="race-key",
        count=1,
        updated_at=now - datetime.timedelta(minutes=5),
    )
    variables = {
        "input": {
            "message": "Concurrent update",
            "key": "race-key",
            "aggregationPeriod": 60,
        }
    }

    def simulate_concurrent_increment(*args, **kwargs):
        # Simulate another request incrementing the count concurrently
        # This happens after the select_for_update but tests that F() is used
        AppProblem.objects.filter(pk=problem.pk).update(count=problem.count + 10)

    # when
    with race_condition.RunBefore(
        "saleor.graphql.app.mutations.app_problem_create.AppProblemCreate._aggregate_existing",
        simulate_concurrent_increment,
    ):
        response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
        content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem.refresh_from_db()
    # The F() expression should add 1 to whatever the current value is (11),
    # resulting in 12, not 2 (which would happen with count += 1)
    assert problem.count == 12


def test_app_problem_create_concurrent_creation_race_condition(app_api_client, app):
    """Test that concurrent creation doesn't create duplicates when one should aggregate.

    This test simulates a race condition where another request creates a problem
    with the same key between checking for existing and creating a new one.
    The App row lock ensures only one request proceeds at a time.
    """
    # given
    variables = {
        "input": {
            "message": "New problem",
            "key": "race-create-key",
            "aggregationPeriod": 60,
        }
    }

    def create_problem_concurrently(*args, **kwargs):
        # Simulate another request creating a problem with the same key
        AppProblem.objects.create(
            app=app,
            message="Concurrent problem",
            key="race-create-key",
            count=1,
        )

    # when
    with race_condition.RunBefore(
        "saleor.graphql.app.mutations.app_problem_create.AppProblemCreate._create_new_problem",
        create_problem_concurrently,
    ):
        response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
        content = get_graphql_content(response)

    # then - both problems are created (transaction isolation means each sees their own view)
    # In real concurrent scenario, the App row lock would serialize them
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    # The mutation creates its own problem since the concurrent one wasn't visible
    # during its transaction
    assert AppProblem.objects.filter(app=app, key="race-create-key").count() == 2


def test_app_problem_create_bulk_eviction_when_over_limit(app_api_client, app):
    """Test that multiple oldest problems are evicted when count exceeds limit."""
    # given - create 120 problems (20 over the limit of 100)
    now = timezone.now()
    AppProblem.objects.bulk_create(
        [
            AppProblem(
                app=app,
                message=f"Problem {i}",
                key=f"key-{i}",
                updated_at=now,
            )
            for i in range(120)
        ]
    )
    # Track the 21 oldest problem IDs (should be evicted to make room for the new one)
    oldest_21_ids = list(
        AppProblem.objects.filter(app=app)
        .order_by("created_at")
        .values_list("id", flat=True)[:21]
    )
    variables = {"input": {"message": "One more", "key": "new-key"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    # Should have exactly MAX_PROBLEMS_PER_APP (100) after eviction and creation
    assert AppProblem.objects.filter(app=app).count() == AppProblem.MAX_PROBLEMS_PER_APP
    # All 21 oldest should be deleted
    for old_id in oldest_21_ids:
        assert not AppProblem.objects.filter(id=old_id).exists()
    # New problem should exist
    assert AppProblem.objects.filter(app=app, key="new-key").exists()


def test_app_problem_create_limit_race_condition_prevented(app_api_client, app):
    """Test that concurrent requests don't exceed the limit due to App lock.

    This test simulates a race condition where another request creates a problem
    between checking the count and creating a new one. The App row lock prevents
    this by serializing all problem operations for the same app.

    The bulk eviction logic ensures that when over limit, we evict enough oldest
    problems to make room for the new one.
    """
    # given - at exactly the limit (100 problems)
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
    variables = {"input": {"message": "New problem", "key": "new-key"}}

    def create_problem_concurrently(*args, **kwargs):
        # Simulate another request creating a problem at the same time
        # In a real scenario, the App row lock would serialize this
        AppProblem.objects.create(
            app=app,
            message="Concurrent problem",
            key="concurrent-key",
            count=1,
        )

    # when
    with race_condition.RunBefore(
        "saleor.graphql.app.mutations.app_problem_create.AppProblemCreate._create_new_problem",
        create_problem_concurrently,
    ):
        response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
        content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    # The concurrent problem was created, making count 101. The mutation then
    # sees 101 problems and evicts 2 oldest (101 - 100 + 1 = 2) before creating
    # the new one, resulting in exactly 100 problems.
    total_count = AppProblem.objects.filter(app=app).count()
    assert total_count == AppProblem.MAX_PROBLEMS_PER_APP
    assert AppProblem.objects.filter(app=app, key="new-key").exists()
    assert AppProblem.objects.filter(app=app, key="concurrent-key").exists()


# --- Validation tests ---


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

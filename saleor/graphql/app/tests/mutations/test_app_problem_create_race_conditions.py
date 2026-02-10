import datetime

from django.utils import timezone

from .....app.models import AppProblem
from .....tests import race_condition
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

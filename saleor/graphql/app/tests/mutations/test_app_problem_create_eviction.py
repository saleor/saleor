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

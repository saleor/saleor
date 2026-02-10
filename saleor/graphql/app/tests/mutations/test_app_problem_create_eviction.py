import datetime
from unittest.mock import patch

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
            }
            errors {
                field
                code
                message
            }
        }
    }
"""

MOCKED_MAX = 2


@patch.object(AppProblem, "MAX_PROBLEMS_PER_APP", MOCKED_MAX)
def test_app_problem_create_limit_eviction(app_api_client, app):
    # given
    now = timezone.now()
    AppProblem.objects.bulk_create(
        [
            AppProblem(
                app=app,
                message=f"Problem {i}",
                key=f"key-{i}",
                updated_at=now - datetime.timedelta(minutes=MOCKED_MAX - i),
            )
            for i in range(MOCKED_MAX)
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
    assert AppProblem.objects.filter(app=app).count() == MOCKED_MAX
    assert not AppProblem.objects.filter(id=oldest_id).exists()
    assert AppProblem.objects.filter(app=app, key="new-key").exists()


@patch.object(AppProblem, "MAX_PROBLEMS_PER_APP", MOCKED_MAX)
def test_app_problem_create_bulk_eviction_when_over_limit(app_api_client, app):
    """Test that multiple oldest problems are evicted when count exceeds limit."""
    # given - create 4 problems (2 over the mocked limit of 2)
    over_limit = MOCKED_MAX + 2
    now = timezone.now()
    AppProblem.objects.bulk_create(
        [
            AppProblem(
                app=app,
                message=f"Problem {i}",
                key=f"key-{i}",
                updated_at=now,
            )
            for i in range(over_limit)
        ]
    )
    # Track the 3 oldest problem IDs (should be evicted to make room for the new one)
    evict_count = over_limit - MOCKED_MAX + 1
    oldest_ids = list(
        AppProblem.objects.filter(app=app)
        .order_by("created_at")
        .values_list("id", flat=True)[:evict_count]
    )
    variables = {"input": {"message": "One more", "key": "new-key"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == MOCKED_MAX
    for old_id in oldest_ids:
        assert not AppProblem.objects.filter(id=old_id).exists()
    assert AppProblem.objects.filter(app=app, key="new-key").exists()

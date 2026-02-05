import pytest
from django.utils import timezone

from ...models import AppProblem


@pytest.fixture
def app_problem_generator():
    def create_problem(
        app,
        key="test-key",
        message="Test problem",
        count=1,
        is_critical=False,
        dismissed=False,
        dismissed_by_user=None,
        updated_at=None,
    ):
        if updated_at is None:
            updated_at = timezone.now()
        return AppProblem.objects.create(
            app=app,
            message=message,
            key=key,
            count=count,
            is_critical=is_critical,
            updated_at=updated_at,
            dismissed=dismissed,
            dismissed_by_user=dismissed_by_user,
        )

    return create_problem

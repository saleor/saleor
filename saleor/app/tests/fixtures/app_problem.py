from datetime import datetime

import pytest
from django.utils import timezone

from ....account.models import User
from ...models import App, AppProblem


@pytest.fixture
def app_problem_generator():
    def create_problem(
        app: App,
        key: str = "test-key",
        message: str = "Test problem",
        count: int = 1,
        is_critical: bool = False,
        dismissed: bool = False,
        dismissed_by_user: User | None = None,
        updated_at: datetime | None = None,
    ) -> AppProblem:
        if updated_at is None:
            updated_at = timezone.now()

        dismissed_by_user_email = None
        if dismissed_by_user is not None:
            dismissed_by_user_email = dismissed_by_user.email

        problem = AppProblem.objects.create(
            app=app,
            message=message,
            key=key,
            count=count,
            is_critical=is_critical,
            dismissed=dismissed,
            dismissed_by_user_email=dismissed_by_user_email,
            dismissed_by_user=dismissed_by_user,
        )
        # Use .update() to set specific updated_at for testing since auto_now=True
        # ignores values passed to create/save
        if updated_at is not None:
            AppProblem.objects.filter(pk=problem.pk).update(updated_at=updated_at)
            problem.refresh_from_db()
        return problem

    return create_problem

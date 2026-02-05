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

        return AppProblem.objects.create(
            app=app,
            message=message,
            key=key,
            count=count,
            is_critical=is_critical,
            updated_at=updated_at,
            dismissed=dismissed,
            dismissed_by_user_email=dismissed_by_user_email,
            dismissed_by_user=dismissed_by_user,
        )

    return create_problem

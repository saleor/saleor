import datetime

import graphene
from django.utils import timezone

from ....app.models import AppProblem
from ....core.exceptions import PermissionDenied
from ....permission.auth_filters import AuthorizationFilters
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import Error
from ..enums import AppProblemCreateErrorCode
from ..types import App


class AppProblemCreateError(Error):
    code = AppProblemCreateErrorCode(description="The error code.", required=True)


class AppProblemCreateInput(graphene.InputObjectType):
    message = graphene.String(
        required=True, description="The problem message to display."
    )
    key = graphene.String(
        required=True,
        description="Key identifying the type of problem.",
    )
    critical_threshold = graphene.Int(
        required=False,
        description=(
            "If set, the problem becomes critical when count reaches this value."
        ),
    )
    aggregation_period = graphene.Int(
        required=False,
        default_value=60,
        description=(
            "Time window in minutes for aggregating problems with the same key. "
            "Defaults to 60. If 0, a new problem is always created."
        ),
    )


class AppProblemCreate(BaseMutation):
    app = graphene.Field(App, description="The app with the new problem.")

    class Arguments:
        input = AppProblemCreateInput(
            required=True, description="Fields required to create an app problem."
        )

    class Meta:
        description = "Add a problem to the calling app." + ADDED_IN_322
        doc_category = DOC_CATEGORY_APPS
        permissions = (AuthorizationFilters.AUTHENTICATED_APP,)
        error_type_class = AppProblemCreateError

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        app = info.context.app
        if not app:
            raise PermissionDenied(permissions=[AuthorizationFilters.AUTHENTICATED_APP])

        input_data = data["input"]
        key = input_data["key"]
        message = input_data["message"]
        critical_threshold = input_data.get("critical_threshold")
        aggregation_period = input_data.get("aggregation_period", 60)

        now = timezone.now()

        existing = (
            AppProblem.objects.filter(app=app, key=key, dismissed=False)
            .order_by("-updated_at")
            .first()
        )

        if existing is not None and aggregation_period > 0:
            cutoff = now - datetime.timedelta(minutes=aggregation_period)
            if existing.updated_at >= cutoff:
                existing.count += 1
                existing.updated_at = now
                existing.message = message
                if (
                    critical_threshold is not None
                    and existing.count >= critical_threshold
                ):
                    existing.is_critical = True
                existing.save(
                    update_fields=[
                        "count",
                        "updated_at",
                        "message",
                        "is_critical",
                    ]
                )
                return AppProblemCreate(app=app)

        # Create a new problem
        total_count = AppProblem.objects.filter(app=app).count()
        if total_count >= AppProblem.MAX_PROBLEMS_PER_APP:
            AppProblem.objects.filter(app=app).order_by("created_at").first().delete()

        is_critical = critical_threshold is not None and 1 >= critical_threshold
        AppProblem.objects.create(
            app=app,
            message=message,
            key=key,
            count=1,
            updated_at=now,
            is_critical=is_critical,
        )
        return AppProblemCreate(app=app)

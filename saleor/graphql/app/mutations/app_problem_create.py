import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....app.error_codes import AppErrorCode
from ....app.models import AppProblem, AppProblemSeverity, AppProblemType
from ....core.exceptions import PermissionDenied
from ....permission.auth_filters import AuthorizationFilters
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import AppError
from ..enums import AppProblemSeverityEnum
from ..types import App


class AppProblemCreateInput(graphene.InputObjectType):
    message = graphene.String(
        required=True, description="The problem message to display."
    )
    aggregate = graphene.String(
        required=False,
        description="Grouping key for this problem. Used to clear related problems.",
    )
    severity = AppProblemSeverityEnum(
        required=False,
        description="Severity of the problem. Defaults to ERROR.",
    )
    key = graphene.String(
        required=False,
        description=(
            "Optional deduplication key. If a problem with this key already exists, "
            "creation is skipped unless `force` is true."
        ),
    )
    force = graphene.Boolean(
        required=False,
        description=(
            "If true and a problem with the same `key` exists, overwrite it "
            "with new message, severity, and timestamp. Defaults to false."
        ),
    )


class AppProblemCreate(BaseMutation):
    app = graphene.Field(App, description="The app with the new problem.")

    class Arguments:
        input = AppProblemCreateInput(
            required=True, description="Fields required to create an app problem."
        )

    class Meta:
        description = (
            "Add a problem to the calling app. OWN problem type will be created"
            + ADDED_IN_322
        )
        doc_category = DOC_CATEGORY_APPS
        permissions = (AuthorizationFilters.AUTHENTICATED_APP,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        app = info.context.app
        if not app:
            raise PermissionDenied(permissions=[AuthorizationFilters.AUTHENTICATED_APP])

        input_data = data["input"]
        key = input_data.get("key")
        severity = input_data.get("severity", AppProblemSeverity.ERROR)

        if key is not None:
            existing = AppProblem.objects.filter(app=app, key=key).first()
            if existing:
                force = input_data.get("force", False)
                if force:
                    AppProblem.objects.filter(pk=existing.pk).update(
                        message=input_data["message"],
                        severity=severity,
                        aggregate=input_data.get("aggregate", ""),
                        created_at=timezone.now(),
                    )
                return AppProblemCreate(app=app)

        current_count = AppProblem.objects.filter(app=app).count()
        if current_count >= AppProblem.MAX_PROBLEMS_PER_APP:
            raise ValidationError(
                {
                    "input": ValidationError(
                        f"App has reached the maximum number of problems "
                        f"({AppProblem.MAX_PROBLEMS_PER_APP}).",
                        code=AppErrorCode.INVALID.value,
                    )
                }
            )
        AppProblem.objects.create(
            app=app,
            type=AppProblemType.OWN,
            message=input_data["message"],
            aggregate=input_data.get("aggregate", ""),
            severity=severity,
            key=key,
        )
        return AppProblemCreate(app=app)

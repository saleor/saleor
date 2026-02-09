import datetime
from typing import Annotated, Any

import graphene
from django.db.models import F
from django.utils import timezone
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from pydantic import ValidationError as PydanticValidationError

from ....app.error_codes import (
    AppProblemCreateErrorCode as AppProblemCreateErrorCodeEnum,
)
from ....app.lock_objects import app_qs_select_for_update
from ....app.models import App as AppModel
from ....app.models import AppProblem
from ....core.tracing import traced_atomic_transaction
from ....permission.auth_filters import AuthorizationFilters
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.scalars import Minute, PositiveInt
from ...core.types import Error
from ...error import pydantic_to_validation_error
from ..enums import AppProblemCreateErrorCode
from ..types import App


class AppProblemCreateError(Error):
    code = AppProblemCreateErrorCode(description="The error code.", required=True)


class AppProblemCreateValidatedInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    message: Annotated[str, StringConstraints(min_length=3)]
    key: Annotated[str, StringConstraints(min_length=3, max_length=128)]
    # No threshold - will never escalate to critical if not set by App itself
    critical_threshold: Annotated[int, Field(ge=1)] | None = None
    # Minutes
    aggregation_period: Annotated[int, Field(ge=0)] = 60

    @field_validator("message", mode="after")
    @classmethod
    def truncate_message(cls, v: str) -> str:
        """Truncate message to 2048 characters including '...' suffix if too long."""
        if len(v) > 2048:
            return v[:2045] + "..."
        return v

    @field_validator("aggregation_period", mode="before")
    @classmethod
    def default_aggregation_period(cls, v: int | None) -> int:
        """Accept null from GraphQL and map to default (60)."""
        if v is None:
            return 60
        return v


class AppProblemCreateInput(graphene.InputObjectType):
    message = graphene.String(
        required=True,
        description=(
            "The problem message to display. Must be at least 3 characters. "
            "Messages longer than 2048 characters will be truncated to 2048 "
            "characters with '...' suffix."
        ),
    )
    key = graphene.String(
        required=True,
        description=(
            "Key identifying the type of problem. App can add multiple problems under "
            "the same key, to merge them together or delete them in batch. "
            "Must be between 3 and 128 characters."
        ),
    )
    critical_threshold = PositiveInt(
        required=False,
        description=(
            "If set, the problem becomes critical when count reaches this value. If sent again with higher value than already counted, problem can be de-escalated."
        ),
    )
    aggregation_period = Minute(
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
    def perform_mutation(
        cls, _root: None, info: ResolveInfo, /, **data: Any
    ) -> "AppProblemCreate":
        app = info.context.app
        assert app is not None
        input_data = data["input"]
        try:
            validated = AppProblemCreateValidatedInput(**input_data)
        except PydanticValidationError as exc:
            raise pydantic_to_validation_error(
                exc, error_code=AppProblemCreateErrorCodeEnum.INVALID.value
            ) from exc

        now = timezone.now()

        with traced_atomic_transaction():
            # Lock the App row to serialize all problem operations for this app
            # At this point it trades performance for correctness
            # If we need to improve performance, we can skip locking entire app row and
            # schedule a cleanup task for > 100 items
            app_qs_select_for_update().filter(pk=app.pk).first()

            existing = (
                AppProblem.objects.filter(app=app, key=validated.key, dismissed=False)
                .order_by("-updated_at")
                .first()
            )

            if not existing:
                cls._create_new_problem(app, validated, now)

                return AppProblemCreate(app=app)

            # Flow for existing / update
            aggregation_enabled = validated.aggregation_period > 0
            cutoff = now - datetime.timedelta(minutes=validated.aggregation_period)
            within_aggregation_window = (
                aggregation_enabled and existing.updated_at >= cutoff
            )

            if not within_aggregation_window:
                cls._create_new_problem(app, validated, now)
                return AppProblemCreate(app=app)

            cls._aggregate_existing(existing, validated, now)
            return AppProblemCreate(app=app)

    @classmethod
    def _aggregate_existing(
        cls,
        existing: AppProblem,
        validated: AppProblemCreateValidatedInput,
        now: datetime.datetime,
    ) -> None:
        new_count = existing.count + 1
        is_critical = bool(
            validated.critical_threshold and new_count >= validated.critical_threshold
        )

        AppProblem.objects.filter(pk=existing.pk).update(
            count=F("count") + 1,
            updated_at=now,
            message=validated.message,
            is_critical=is_critical,
        )

    @classmethod
    def _create_new_problem(
        cls,
        app: AppModel,
        validated: AppProblemCreateValidatedInput,
        now: datetime.datetime,
    ) -> None:
        total_count = AppProblem.objects.filter(app=app).count()
        # +1 accounts for the new problem we're about to create
        excess_count = total_count - AppProblem.MAX_PROBLEMS_PER_APP + 1

        if excess_count > 0:
            oldest_pks = list(
                AppProblem.objects.filter(app=app)
                .order_by("updated_at")
                .values_list("pk", flat=True)[:excess_count]
            )
            if oldest_pks:
                AppProblem.objects.filter(pk__in=oldest_pks).delete()

        immediately_critical = bool(
            validated.critical_threshold and validated.critical_threshold <= 1
        )

        AppProblem.objects.create(
            app=app,
            message=validated.message,
            key=validated.key,
            count=1,
            is_critical=immediately_critical,
        )

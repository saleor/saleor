import datetime
from typing import Annotated, Any

import graphene
from django.db.models import F
from django.utils import timezone
from pydantic import BaseModel, ConfigDict, StringConstraints

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
from ..enums import AppProblemCreateErrorCode
from ..types import App


class AppProblemCreateError(Error):
    code = AppProblemCreateErrorCode(description="The error code.", required=True)


class AppProblemCreateValidatedInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    message: Annotated[str, StringConstraints(min_length=3, max_length=2048)]
    key: Annotated[str, StringConstraints(min_length=3, max_length=128)]
    # No threshold - will never escalate to critical if not set by App itself
    critical_threshold: int | None = None
    # Minutes
    aggregation_period: int = 60


class AppProblemCreateInput(graphene.InputObjectType):
    message = graphene.String(
        required=True, description="The problem message to display."
    )
    key = graphene.String(
        required=True,
        description="Key identifying the type of problem.",
    )
    critical_threshold = PositiveInt(
        required=False,
        description=(
            "If set, the problem becomes critical when count reaches this value."
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
        validated = AppProblemCreateValidatedInput(
            message=input_data["message"],
            key=input_data["key"],
            critical_threshold=input_data.get("critical_threshold"),
            aggregation_period=input_data.get("aggregation_period"),
        )

        now = timezone.now()

        with traced_atomic_transaction():
            # Lock the App row to serialize all problem operations for this app
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
        # Can be calculated here, the update itself happens in db and this is needed only to
        # calculate is_critical, so even if count is actually higher due to thread race, is_critical will
        # be still true
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
                .order_by("created_at")
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
            updated_at=now,
            is_critical=immediately_critical,
        )

from typing import Annotated, Any, cast

import graphene
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from pydantic import ValidationError as PydanticValidationError

from ....app.error_codes import (
    AppProblemCreateErrorCode as AppProblemCreateErrorCodeEnum,
)
from ....app.models import App as AppModel
from ....app.problems import create_or_update_problem
from ....permission.auth_filters import AuthorizationFilters
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.scalars import Minute, PositiveInt
from ...core.types import Error
from ...error import pydantic_to_validation_error
from ..enums import AppProblemCreateErrorCode
from ..types import AppProblem as AppProblemType


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
            "If set, the problem becomes critical when count reaches this value. "
            "If sent again with higher value than already counted, problem can be de-escalated."
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
    app_problem = graphene.Field(
        AppProblemType, description="The created or updated app problem."
    )

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
        app = cast(AppModel, info.context.app)
        input_data = data["input"]
        try:
            validated = AppProblemCreateValidatedInput(**input_data)
        except PydanticValidationError as exc:
            raise pydantic_to_validation_error(
                exc, default_error_code=AppProblemCreateErrorCodeEnum.INVALID.value
            ) from exc

        problem = create_or_update_problem(
            app.pk,
            message=validated.message,
            key=validated.key,
            critical_threshold=validated.critical_threshold,
            aggregation_period=validated.aggregation_period,
        )
        return AppProblemCreate(app_problem=problem)

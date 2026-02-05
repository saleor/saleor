from typing import Any

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q

from ....app.error_codes import (
    AppProblemDismissErrorCode as AppProblemDismissErrorCodeEnum,
)
from ....app.models import App as AppModel
from ....app.models import AppProblem
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AppPermission
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, Error, NonNullList
from ...core.utils import from_global_id_or_error
from ...utils import get_user_or_app_from_context
from ..enums import AppProblemDismissErrorCode
from ..types import App


class AppProblemDismissError(Error):
    code = AppProblemDismissErrorCode(description="The error code.", required=True)


class AppProblemDismissByAppInput(BaseInputObjectType):
    """Input for app callers to dismiss their own problems."""

    ids = NonNullList(
        graphene.ID,
        required=False,
        description="List of problem IDs to dismiss. Cannot be combined with keys.",
    )
    keys = NonNullList(
        graphene.String,
        required=False,
        description="List of problem keys to dismiss. Cannot be combined with ids.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_APPS


class AppProblemDismissByUserWithIdsInput(BaseInputObjectType):
    """Input for staff/user callers to dismiss problems by IDs."""

    ids = NonNullList(
        graphene.ID,
        required=True,
        description="List of problem IDs to dismiss.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_APPS


class AppProblemDismissByUserWithKeysInput(BaseInputObjectType):
    """Input for staff/user callers to dismiss problems by keys."""

    keys = NonNullList(
        graphene.String,
        required=True,
        description="List of problem keys to dismiss.",
    )
    app = graphene.ID(
        required=True,
        description="ID of the app whose problems to dismiss.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_APPS


class AppProblemDismissInput(BaseInputObjectType):
    """Input for dismissing app problems. Only one can be specified."""

    by_app = graphene.Field(
        AppProblemDismissByAppInput,
        description="For app callers only - dismiss own problems.",
    )
    by_user_with_ids = graphene.Field(
        AppProblemDismissByUserWithIdsInput,
        description="For staff/user callers - dismiss problems by IDs.",
    )
    by_user_with_keys = graphene.Field(
        AppProblemDismissByUserWithKeysInput,
        description="For staff/user callers - dismiss problems by keys for specified app.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_APPS


class AppProblemDismiss(BaseMutation):
    class Arguments:
        input = AppProblemDismissInput(
            required=True,
            description="Input for dismissing app problems.",
        )

    class Meta:
        description = "Dismiss problems for an app." + ADDED_IN_322
        doc_category = DOC_CATEGORY_APPS
        permissions = (
            AppPermission.MANAGE_APPS,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        error_type_class = AppProblemDismissError

    @classmethod
    def perform_mutation(
        cls, _root: None, info: ResolveInfo, /, **data: Any
    ) -> "AppProblemDismiss":
        caller_app = info.context.app
        input_data = data.get("input", {})

        by_app = input_data.get("by_app")
        by_user_with_ids = input_data.get("by_user_with_ids")
        by_user_with_keys = input_data.get("by_user_with_keys")

        cls._validate_top_level(by_app, by_user_with_ids, by_user_with_keys, caller_app)

        if by_app is not None:
            assert caller_app is not None  # validated in _validate_top_level
            cls._validate_by_app_input(by_app)
            cls._dismiss_for_app_caller(by_app, caller_app)
        elif by_user_with_ids is not None:
            cls._dismiss_by_ids_for_user(info, by_user_with_ids["ids"])
        else:
            cls._dismiss_by_keys_for_user(
                info, by_user_with_keys["keys"], by_user_with_keys["app"]
            )

        return AppProblemDismiss()

    @classmethod
    def _validate_top_level(
        cls,
        by_app: dict | None,
        by_user_with_ids: dict | None,
        by_user_with_keys: dict | None,
        caller_app: AppModel | None,
    ) -> None:
        """Validate top-level input: exactly one branch, matching caller type."""
        provided = [
            by_app is not None,
            by_user_with_ids is not None,
            by_user_with_keys is not None,
        ]
        count = sum(provided)

        if count == 0:
            raise ValidationError(
                {
                    "input": ValidationError(
                        "Must provide one of 'byApp', 'byUserWithIds', or 'byUserWithKeys'.",
                        code=AppProblemDismissErrorCodeEnum.REQUIRED.value,
                    )
                }
            )

        if count > 1:
            raise ValidationError(
                {
                    "input": ValidationError(
                        "Must provide exactly one of 'byApp', 'byUserWithIds', or 'byUserWithKeys'.",
                        code=AppProblemDismissErrorCodeEnum.INVALID.value,
                    )
                }
            )

        # Validate caller-type matching
        is_app_caller = caller_app is not None
        uses_by_app = by_app is not None
        uses_by_user = by_user_with_ids is not None or by_user_with_keys is not None

        if uses_by_app and not is_app_caller:
            raise ValidationError(
                {
                    "byApp": ValidationError(
                        "Only app callers can use 'byApp'.",
                        code=AppProblemDismissErrorCodeEnum.INVALID.value,
                    )
                }
            )

        if uses_by_user and is_app_caller:
            field = "byUserWithIds" if by_user_with_ids else "byUserWithKeys"
            raise ValidationError(
                {
                    field: ValidationError(
                        "App callers cannot use this input. Use 'byApp' instead.",
                        code=AppProblemDismissErrorCodeEnum.INVALID.value,
                    )
                }
            )

    @classmethod
    def _validate_by_app_input(cls, by_app: dict) -> None:
        """Validate byApp input has exactly one of ids or keys."""
        ids = by_app.get("ids")
        keys = by_app.get("keys")

        if ids and keys:
            raise ValidationError(
                {
                    "byApp": ValidationError(
                        "Cannot specify both 'ids' and 'keys'.",
                        code=AppProblemDismissErrorCodeEnum.INVALID.value,
                    )
                }
            )

        if not ids and not keys:
            raise ValidationError(
                {
                    "byApp": ValidationError(
                        "Must provide either 'ids' or 'keys'.",
                        code=AppProblemDismissErrorCodeEnum.REQUIRED.value,
                    )
                }
            )

    @classmethod
    def _dismiss_for_app_caller(
        cls,
        by_app: dict,
        caller_app: AppModel,
    ) -> None:
        """Dismiss problems for an app caller (can only dismiss own problems)."""
        ids = by_app.get("ids")
        keys = by_app.get("keys")

        # Validate that all provided IDs belong to the caller app
        if ids:
            problem_pks = cls._parse_problem_ids(ids)
            other_app_problems = AppProblem.objects.filter(pk__in=problem_pks).exclude(
                app=caller_app
            )
            if other_app_problems.exists():
                raise ValidationError(
                    {
                        "ids": ValidationError(
                            "Cannot dismiss problems belonging to other apps.",
                            code=AppProblemDismissErrorCodeEnum.INVALID.value,
                        )
                    }
                )

        filter_q = cls._build_filter_query(ids, keys)
        AppProblem.objects.filter(filter_q, app=caller_app, dismissed=False).update(
            dismissed=True
        )

    @classmethod
    def _dismiss_by_ids_for_user(
        cls,
        info: ResolveInfo,
        ids: list[str],
    ) -> None:
        """Dismiss problems by IDs for a user/staff caller."""
        requestor = get_user_or_app_from_context(info.context)
        problem_pks = cls._parse_problem_ids(ids)

        AppProblem.objects.filter(pk__in=problem_pks, dismissed=False).update(
            dismissed=True, dismissed_by_user=requestor
        )

    @classmethod
    def _dismiss_by_keys_for_user(
        cls,
        info: ResolveInfo,
        keys: list[str],
        app_id: str,
    ) -> None:
        """Dismiss problems by keys for a user/staff caller."""
        requestor = get_user_or_app_from_context(info.context)
        target_app = cls.get_node_or_error(info, app_id, field="app", only_type=App)

        AppProblem.objects.filter(app=target_app, key__in=keys, dismissed=False).update(
            dismissed=True, dismissed_by_user=requestor
        )

    @classmethod
    def _build_filter_query(cls, ids: list[str] | None, keys: list[str] | None) -> Q:
        """Build Q filter for ids OR keys."""
        filter_q = Q()
        if ids:
            problem_pks = cls._parse_problem_ids(ids)
            filter_q |= Q(pk__in=problem_pks)
        if keys:
            filter_q |= Q(key__in=keys)
        return filter_q

    @classmethod
    def _parse_problem_ids(cls, global_ids: list[str]) -> list[int]:
        """Convert global IDs to database PKs."""
        problem_pks = []
        for global_id in global_ids:
            _, pk = from_global_id_or_error(global_id, "AppProblem")
            problem_pks.append(int(pk))
        return problem_pks

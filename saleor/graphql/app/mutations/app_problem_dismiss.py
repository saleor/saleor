from typing import Any, cast

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
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
from ...core.validators import validate_one_of_args_is_in_mutation
from ...utils import get_user_or_app_from_context
from ..enums import AppProblemDismissErrorCode
from ..types import App

MAX_ITEMS_LIMIT = 100


class AppProblemDismissError(Error):
    code = AppProblemDismissErrorCode(description="The error code.", required=True)


class AppProblemDismissByAppInput(BaseInputObjectType):
    """Input for app callers to dismiss their own problems."""

    ids = NonNullList(
        graphene.ID,
        required=False,
        description=f"List of problem IDs to dismiss. Cannot be combined with keys. Max {MAX_ITEMS_LIMIT}.",
    )
    keys = NonNullList(
        graphene.String,
        required=False,
        description=f"List of problem keys to dismiss. Cannot be combined with ids. Max {MAX_ITEMS_LIMIT}.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_APPS


class AppProblemDismissByStaffWithIdsInput(BaseInputObjectType):
    """Input for staff callers to dismiss problems by IDs."""

    ids = NonNullList(
        graphene.ID,
        required=True,
        description=f"List of problem IDs to dismiss. Max {MAX_ITEMS_LIMIT}.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_APPS


class AppProblemDismissByStaffWithKeysInput(BaseInputObjectType):
    """Input for staff callers to dismiss problems by keys."""

    keys = NonNullList(
        graphene.String,
        required=True,
        description=f"List of problem keys to dismiss. Max {MAX_ITEMS_LIMIT}.",
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
    by_staff_with_ids = graphene.Field(
        AppProblemDismissByStaffWithIdsInput,
        description="For staff callers - dismiss problems by IDs.",
    )
    by_staff_with_keys = graphene.Field(
        AppProblemDismissByStaffWithKeysInput,
        description="For staff callers - dismiss problems by keys for specified app.",
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
        by_staff_with_ids = input_data.get("by_staff_with_ids")
        by_staff_with_keys = input_data.get("by_staff_with_keys")

        validate_one_of_args_is_in_mutation(
            "by_app",
            by_app,
            "by_staff_with_ids",
            by_staff_with_ids,
            "by_staff_with_keys",
            by_staff_with_keys,
            use_camel_case=True,
        )

        if by_app and caller_app:
            cls._validate_by_app_input(by_app)
            cls._dismiss_for_app_caller(by_app, caller_app)
        elif by_staff_with_ids and not caller_app:
            cls._validate_items_limit(by_staff_with_ids["ids"], "ids")
            cls._dismiss_by_ids_for_staff(info, by_staff_with_ids["ids"])
        elif by_staff_with_keys and not caller_app:
            cls._validate_items_limit(by_staff_with_keys["keys"], "keys")
            cls._dismiss_by_keys_for_staff(
                info, by_staff_with_keys["keys"], by_staff_with_keys["app"]
            )
        else:
            cls._raise_caller_type_mismatch(by_app, by_staff_with_ids)

        return AppProblemDismiss()

    @classmethod
    def _raise_caller_type_mismatch(
        cls,
        by_app: dict | None,
        by_staff_with_ids: dict | None,
    ) -> None:
        if by_app is not None:
            raise ValidationError(
                {
                    "byApp": ValidationError(
                        "Only app callers can use 'byApp'.",
                        code=AppProblemDismissErrorCodeEnum.INVALID.value,
                    )
                }
            )
        field = "byStaffWithIds" if by_staff_with_ids else "byStaffWithKeys"
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

        items = ids or keys
        assert items is not None
        cls._validate_items_limit(items, "ids" if ids else "keys")

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

        if ids:
            AppProblem.objects.filter(
                pk__in=problem_pks, app=caller_app, dismissed=False
            ).order_by("pk").update(dismissed=True)
        else:
            AppProblem.objects.filter(
                key__in=keys, app=caller_app, dismissed=False
            ).order_by("pk").update(dismissed=True)

    @classmethod
    def _validate_items_limit(cls, items: list[str], field_name: str) -> None:
        """Validate that items list does not exceed MAX_ITEMS_LIMIT."""
        if len(items) > MAX_ITEMS_LIMIT:
            raise ValidationError(
                {
                    field_name: ValidationError(
                        f"Cannot specify more than {MAX_ITEMS_LIMIT} items.",
                        code=AppProblemDismissErrorCodeEnum.INVALID.value,
                    )
                }
            )

    @classmethod
    def _dismiss_by_ids_for_staff(
        cls,
        info: ResolveInfo,
        ids: list[str],
    ) -> None:
        """Dismiss problems by IDs for a staff caller."""
        requestor = cast(User, get_user_or_app_from_context(info.context))
        problem_pks = cls._parse_problem_ids(ids)

        AppProblem.objects.filter(pk__in=problem_pks, dismissed=False).order_by(
            "pk"
        ).update(
            dismissed=True,
            dismissed_by_user_email=requestor.email,
            dismissed_by_user=requestor,
        )

    @classmethod
    def _dismiss_by_keys_for_staff(
        cls,
        info: ResolveInfo,
        keys: list[str],
        app_id: str,
    ) -> None:
        """Dismiss problems by keys for a staff caller."""
        requestor = cast(User, get_user_or_app_from_context(info.context))
        target_app = cls.get_node_or_error(info, app_id, field="app", only_type=App)

        AppProblem.objects.filter(
            app=target_app, key__in=keys, dismissed=False
        ).order_by("pk").update(
            dismissed=True,
            dismissed_by_user_email=requestor.email,
            dismissed_by_user=requestor,
        )

    @classmethod
    def _parse_problem_ids(cls, global_ids: list[str]) -> list[int]:
        """Convert global IDs to database PKs."""
        problem_pks = []
        for global_id in global_ids:
            _, pk = from_global_id_or_error(global_id, "AppProblem")
            try:
                problem_pks.append(int(pk))
            except (ValueError, TypeError) as err:
                raise ValidationError(
                    {
                        "ids": ValidationError(
                            f"Invalid ID: {global_id}.",
                            code=AppProblemDismissErrorCodeEnum.INVALID.value,
                        )
                    }
                ) from err
        return problem_pks

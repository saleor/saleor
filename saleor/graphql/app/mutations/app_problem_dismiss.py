from typing import Any

import graphene
from django.core.exceptions import ValidationError
from pydantic import BaseModel, ConfigDict

from ....app.error_codes import (
    AppProblemDismissErrorCode as AppProblemDismissErrorCodeEnum,
)
from ....app.models import App as AppModel
from ....app.models import AppProblem
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AppPermission
from ...account.utils import can_manage_app
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import Error, NonNullList
from ...core.utils import from_global_id_or_error
from ...utils import get_user_or_app_from_context, requestor_is_superuser
from ..enums import AppProblemDismissErrorCode
from ..types import App


class AppProblemDismissError(Error):
    code = AppProblemDismissErrorCode(description="The error code.", required=True)


class AppProblemDismissInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    ids: list[str] | None = None
    keys: list[str] | None = None
    app_id: str | None = None
    caller_is_app: bool

    def validate_input(self) -> None:
        """Validate cross-field constraints. Raises Django ValidationError."""

        both_provided = self.ids and self.keys
        neither_provided = not self.ids and not self.keys
        app_caller_specified_app = self.caller_is_app and self.app_id is not None
        staff_using_keys_without_app = (
            not self.caller_is_app and self.keys and self.app_id is None
        )

        if both_provided:
            raise ValidationError(
                {
                    "ids": ValidationError(
                        "Cannot specify both 'ids' and 'keys'.",
                        code=AppProblemDismissErrorCodeEnum.INVALID.value,
                    )
                }
            )

        if neither_provided:
            raise ValidationError(
                {
                    "ids": ValidationError(
                        "Must provide either 'ids' or 'keys'.",
                        code=AppProblemDismissErrorCodeEnum.REQUIRED.value,
                    )
                }
            )

        if app_caller_specified_app:
            raise ValidationError(
                {
                    "app": ValidationError(
                        "App callers cannot specify the 'app' argument.",
                        code=AppProblemDismissErrorCodeEnum.INVALID.value,
                    )
                }
            )

        if staff_using_keys_without_app:
            raise ValidationError(
                {
                    "app": ValidationError(
                        "The 'app' argument is required for staff when using 'keys'.",
                        code=AppProblemDismissErrorCodeEnum.REQUIRED.value,
                    )
                }
            )


class AppProblemDismiss(BaseMutation):
    app = graphene.Field(
        App,
        description="The app whose problems were dismissed.",
    )

    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=False,
            description="List of problem IDs to dismiss.",
        )
        keys = NonNullList(
            graphene.String,
            required=False,
            description="List of problem keys to dismiss.",
        )
        app = graphene.ID(
            required=False,
            description=(
                "ID of the app whose problems to dismiss. "
                "Required for staff when using keys, disallowed for app callers."
            ),
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

        validated = AppProblemDismissInput(
            ids=data.get("ids"),
            keys=data.get("keys"),
            app_id=data.get("app"),
            caller_is_app=caller_app is not None,
        )
        validated.validate_input()

        target_app = cls._resolve_target_app(info, validated, caller_app)

        if validated.ids:
            target_app = cls._dismiss_by_ids(info, validated, caller_app, target_app)
        else:
            cls._dismiss_by_keys(info, validated, caller_app, target_app)

        return AppProblemDismiss(app=target_app)

    @classmethod
    def _resolve_target_app(
        cls,
        info: ResolveInfo,
        validated: AppProblemDismissInput,
        caller_app: AppModel | None,
    ) -> AppModel | None:
        if caller_app:
            return caller_app

        if validated.app_id is None:
            return None

        target_app = cls.get_node_or_error(
            info, validated.app_id, field="app", only_type=App
        )
        requestor = get_user_or_app_from_context(info.context)
        cannot_manage_target = not requestor_is_superuser(
            requestor
        ) and not can_manage_app(requestor, target_app)

        if cannot_manage_target:
            raise ValidationError(
                {
                    "app": ValidationError(
                        "You can't manage this app.",
                        code=AppProblemDismissErrorCodeEnum.OUT_OF_SCOPE_APP.value,
                    )
                }
            )
        return target_app

    @classmethod
    def _build_dismiss_fields(
        cls, info: ResolveInfo, caller_app: AppModel | None
    ) -> dict[str, Any]:
        fields: dict[str, Any] = {"dismissed": True}
        if caller_app:
            fields["dismissed_by_app"] = caller_app
        else:
            fields["dismissed_by_user"] = get_user_or_app_from_context(info.context)
        return fields

    @classmethod
    def _dismiss_by_ids(
        cls,
        info: ResolveInfo,
        validated: AppProblemDismissInput,
        caller_app: AppModel | None,
        target_app: AppModel | None,
    ) -> AppModel | None:
        # Invariant - in Pydantic model it can be None, so ensure this method is not called incorrectly without ids
        assert validated.ids is not None

        problem_pks = []

        for global_id in validated.ids:
            _, pk = from_global_id_or_error(global_id, "AppProblem")
            problem_pks.append(int(pk))

        qs = AppProblem.objects.filter(pk__in=problem_pks, dismissed=False)

        if caller_app:
            qs = qs.filter(app=caller_app)

        problems = list(qs)

        if not problems:
            return target_app or caller_app

        # For staff calling by IDs, we infer the target app
        if target_app is None:
            target_app = problems[0].app

        qs.update(**cls._build_dismiss_fields(info, caller_app))

        return target_app

    @classmethod
    def _dismiss_by_keys(
        cls,
        info: ResolveInfo,
        validated: AppProblemDismissInput,
        caller_app: AppModel | None,
        target_app: AppModel | None,
    ) -> None:
        # Invariant - in Pydantic model it can be None, so ensure this method is not called incorrectly without keys
        assert validated.keys is not None

        qs = AppProblem.objects.filter(
            app=target_app, key__in=validated.keys, dismissed=False
        )
        qs.update(**cls._build_dismiss_fields(info, caller_app))

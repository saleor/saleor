import graphene
from django.core.exceptions import ValidationError

from ....app.error_codes import (
    AppProblemDismissErrorCode as AppProblemDismissErrorCodeEnum,
)
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
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        ids = data.get("ids")
        keys = data.get("keys")
        app_id = data.get("app")

        if ids and keys:
            raise ValidationError(
                {
                    "ids": ValidationError(
                        "Cannot specify both 'ids' and 'keys'.",
                        code=AppProblemDismissErrorCodeEnum.INVALID.value,
                    )
                }
            )

        if not ids and not keys:
            raise ValidationError(
                {
                    "ids": ValidationError(
                        "Must provide either 'ids' or 'keys'.",
                        code=AppProblemDismissErrorCodeEnum.REQUIRED.value,
                    )
                }
            )

        caller_app = info.context.app

        if caller_app:
            # App caller
            if app_id is not None:
                raise ValidationError(
                    {
                        "app": ValidationError(
                            "App callers cannot specify the 'app' argument.",
                            code=AppProblemDismissErrorCodeEnum.INVALID.value,
                        )
                    }
                )
            target_app = caller_app
        else:
            # Staff caller
            if keys and app_id is None:
                raise ValidationError(
                    {
                        "app": ValidationError(
                            "The 'app' argument is required for staff when using 'keys'.",
                            code=AppProblemDismissErrorCodeEnum.REQUIRED.value,
                        )
                    }
                )

            if app_id is not None:
                target_app = cls.get_node_or_error(
                    info, app_id, field="app", only_type=App
                )
                requestor = get_user_or_app_from_context(info.context)
                if not requestor_is_superuser(requestor) and not can_manage_app(
                    requestor, target_app
                ):
                    raise ValidationError(
                        {
                            "app": ValidationError(
                                "You can't manage this app.",
                                code=AppProblemDismissErrorCodeEnum.OUT_OF_SCOPE_APP.value,
                            )
                        }
                    )
            else:
                target_app = None

        if ids:
            problem_pks = []
            for global_id in ids:
                _, pk = from_global_id_or_error(global_id, "AppProblem")
                problem_pks.append(int(pk))

            qs = AppProblem.objects.filter(pk__in=problem_pks, dismissed=False)
            if caller_app:
                qs = qs.filter(app=caller_app)

            problems = list(qs)
            if not problems:
                return AppProblemDismiss(app=target_app or caller_app)

            # For staff calling by IDs, we infer the target app
            if target_app is None:
                target_app = problems[0].app

            dismiss_fields = {"dismissed": True}
            if caller_app:
                dismiss_fields["dismissed_by_app"] = caller_app
            else:
                requestor = get_user_or_app_from_context(info.context)
                dismiss_fields["dismissed_by_user"] = requestor

            qs.update(**dismiss_fields)
        else:
            # keys
            qs = AppProblem.objects.filter(
                app=target_app, key__in=keys, dismissed=False
            )
            dismiss_fields = {"dismissed": True}
            if caller_app:
                dismiss_fields["dismissed_by_app"] = caller_app
            else:
                requestor = get_user_or_app_from_context(info.context)
                dismiss_fields["dismissed_by_user"] = requestor

            qs.update(**dismiss_fields)

        return AppProblemDismiss(app=target_app)

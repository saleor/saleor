import graphene
from django.core.exceptions import ValidationError

from ....app.error_codes import AppProblemClearErrorCode as AppProblemClearErrorCodeEnum
from ....app.models import AppProblem, AppProblemType
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AppPermission
from ...account.utils import can_manage_app
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import Error
from ...utils import get_user_or_app_from_context, requestor_is_superuser
from ..enums import AppProblemClearErrorCode
from ..types import App


class AppProblemClearError(Error):
    code = AppProblemClearErrorCode(description="The error code.", required=True)


class AppProblemClear(BaseMutation):
    app = graphene.Field(
        App,
        description="The app whose problems were cleared. Only OWN type of problems can be clear with this mutation.",
    )

    class Arguments:
        app = graphene.ID(
            required=False,
            description=(
                "ID of the app to clear problems for. "
                "Required for staff, disallowed for app callers."
            ),
        )
        aggregate = graphene.String(
            required=False,
            description=(
                "If provided, only clears own problems with this aggregate value."
            ),
        )
        key = graphene.String(
            required=False,
            description="If provided, only clears own problems with this key.",
        )

    class Meta:
        description = "Clear problems from the calling app." + ADDED_IN_322
        doc_category = DOC_CATEGORY_APPS
        permissions = (
            AppPermission.MANAGE_APPS,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        error_type_class = AppProblemClearError

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        app_id = data.get("app")
        aggregate = data.get("aggregate")
        key = data.get("key")

        if info.context.app:
            # App caller
            if app_id is not None:
                raise ValidationError(
                    {
                        "app": ValidationError(
                            "App callers cannot specify the 'app' argument.",
                            code=AppProblemClearErrorCodeEnum.INVALID.value,
                        )
                    }
                )
            target_app = info.context.app
        else:
            # Staff caller
            if app_id is None:
                raise ValidationError(
                    {
                        "app": ValidationError(
                            "The 'app' argument is required for staff users.",
                            code=AppProblemClearErrorCodeEnum.REQUIRED.value,
                        )
                    }
                )
            target_app = cls.get_node_or_error(info, app_id, field="app", only_type=App)
            requestor = get_user_or_app_from_context(info.context)
            if not requestor_is_superuser(requestor) and not can_manage_app(
                requestor, target_app
            ):
                raise ValidationError(
                    {
                        "app": ValidationError(
                            "You can't manage this app.",
                            code=AppProblemClearErrorCodeEnum.OUT_OF_SCOPE_APP.value,
                        )
                    }
                )

        if aggregate is not None and key is not None:
            raise ValidationError(
                {
                    "key": ValidationError(
                        "Cannot specify both 'aggregate' and 'key'.",
                        code=AppProblemClearErrorCodeEnum.INVALID.value,
                    )
                }
            )

        qs = AppProblem.objects.filter(app=target_app, type=AppProblemType.OWN)
        if aggregate is not None:
            qs = qs.filter(aggregate=aggregate)
        if key is not None:
            qs = qs.filter(key=key)
        qs.delete()
        return AppProblemClear(app=target_app)

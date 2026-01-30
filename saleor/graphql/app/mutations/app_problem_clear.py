import graphene
from django.core.exceptions import ValidationError

from ....app.error_codes import AppErrorCode
from ....app.models import AppProblem, AppProblemType
from ....core.exceptions import PermissionDenied
from ....permission.auth_filters import AuthorizationFilters
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import AppError
from ..types import App


class AppProblemClear(BaseMutation):
    app = graphene.Field(
        App,
        description="The app whose problems were cleared. Only OWN type of problems can be clear with this mutation.",
    )

    class Arguments:
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
        permissions = (AuthorizationFilters.AUTHENTICATED_APP,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        app = info.context.app
        if not app:
            raise PermissionDenied(permissions=[AuthorizationFilters.AUTHENTICATED_APP])

        aggregate = data.get("aggregate")
        key = data.get("key")
        if aggregate is not None and key is not None:
            raise ValidationError(
                {
                    "key": ValidationError(
                        "Cannot specify both 'aggregate' and 'key'.",
                        code=AppErrorCode.INVALID.value,
                    )
                }
            )

        qs = AppProblem.objects.filter(app=app, type=AppProblemType.OWN)
        if aggregate is not None:
            qs = qs.filter(aggregate=aggregate)
        if key is not None:
            qs = qs.filter(key=key)
        qs.delete()
        return AppProblemClear(app=app)

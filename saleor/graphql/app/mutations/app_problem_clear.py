import graphene

from ....app.models import AppProblem, AppProblemType
from ....core.exceptions import PermissionDenied
from ....permission.auth_filters import AuthorizationFilters
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import AppError
from ..types import App


class AppProblemClear(BaseMutation):
    app = graphene.Field(App, description="The app whose problems were cleared.")

    class Arguments:
        aggregate = graphene.String(
            required=False,
            description=(
                "If provided, only clears custom problems with this aggregate value."
            ),
        )

    class Meta:
        description = "Clear custom problems from the calling app."
        doc_category = DOC_CATEGORY_APPS
        permissions = (AuthorizationFilters.AUTHENTICATED_APP,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        app = info.context.app
        if not app:
            raise PermissionDenied(permissions=[AuthorizationFilters.AUTHENTICATED_APP])
        qs = AppProblem.objects.filter(app=app, type=AppProblemType.CUSTOM)
        aggregate = data.get("aggregate")
        if aggregate is not None:
            qs = qs.filter(aggregate=aggregate)
        qs.delete()
        return AppProblemClear(app=app)

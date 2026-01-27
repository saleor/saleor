import graphene

from ....app.models import AppProblem, AppProblemType
from ....core.exceptions import PermissionDenied
from ....permission.auth_filters import AuthorizationFilters
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import AppError
from ..types import App


class AppProblemCreateInput(graphene.InputObjectType):
    message = graphene.String(
        required=True, description="The problem message to display."
    )
    aggregate = graphene.String(
        required=False,
        description="Grouping key for this problem. Used to clear related problems.",
    )


class AppProblemCreate(BaseMutation):
    app = graphene.Field(App, description="The app with the new problem.")

    class Arguments:
        input = AppProblemCreateInput(
            required=True, description="Fields required to create an app problem."
        )

    class Meta:
        description = "Add a custom problem to the calling app."
        doc_category = DOC_CATEGORY_APPS
        permissions = (AuthorizationFilters.AUTHENTICATED_APP,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        app = info.context.app
        if not app:
            raise PermissionDenied(permissions=[AuthorizationFilters.AUTHENTICATED_APP])
        input_data = data["input"]
        AppProblem.objects.create(
            app=app,
            type=AppProblemType.CUSTOM,
            message=input_data["message"],
            aggregate=input_data.get("aggregate", ""),
        )
        return AppProblemCreate(app=app)

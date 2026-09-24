from typing import Any, cast

import graphene

from ....app.models import DEPRECATION_REASON_MAX_LENGTH
from ....app.models import App as AppModel
from ....app.utils import normalize_deprecation_reason
from ....permission.auth_filters import AuthorizationFilters
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_323
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, Error
from ..enums import AppSelfUpdateErrorCode
from ..types import App


class AppSelfUpdateError(Error):
    code = AppSelfUpdateErrorCode(
        description="The error code." + ADDED_IN_323, required=True
    )

    class Meta:
        description = "Represents errors in the appSelfUpdate mutation." + ADDED_IN_323
        doc_category = DOC_CATEGORY_APPS


class AppSelfUpdateInput(BaseInputObjectType):
    deprecation_reason = graphene.String(
        required=False,
        description=(
            "Reason why the app is deprecated. Setting it marks the app as "
            "deprecated in the dashboard; the app itself keeps working as "
            "usual. Pass a blank value to clear it. Omit the field or pass "
            "`null` to leave it unchanged. Values longer than "
            f"{DEPRECATION_REASON_MAX_LENGTH} characters are truncated." + ADDED_IN_323
        ),
    )

    class Meta:
        description = "Fields to update on the calling app." + ADDED_IN_323
        doc_category = DOC_CATEGORY_APPS


class AppSelfUpdate(BaseMutation):
    app = graphene.Field(App, description="The updated app." + ADDED_IN_323)

    class Arguments:
        input = AppSelfUpdateInput(
            required=True,
            description="Fields to update on the calling app." + ADDED_IN_323,
        )

    class Meta:
        description = (
            "Updates the app that calls this mutation. Only the app itself can "
            "change these fields - staff users cannot set them via `appUpdate`."
            + ADDED_IN_323
        )
        doc_category = DOC_CATEGORY_APPS
        permissions = (AuthorizationFilters.AUTHENTICATED_APP,)
        error_type_class = AppSelfUpdateError

    @classmethod
    def perform_mutation(
        cls, _root: None, info: ResolveInfo, /, **data: Any
    ) -> "AppSelfUpdate":
        app = cast(AppModel, info.context.app)
        input_data = data["input"]

        # `null` means "leave unchanged", exactly like omitting the field, so
        # that fields added to this input later can't wipe each other - clients
        # commonly serialize unset fields as explicit nulls. Clearing is done
        # by sending a blank string, which `normalize_deprecation_reason` maps
        # back to NULL.
        reason_input = input_data.get("deprecation_reason")
        if reason_input is not None:
            reason = normalize_deprecation_reason(reason_input)
            if reason != app.deprecation_reason:
                app.deprecation_reason = reason
                app.save(update_fields=["deprecation_reason"])

        return AppSelfUpdate(app=app)

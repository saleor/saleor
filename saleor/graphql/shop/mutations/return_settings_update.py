import graphene

from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType
from ...core.types.common import ReturnSettingsUpdateError
from ...site.dataloaders import get_site_promise
from ..types import ReturnSettings


class ReturnSettingsUpdateInput(BaseInputObjectType):
    return_reason_reference_type = graphene.ID(
        description=(
            "The ID of a model type, that will be used to reference return reasons. "
            "All models with of this type will be accepted as return reasons. "
            f"{ADDED_IN_322}"
        ),
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_SHOP


class ReturnSettingsUpdate(BaseMutation):
    return_settings = graphene.Field(
        ReturnSettings, description="Return settings.", required=True
    )

    class Arguments:
        input = ReturnSettingsUpdateInput(
            required=True, description="Fields required to update return settings."
        )

    class Meta:
        description = "Update return settings across all channels." + ADDED_IN_322
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ReturnSettingsUpdateError
        error_type_field = "return_settings_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, input
    ):
        return_reason_reference_type = input.get("return_reason_reference_type")

        site = get_site_promise(info.context).get()
        settings = site.settings

        if return_reason_reference_type:
            model_type = cls.get_node_or_error(
                info,
                return_reason_reference_type,
                only_type="PageType",
                field="return_reason_reference_type",
            )

            settings.return_reason_reference_type = model_type  # type: ignore[assignment]

            settings.save(update_fields=["return_reason_reference_type"])

        return ReturnSettingsUpdate(return_settings=settings)

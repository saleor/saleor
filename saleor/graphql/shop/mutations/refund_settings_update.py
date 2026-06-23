import graphene
from django.core.exceptions import ValidationError

from ....permission.enums import SitePermissions
from ....site.error_codes import RefundSettingsErrorCode
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType
from ...core.types.common import RefundSettingsUpdateError
from ...page.types import PageType
from ...site.dataloaders import get_site_promise
from ..types import RefundSettings


class RefundSettingsUpdateInput(BaseInputObjectType):
    refund_reason_reference_type = graphene.ID(
        description=(
            "The ID of a model type, that will be used to reference refund reasons. "
            "All models with of this type will be accepted as refund reasons. "
            f"{ADDED_IN_322}"
        ),
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_SHOP


class RefundSettingsUpdate(BaseMutation):
    refund_settings = graphene.Field(RefundSettings, description="Refund settings.")

    class Arguments:
        input = RefundSettingsUpdateInput(
            required=True, description="Fields required to update refund settings."
        )

    class Meta:
        description = "Update refund settings across all channels." + ADDED_IN_322
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = RefundSettingsUpdateError
        error_type_field = "refund_settings_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, input
    ):
        refund_reason_reference_type = input.get("refund_reason_reference_type")

        if not refund_reason_reference_type:
            raise ValidationError(
                {
                    "refund_reason_reference_type": ValidationError(
                        "This field is required.",
                        code=RefundSettingsErrorCode.REQUIRED.value,
                    )
                }
            )

        site = get_site_promise(info.context).get()
        settings = site.settings

        model_type = cls.get_node_or_error(
            info,
            refund_reason_reference_type,
            only_type=PageType,
            field="refund_reason_reference_type",
        )

        settings.refund_reason_reference_type = model_type
        settings.save(update_fields=["refund_reason_reference_type"])

        return RefundSettingsUpdate(refund_settings=settings)

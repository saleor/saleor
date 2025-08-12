import graphene
from django.core.exceptions import ValidationError

from ....page.models import PageType
from ....permission.enums import SitePermissions
from ....site.models import SiteSettings
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType
from ...core.types.common import RefundSettingsError
from ..types import RefundSettings


class RefundSettingsUpdateInput(BaseInputObjectType):
    refund_reason_reference_type = graphene.ID(
        description=(
            "The ID of a model type, that will be used to reference refund reasons. "
            "All models with of this type will be accepted as refund reasons. "
            f"{ADDED_IN_322}"
        ),
        required=False,
    )

    class Meta:
        # Orders or Shop?
        doc_category = DOC_CATEGORY_SHOP


class RefundSettingsUpdate(BaseMutation):
    refund_settings = graphene.Field(
        RefundSettings, description="Refund settings.", required=True
    )

    class Arguments:
        input = RefundSettingsUpdateInput(
            required=True, description="Fields required to update refund settings."
        )

    class Meta:
        description = "Update refund settings across all channels." + ADDED_IN_322
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = RefundSettingsError
        error_type_field = "refund_settings_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        input = data.get("input")

        refund_reason_reference_type = input.get("refund_reason_reference_type")

        if len(refund_reason_reference_type) == 0:
            raise ValidationError(
                {
                    "refund_reason_model_type": ValidationError(
                        "Field should be a valid ID", code="invalid"
                    )
                }
            ) from None

        settings = SiteSettings.objects.get()

        if refund_reason_reference_type:
            try:
                page_type_id = cls.get_global_id_or_error(
                    refund_reason_reference_type, "PageType"
                )
                model_type = PageType.objects.get(pk=page_type_id)
                settings.refund_reason_reference_type = model_type
            except PageType.DoesNotExist:
                raise ValidationError(
                    {
                        "refund_reason_model_type": ValidationError(
                            "PageType with given ID does not exist.", code="not_found"
                        )
                    }
                ) from None

        settings.save()

        return RefundSettingsUpdate(refund_settings=settings)

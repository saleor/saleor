import graphene
from django.core.exceptions import ValidationError

from ....page.models import PageType
from ....permission.enums import SitePermissions
from ....site.models import SiteSettings
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType
from ...core.types.common import RefundSettingsError
from ..types import RefundSettings


class RefundSettingsUpdateInput(BaseInputObjectType):
    allow_custom_refund_reasons = graphene.Boolean(
        description=(
            f"Allow to set a custom reason for a refund. When set to false, only referenced models will be accepted"
            f"{ADDED_IN_322}"
        )
    )
    refund_reason_model_type = graphene.ID(
        description=(
            "The ID of a model type, that will be used to reference refund reasons. "
            "All models with of this type will be accepted as refund reasons. "
            f"{ADDED_IN_322}"
        )
    )

    class Meta:
        # Orders or Shop?
        doc_category = DOC_CATEGORY_ORDERS


class RefundSettingsUpdate(BaseMutation):
    refund_settings = graphene.Field(RefundSettings, description="Refund settings.")

    class Arguments:
        input = RefundSettingsUpdateInput(
            required=True, description="Fields required to update shop refund settings."
        )

    class Meta:
        description = "Update shop refund settings across all channels. "
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = RefundSettingsError
        error_type_field = "refund_settings_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        input = data.get("input")

        allow_custom_refund_reasons = input.get("allow_custom_refund_reasons")
        refund_reason_model_type = input.get("refund_reason_model_type")

        if not allow_custom_refund_reasons and refund_reason_model_type is None:
            raise ValidationError(
                {
                    "allow_custom_refund_reasons": ValidationError(
                        "When allowCustomRefundReasons is false, model type must be provided",
                        # TODO What code?
                        code="required",
                    )
                }
            ) from None

        # TODO Check permissions

        # todo site loader
        settings = SiteSettings.objects.get()

        if allow_custom_refund_reasons is not None:
            settings.allow_custom_refund_reasons = allow_custom_refund_reasons

        # Handle refund_reason_type - validate PageType exists and create one-to-one reference
        if refund_reason_model_type:
            try:
                # Decode the global ID to get the actual database ID
                page_type_id = cls.get_global_id_or_error(
                    refund_reason_model_type, "PageType"
                )
                model_type = PageType.objects.get(pk=page_type_id)
                settings.refund_reason_model_type = model_type
            except PageType.DoesNotExist:
                raise ValidationError(
                    {
                        "refund_reason_model_type": ValidationError(
                            "PageType with given ID does not exist.", code="not_found"
                        )
                    }
                ) from None
        else:
            # Set to None when refund_reason_type is null/None
            settings.refund_reason_model_type = None

        settings.save()

        return RefundSettingsUpdate(refund_settings=settings)

import graphene

from ....permission.enums import SitePermissions
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
    refund_reason_type = graphene.ID(
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
        # TODO Validation
        # TODO Check permissions

        # TODO Logic

        refund_settings = RefundSettings(
            # TODO Properly instantionate this
            allow_custom_refund_reasons=True  # todo
        )

        return RefundSettingsUpdate(refund_settings=refund_settings)

import graphene

from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types.common import ReturnReasonReferenceTypeClearError
from ...site.dataloaders import get_site_promise
from ..types import ReturnSettings


class ReturnReasonReferenceTypeClear(BaseMutation):
    return_settings = graphene.Field(
        ReturnSettings, description="Return settings.", required=True
    )

    class Meta:
        description = (
            "Updates ReturnSettings. The `Page` (Model) Type will be cleared from `reasonReferenceType`. When it's cleared, passing reason reference to return mutations is no longer accepted and will raise error."
            + ADDED_IN_322
        )
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ReturnReasonReferenceTypeClearError
        error_type_field = "return_settings_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        site = get_site_promise(info.context).get()
        settings = site.settings

        settings.return_reason_reference_type = None

        settings.save(update_fields=["return_reason_reference_type"])

        return ReturnReasonReferenceTypeClear(return_settings=settings)

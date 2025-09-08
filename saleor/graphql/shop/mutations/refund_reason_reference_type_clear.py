import graphene

from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types.common import RefundSettingsError
from ...site.dataloaders import get_site_promise
from ..types import RefundSettings


class RefundReasonReferenceTypeClear(BaseMutation):
    refund_settings = graphene.Field(
        RefundSettings, description="Refund settings.", required=True
    )

    class Meta:
        description = "Clear refundReasonReference setting" + ADDED_IN_322
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = RefundSettingsError
        error_type_field = "refund_settings_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        site = get_site_promise(info.context).get()
        settings = site.settings

        settings.refund_reason_reference_type = None

        settings.save(update_fields=["refund_reason_reference_type"])

        return RefundReasonReferenceTypeClear(refund_settings=settings)

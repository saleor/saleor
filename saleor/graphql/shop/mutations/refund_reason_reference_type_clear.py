import graphene
from django.contrib.sites.models import Site

from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types.common import RefundReasonReferenceTypeClearError
from ..types import RefundSettings


class RefundReasonReferenceTypeClear(BaseMutation):
    refund_settings = graphene.Field(
        RefundSettings, description="Refund settings.", required=True
    )

    class Meta:
        description = (
            "Updates RefundSettings. The `Page` (Model) Type will be cleared from `reasonReferenceType`. When it's cleared, passing reason reference to refund mutations is no longer accepted and will raise error."
            + ADDED_IN_322
        )
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = RefundReasonReferenceTypeClearError
        error_type_field = "refund_settings_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        settings = Site.objects.get_current().settings

        settings.refund_reason_reference_type = None

        settings.save(update_fields=["refund_reason_reference_type"])

        return RefundReasonReferenceTypeClear(refund_settings=settings)

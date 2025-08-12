import graphene

from ...core.descriptions import ADDED_IN_322
from ....permission.enums import SitePermissions
from ....site.models import SiteSettings
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types.common import RefundSettingsError
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

        settings = SiteSettings.objects.get()

        settings.refund_reason_reference_type = None

        settings.save()

        return RefundReasonReferenceTypeClear(refund_settings=settings)

import graphene

from ....csv import models as csv_models
from ....csv.events import export_started_event
from ....csv.tasks import export_voucher_codes_task
from ....permission.enums import DiscountPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_318
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.types import BaseInputObjectType, ExportError, NonNullList
from ...core.utils import WebhookEventInfo
from ...discount.schema import VoucherCodeFilterInput
from ...discount.types import VoucherCode
from ..enums import ExportScope, FileTypeEnum
from .base_export import BaseExportMutation


class ExportVoucherCodesInput(BaseInputObjectType):
    scope = ExportScope(
        description="Determine which voucher codes should be exported.", required=True
    )
    filter = VoucherCodeFilterInput(
        description="Filtering options for voucher codes.", required=False
    )
    ids = NonNullList(
        graphene.ID,
        description="List of voucher code IDs to export.",
        required=False,
    )
    file_type = FileTypeEnum(description="Type of exported file.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class ExportVoucherCodes(BaseExportMutation):
    class Arguments:
        input = ExportVoucherCodesInput(
            required=True, description="Fields required to export voucher codes."
        )

    class Meta:
        description = "Export voucher codes to csv/xlsx file." + ADDED_IN_318
        doc_category = DOC_CATEGORY_DISCOUNTS
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = ExportError
        webhook_events_info = [
            # WebhookEventInfo(
            #     type=WebhookEventAsyncType.VOUCHER_CODE_EXPORT_COMPLETED,
            #     description="A notification for the exported file.",
            # ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        scope = cls.get_scope(input, VoucherCode)
        file_type = input["file_type"]

        app = get_app_promise(info.context).get()

        export_file = csv_models.ExportFile.objects.create(
            app=app, user=info.context.user
        )
        export_started_event(export_file=export_file, app=app, user=info.context.user)
        export_voucher_codes_task.delay(export_file.pk, scope, file_type)

        export_file.refresh_from_db()
        return cls(export_file=export_file)

import graphene
from django.core.exceptions import ValidationError

from ....csv import models as csv_models
from ....csv.error_codes import ExportErrorCode
from ....csv.events import export_started_event
from ....csv.tasks import export_voucher_codes_task
from ....permission.enums import DiscountPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_318, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.types import ExportError, NonNullList
from ...core.utils import raise_validation_error
from ...core.validators import validate_one_of_args_is_in_mutation
from ...directives import doc, webhook_events
from ..enums import FileTypeEnum
from .base_export import BaseExportMutation


@doc(category=DOC_CATEGORY_DISCOUNTS)
class ExportVoucherCodesInput(graphene.InputObjectType):
    voucher_id = graphene.GlobalID(
        required=False,
        description=(
            "The ID of the voucher. "
            "If provided, exports all codes belonging to the voucher."
        ),
    )
    ids = NonNullList(
        graphene.ID,
        description="List of voucher code IDs to export.",
        required=False,
    )
    file_type = FileTypeEnum(description="Type of exported file.", required=True)


@doc(category=DOC_CATEGORY_DISCOUNTS)
@webhook_events(async_events={WebhookEventAsyncType.VOUCHER_CODE_EXPORT_COMPLETED})
class ExportVoucherCodes(BaseExportMutation):
    class Arguments:
        input = ExportVoucherCodesInput(
            required=True, description="Fields required to export voucher codes."
        )

    class Meta:
        description = (
            "Export voucher codes to csv/xlsx file." + ADDED_IN_318 + PREVIEW_FEATURE
        )
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = ExportError

    @classmethod
    def clean_input(cls, input):
        voucher_id = input.get("voucher_id")
        ids = input.get("ids") or []
        validate_one_of_args_is_in_mutation("voucher_id", voucher_id, "ids", ids)

        if voucher_id:
            try:
                input["voucher_id"] = cls.get_global_id_or_error(
                    id=voucher_id, only_type="Voucher"
                )
            except ValidationError:
                raise_validation_error(
                    field="voucherId",
                    message="Invalid voucher ID.",
                    code=ExportErrorCode.INVALID,
                )

        if ids:
            try:
                input["ids"] = cls.get_global_ids_or_error(
                    ids=ids, only_type="VoucherCode"
                )
            except ValidationError:
                raise_validation_error(
                    field="ids",
                    message="Invalid voucher code IDs.",
                    code=ExportErrorCode.INVALID,
                )
        return input

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        cls.clean_input(input)
        file_type = input["file_type"]
        ids = input.get("ids") or []
        voucher_id = input.get("voucher_id")

        app = get_app_promise(info.context).get()

        export_file = csv_models.ExportFile.objects.create(
            app=app, user=info.context.user
        )
        export_started_event(export_file=export_file, app=app, user=info.context.user)
        export_voucher_codes_task.delay(
            export_file.pk, file_type, voucher_id=voucher_id, ids=ids
        )

        export_file.refresh_from_db()
        return cls(export_file=export_file)

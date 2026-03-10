import graphene

from ....csv import models as csv_models
from ....csv.events import export_started_event
from ....csv.tasks import export_purchase_orders_task
from ....permission.enums import ProductPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.types import BaseInputObjectType, ExportError, NonNullList
from ...core.utils import WebhookEventInfo
from ...inventory.types import PurchaseOrder as PurchaseOrderType
from ..enums import ExportScope, FileTypeEnum
from .base_export import BaseExportMutation


class ExportPurchaseOrdersInput(BaseInputObjectType):
    scope = ExportScope(
        description="Determine which purchase orders should be exported.",
        required=True,
    )
    ids = NonNullList(
        graphene.ID,
        description="List of purchase order IDs to export.",
        required=False,
    )
    file_type = FileTypeEnum(description="Type of exported file.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ExportPurchaseOrders(BaseExportMutation):
    class Arguments:
        input = ExportPurchaseOrdersInput(
            required=True,
            description="Fields required to export purchase orders data.",
        )

    class Meta:
        description = "Export purchase orders to csv or xlsx file."
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ExportError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for the exported file.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, input):  # type: ignore[override]
        scope = cls.get_scope(input, PurchaseOrderType)
        file_type = input["file_type"]

        app = get_app_promise(info.context).get()

        export_file = csv_models.ExportFile.objects.create(
            app=app, user=info.context.user
        )
        export_started_event(export_file=export_file, app=app, user=info.context.user)
        export_purchase_orders_task.delay(export_file.pk, scope, file_type)

        export_file.refresh_from_db()
        return cls(export_file=export_file)

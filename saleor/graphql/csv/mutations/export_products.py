import graphene

from ....csv import models as csv_models
from ....csv.events import export_started_event
from ....csv.tasks import export_products_task
from ....permission.enums import ProductPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...attribute.types import Attribute
from ...channel.types import Channel
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.types import BaseInputObjectType, ExportError, NonNullList
from ...core.utils import WebhookEventInfo
from ...product.filters import ProductFilterInput
from ...product.types import Product
from ...warehouse.types import Warehouse
from ..enums import ExportScope, FileTypeEnum, ProductFieldEnum
from .base_export import BaseExportMutation


class ExportInfoInput(BaseInputObjectType):
    attributes = NonNullList(
        graphene.ID,
        description="List of attribute ids witch should be exported.",
    )
    warehouses = NonNullList(
        graphene.ID,
        description="List of warehouse ids witch should be exported.",
    )
    channels = NonNullList(
        graphene.ID,
        description="List of channels ids which should be exported.",
    )
    fields = NonNullList(
        ProductFieldEnum,
        description="List of product fields witch should be exported.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ExportProductsInput(BaseInputObjectType):
    scope = ExportScope(
        description="Determine which products should be exported.", required=True
    )
    filter = ProductFilterInput(
        description="Filtering options for products.", required=False
    )
    ids = NonNullList(
        graphene.ID,
        description="List of products IDs to export.",
        required=False,
    )
    export_info = ExportInfoInput(
        description="Input with info about fields which should be exported.",
        required=False,
    )
    file_type = FileTypeEnum(description="Type of exported file.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ExportProducts(BaseExportMutation):
    class Arguments:
        input = ExportProductsInput(
            required=True, description="Fields required to export product data."
        )

    class Meta:
        description = "Export products to csv file."
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ExportError
        error_type_field = "export_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for the exported file.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, input
    ):
        scope = cls.get_scope(input, Product)
        export_info = cls.get_export_info(input["export_info"])
        file_type = input["file_type"]

        app = get_app_promise(info.context).get()

        export_file = csv_models.ExportFile.objects.create(
            app=app, user=info.context.user
        )
        export_started_event(export_file=export_file, app=app, user=info.context.user)
        export_products_task.delay(export_file.pk, scope, export_info, file_type)

        export_file.refresh_from_db()
        return cls(export_file=export_file)

    @classmethod
    def get_export_info(cls, export_info_input):
        export_info = {}
        fields = export_info_input.get("fields")
        if fields:
            export_info["fields"] = fields

        for field, graphene_type in [
            ("attributes", Attribute),
            ("warehouses", Warehouse),
            ("channels", Channel),
        ]:
            pks = cls.get_items_pks(field, export_info_input, graphene_type)
            if pks:
                export_info[field] = pks

        return export_info

    @classmethod
    def get_items_pks(cls, field, export_info_input, graphene_type):
        ids = export_info_input.get(field)
        if not ids:
            return
        pks = cls.get_global_ids_or_error(ids, only_type=graphene_type, field=field)
        return pks

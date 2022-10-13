from typing import Dict, List, Mapping, Union

import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import GiftcardPermissions, ProductPermissions
from ...csv import models as csv_models
from ...csv.events import export_started_event
from ...csv.tasks import export_gift_cards_task, export_products_task
from ..app.dataloaders import load_app
from ..attribute.types import Attribute
from ..channel.types import Channel
from ..core.descriptions import ADDED_IN_31, PREVIEW_FEATURE
from ..core.enums import ExportErrorCode
from ..core.mutations import BaseMutation
from ..core.types import ExportError, NonNullList
from ..giftcard.filters import GiftCardFilterInput
from ..giftcard.types import GiftCard
from ..product.filters import ProductFilterInput
from ..product.types import Product
from ..warehouse.types import Warehouse
from .enums import ExportScope, FileTypeEnum, ProductFieldEnum
from .types import ExportFile


class BaseExportMutation(BaseMutation):
    export_file = graphene.Field(
        ExportFile,
        description=(
            "The newly created export file job which is responsible for export data."
        ),
    )

    class Meta:
        abstract = True

    @classmethod
    def get_scope(cls, input, only_type) -> Mapping[str, Union[list, dict, str]]:
        scope = input["scope"]
        if scope == ExportScope.IDS.value:  # type: ignore
            return cls.clean_ids(input, only_type)
        elif scope == ExportScope.FILTER.value:  # type: ignore
            return cls.clean_filter(input)
        return {"all": ""}

    @classmethod
    def clean_ids(cls, input, only_type) -> Dict[str, List[str]]:
        ids = input.get("ids", [])
        if not ids:
            raise ValidationError(
                {
                    "ids": ValidationError(
                        "You must provide at least one id.",
                        code=ExportErrorCode.REQUIRED.value,
                    )
                }
            )
        pks = cls.get_global_ids_or_error(ids, only_type=only_type, field="ids")
        return {"ids": pks}

    @staticmethod
    def clean_filter(input) -> Dict[str, dict]:
        filter = input.get("filter")
        if not filter:
            raise ValidationError(
                {
                    "filter": ValidationError(
                        "You must provide filter input.",
                        code=ExportErrorCode.REQUIRED.value,
                    )
                }
            )
        return {"filter": filter}


class ExportInfoInput(graphene.InputObjectType):
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


class ExportProductsInput(graphene.InputObjectType):
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


class ExportProducts(BaseExportMutation):
    class Arguments:
        input = ExportProductsInput(
            required=True, description="Fields required to export product data."
        )

    class Meta:
        description = "Export products to csv file."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ExportError
        error_type_field = "export_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        input = data["input"]
        scope = cls.get_scope(input, Product)
        export_info = cls.get_export_info(input["export_info"])
        file_type = input["file_type"]

        app = load_app(info.context)
        kwargs = {"app": app} if app else {"user": info.context.user}

        export_file = csv_models.ExportFile.objects.create(**kwargs)
        export_started_event(export_file=export_file, **kwargs)
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


class ExportGiftCardsInput(graphene.InputObjectType):
    scope = ExportScope(
        description="Determine which gift cards should be exported.", required=True
    )
    filter = GiftCardFilterInput(
        description="Filtering options for gift cards.", required=False
    )
    ids = NonNullList(
        graphene.ID,
        description="List of gift cards IDs to export.",
        required=False,
    )
    file_type = FileTypeEnum(description="Type of exported file.", required=True)


class ExportGiftCards(BaseExportMutation):
    class Arguments:
        input = ExportGiftCardsInput(
            required=True, description="Fields required to export gift cards data."
        )

    class Meta:
        description = "Export gift cards to csv file." + ADDED_IN_31 + PREVIEW_FEATURE
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = ExportError

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        input = data["input"]
        scope = cls.get_scope(input, GiftCard)
        file_type = input["file_type"]

        app = load_app(info.context)
        kwargs = {"app": app} if app else {"user": info.context.user}

        export_file = csv_models.ExportFile.objects.create(**kwargs)
        export_started_event(export_file=export_file, **kwargs)
        export_gift_cards_task.delay(export_file.pk, scope, file_type)

        export_file.refresh_from_db()
        return cls(export_file=export_file)

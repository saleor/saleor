from typing import Dict, List, Mapping, Union

import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import ProductPermissions
from ...csv import models as csv_models
from ...csv.events import export_event
from ...csv.utils.export import export_products
from ..core.enums import CsvErrorCode
from ..core.mutations import BaseMutation
from ..core.types.common import CsvError
from ..product.filters import ProductFilterInput
from ..product.types import Product
from ..utils import resolve_global_ids_to_primary_keys
from .enums import ExportScope
from .types import ExportFile


class ExportProductsInput(graphene.InputObjectType):
    scope = ExportScope(
        description="Determine which products should be exported.", required=True
    )
    filter = ProductFilterInput(
        description="Filtering options for products.", required=False
    )
    ids = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of products IDS to export.",
        required=False,
    )


class ExportProducts(BaseMutation):
    export_file = graphene.Field(
        ExportFile,
        description=(
            "The newly created export file job which is responsible for export data."
        ),
    )

    class Arguments:
        input = ExportProductsInput(
            required=True, description="Fields required to export product data"
        )

    class Meta:
        description = "Export products to csv file."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CsvError
        error_type_field = "csv_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        scope = cls.get_products_scope(info, data["input"])
        export_file = csv_models.ExportFile.objects.create(created_by=user)
        export_event(export_file=export_file, user=user)
        export_products.delay(export_file.pk, scope)
        export_file.refresh_from_db()
        return cls(export_file=export_file)

    @classmethod
    def get_products_scope(cls, info, input) -> Mapping[str, Union[list, dict, str]]:
        scope = input["scope"]
        if scope == ExportScope.IDS.value:  # type: ignore
            return cls.clean_ids(input)
        elif scope == ExportScope.FILTER.value:  # type: ignore
            return cls.clean_filter(input)
        return {"all": ""}

    @staticmethod
    def clean_ids(input) -> Dict[str, List[str]]:
        ids = input.get("ids", [])
        if not ids:
            raise ValidationError(
                {
                    "ids": ValidationError(
                        "You must provide at least one product id.",
                        code=CsvErrorCode.REQUIRED.value,
                    )
                }
            )
        _, pks = resolve_global_ids_to_primary_keys(ids, graphene_type=Product)
        return {"ids": pks}

    @staticmethod
    def clean_filter(input) -> Dict[str, dict]:
        filter = input.get("filter")
        if not filter:
            raise ValidationError(
                {
                    "filter": ValidationError(
                        "You must provide filter input.",
                        code=CsvErrorCode.REQUIRED.value,
                    )
                }
            )
        return {"filter": filter}

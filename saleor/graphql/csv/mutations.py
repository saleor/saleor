import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import ProductPermissions
from ...csv import models as csv_models
from ...csv.utils.export import export_products
from ...product import models as product_models
from ..core.enums import CsvErrorCode
from ..core.mutations import BaseMutation
from ..core.types.common import CsvError
from ..product.filters import ProductFilterInput
from ..utils import _resolve_nodes
from .enums import ExportScope
from .types import Job


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
    job = graphene.Field(
        Job, description="Tne newly created job which is responsible for export data."
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
        scope = cls.get_products_scope(info, data["input"])
        job = csv_models.Job.objects.create()
        export_products.delay(scope, job.pk)
        job.refresh_from_db()
        return cls(job=job)

    @classmethod
    def get_products_scope(cls, info, input):
        scope = input["scope"]
        if scope == ExportScope.IDS.value:
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
            _, pks = _resolve_nodes(ids, graphene_type=product_models.Product)
            return {"ids": pks}
        elif scope == ExportScope.FILTER.value:
            filter = input.get("filter")
            if not filter:
                raise ValidationError(
                    {
                        "filter": ValidationError(
                            "You must provide filter input.",
                            code=CsvErrorCode.REQUIRED.code,
                        )
                    }
                )
            return {"filter": filter}
        return {"all": ""}

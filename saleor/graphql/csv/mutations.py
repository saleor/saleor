import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import ProductPermissions
from ...product import models as product_models
from ..core.enums import CsvErrorCode
from ..core.mutations import BaseMutation
from ..core.types.common import CsvError
from ..product.filters import ProductFilterInput
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
        # TODO: add prefetch_related: attributes, productVariant,
        # productType, collections, category etc.
        cls.get_queryset(cls, data["input"])
        return None

    @classmethod
    def get_queryset(cls, info, input):
        scope = input["scope"]
        queryset = product_models.Product.objects.all()
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
            queryset = cls.get_nodes_or_error(
                ids, "ids", only_type=product_models.Product
            )
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
            queryset = ProductFilterInput.filterset_class(
                data=filter, queryset=queryset
            ).qs
        return queryset.order_by("pk")

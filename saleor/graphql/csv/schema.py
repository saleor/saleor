import graphene

from ...core.permissions import ProductPermissions
from ...csv import models
from ..core.fields import FilterInputConnectionField
from ..decorators import permission_required
from .filters import ExportFileFilterInput
from .mutations import ExportProducts
from .sorters import ExportFileSortingInput
from .types import ExportFile


class CsvQueries(graphene.ObjectType):
    export_file = graphene.Field(
        ExportFile,
        id=graphene.Argument(
            graphene.ID, description="ID of the export file job.", required=True
        ),
        description="Look up a export file by ID.",
    )
    export_files = FilterInputConnectionField(
        ExportFile,
        filter=ExportFileFilterInput(description="Filtering options for export files."),
        sort_by=ExportFileSortingInput(description="Sort export files."),
        description="List of export files.",
    )

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_export_file(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ExportFile)

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_export_files(self, info, query=None, sort_by=None, **kwargs):
        return models.ExportFile.objects.all()


class CsvMutations(graphene.ObjectType):
    export_products = ExportProducts.Field()

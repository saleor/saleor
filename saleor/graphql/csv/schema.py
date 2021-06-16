import graphene

from ...core.permissions import ProductPermissions
from ..core.fields import FilterInputConnectionField
from ..core.utils import from_global_id_or_error
from ..decorators import permission_required
from .filters import ExportFileFilterInput
from .mutations import ExportProducts
from .resolvers import resolve_export_file, resolve_export_files
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
        _, id = from_global_id_or_error(id, ExportFile)
        return resolve_export_file(id)

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_export_files(self, _info, **kwargs):
        return resolve_export_files()


class CsvMutations(graphene.ObjectType):
    export_products = ExportProducts.Field()

import graphene

from ...core.permissions import ProductPermissions
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.fields import FilterConnectionField
from ..core.utils import from_global_id_or_error
from ..decorators import permission_required
from .filters import ExportFileFilterInput
from .mutations import ExportGiftCards, ExportProducts
from .resolvers import resolve_export_file, resolve_export_files
from .sorters import ExportFileSortingInput
from .types import ExportFile, ExportFileCountableConnection


class CsvQueries(graphene.ObjectType):
    export_file = graphene.Field(
        ExportFile,
        id=graphene.Argument(
            graphene.ID, description="ID of the export file job.", required=True
        ),
        description="Look up a export file by ID.",
    )
    export_files = FilterConnectionField(
        ExportFileCountableConnection,
        filter=ExportFileFilterInput(description="Filtering options for export files."),
        sort_by=ExportFileSortingInput(description="Sort export files."),
        description="List of export files.",
    )

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_export_file(self, info, id):
        _, id = from_global_id_or_error(id, ExportFile)
        return resolve_export_file(id)

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_export_files(self, info, **kwargs):
        qs = resolve_export_files()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, ExportFileCountableConnection)


class CsvMutations(graphene.ObjectType):
    export_products = ExportProducts.Field()
    export_gift_cards = ExportGiftCards.Field()

import graphene
import graphene_django_optimizer as gql_optimizer

from ...core.permissions import ProductPermissions
from ...csv import models
from ..core.fields import FilterInputConnectionField
from ..decorators import permission_required
from ..utils import sort_queryset
from .filters import JobFilterInput
from .mutations import ExportProducts
from .sorters import JobSortingInput
from .types import Job


class CsvQueries(graphene.ObjectType):
    job = graphene.Field(
        Job,
        id=graphene.Argument(graphene.ID, description="ID of the job.", required=True),
        description="Look up a job by ID.",
    )
    jobs = FilterInputConnectionField(
        Job,
        filter=JobFilterInput(description="Filtering options for jobs."),
        sort_by=JobSortingInput(description="Sort jobs."),
        description="List of jobs.",
    )

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_job(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Job)

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_jobs(self, info, query=None, sort_by=None, **kwargs):
        qs = models.Job.objects.all()
        qs = sort_queryset(qs, sort_by, JobSortingInput)
        return gql_optimizer.query(qs, info)


class CsvMutations(graphene.ObjectType):
    export_products = ExportProducts.Field()

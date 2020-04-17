import graphene_django_optimizer as gql_optimizer

from ....app.models import App
from ...utils import sort_queryset
from ..deprecated.sorters import ServiceAccountSortField


def resolve_service_accounts(info, sort_by=None, **_kwargs):
    qs = App.objects.all()
    qs = sort_queryset(qs, sort_by, ServiceAccountSortField)
    return gql_optimizer.query(qs, info)

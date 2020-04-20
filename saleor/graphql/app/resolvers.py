import graphene_django_optimizer as gql_optimizer

from ...app import models
from ..utils import sort_queryset
from .sorters import AppSortField


def resolve_apps(info, sort_by=None, **_kwargs):
    qs = models.App.objects.all()
    qs = sort_queryset(qs, sort_by, AppSortField)
    return gql_optimizer.query(qs, info)

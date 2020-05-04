import django_filters

from ..core.filters import BaseJobFilter
from ..core.types import FilterInputObjectType
from ..utils.filters import filter_by_query_param


def filter_created_by(qs, _, value):
    user_fields = [
        "created_by__pk",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__email",
    ]
    qs = filter_by_query_param(qs, value, user_fields)
    return qs


class ExportFileFilter(BaseJobFilter):
    created_by = django_filters.CharFilter(method=filter_created_by)


class ExportFileFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ExportFileFilter

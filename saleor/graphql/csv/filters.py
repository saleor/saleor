import django_filters

from ..core.filters import EnumFilter, ObjectTypeFilter
from ..core.types import FilterInputObjectType
from ..core.types.common import DateTimeRangeInput
from ..utils import filter_by_query_param, filter_range_field
from .enums import JobStatusEnum


def filter_created_at(qs, _, value):
    return filter_range_field(qs, "created_at", value)


def filter_completed_at(qs, _, value):
    return filter_range_field(qs, "completed_at", value)


def filter_status(qs, _, value):
    if not value:
        return qs
    return qs.filter(status=value)


def filter_created_by(qs, _, value):
    user_fields = [
        "created_by__pk",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__email",
    ]
    qs = filter_by_query_param(qs, value, user_fields)
    return qs


class JobFilter(django_filters.FilterSet):
    created_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_created_at
    )
    completed_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_completed_at
    )
    status = EnumFilter(input_class=JobStatusEnum, method=filter_status)
    created_by = django_filters.CharFilter(method=filter_created_by)


class JobFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = JobFilter

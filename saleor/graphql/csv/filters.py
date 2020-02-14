import django_filters

from ..core.filters import EnumFilter, ObjectTypeFilter
from ..core.types import FilterInputObjectType
from ..core.types.common import DateTimeRangeInput
from ..utils import filter_by_query_param, filter_range_field
from .enums import JobStatusEnum


def filter_created_at(qs, _, value):
    return filter_range_field(qs, "created_at", value)


def filter_ended_at(qs, _, value):
    return filter_range_field(qs, "ended_at", value)


def filter_status(qs, _, value):
    if not value:
        return qs
    return qs.filter(status=value)


def filter_user(qs, _, value):
    user_fields = [
        "user__pk",
        "user__first_name",
        "user__last_name",
        "user__email",
    ]
    qs = filter_by_query_param(qs, value, user_fields)
    return qs


class JobFilter(django_filters.FilterSet):
    created_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_created_at
    )
    ended_at = ObjectTypeFilter(input_class=DateTimeRangeInput, method=filter_ended_at)
    status = EnumFilter(input_class=JobStatusEnum, method=filter_status)
    user = django_filters.CharFilter(method=filter_user)


class JobFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = JobFilter

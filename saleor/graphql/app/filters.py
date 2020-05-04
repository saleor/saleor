import django_filters

from ...app import models
from ..utils.filters import filter_by_query_param


def filter_app_search(qs, _, value):
    if value:
        qs = filter_by_query_param(qs, value, ("name",))
    return qs


class AppFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_app_search)
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = models.App
        fields = ["search", "is_active"]
